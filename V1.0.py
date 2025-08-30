"""
YOLOv8 实时检测 + 鼠标自动微调脚本
功能：
1. 黄色矩形框（Class 0）
2. 绿色图像中心点
3. 2 倍等比放大
4. 实时 FPS
5. 最近黄色框中心：
   • 方向箭头 + 水平/垂直箭头
   • 带符号 Δx、Δy 与直线距离
6. 长按鼠标侧键 X1（前进键）→ 根据 Δx/Δy 平滑移动鼠标
7. 纯 Win32 DLL 驱动，无硬件加速也能跑
"""

import ctypes           # 调用 Win32 DLL（鼠标驱动）
import os               # 获取脚本目录
import time             # 计时、延时
import cv2              # 图像处理
import pyautogui        # 仅用于获取当前鼠标坐标（可删）
from pynput import mouse  # 后台监听鼠标侧键
from ultralytics import YOLO

# ================= 鼠标控制相关 =================
# DLL 路径：把 MouseControl.dll 放在脚本同目录或绝对路径
DLL_PATH = r'C:\Users\R\Desktop\Project\Anaconda\object\OVERWATCH\lib\MouseControl.dll'
driver = ctypes.CDLL(DLL_PATH)

# 全局标志：是否正在长按鼠标侧键 X1
pressed_flag = False

def on_click(x, y, button, pressed):
    """
    鼠标事件回调：仅监听侧键 X1（前进键）
    pressed=True  表示按下
    pressed=False 表示松开
    """
    global pressed_flag
    if button == mouse.Button.x1:
        pressed_flag = pressed
        print('侧键 X1', '按下' if pressed else '释放')

# 启动后台监听（非阻塞）
listener = mouse.Listener(on_click=on_click)
listener.start()

# ================= 模型 & 摄像头参数 =================
MODEL_PATH = r"C:\Users\R\Desktop\Project\Anaconda\object\OVERWATCH\runs\detect\train\weights\best.pt"
CAM_ID      = 2         # 摄像头编号
CONF_THRES  = 0.7       # 置信度阈值
SCALE       = 2.0       # 显示放大倍率

# 加载 YOLO 模型
model = YOLO(MODEL_PATH)

# 打开摄像头
cap = cv2.VideoCapture(CAM_ID)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# FPS 计时变量
prev_time = 0

# ================= 主循环 =================
while True:
    # ---------- 1. 读取帧 ----------
    ok, frame = cap.read()
    if not ok:
        print("无法读取帧")
        break

    # ---------- 2. 计算 FPS ----------
    now = time.time()
    fps = 1 / (now - prev_time) if prev_time else 0
    prev_time = now

    # ---------- 3. YOLO 推理 ----------
    results = model(frame, conf=CONF_THRES)

    # ---------- 4. 预处理 ----------
    h, w = frame.shape[:2]                 # 原图高、宽
    img_cx, img_cy = w // 2, h // 2        # 图像中心坐标
    cv2.circle(frame, (img_cx, img_cy), 5, (0, 255, 0), -1)  # 画绿色中心点

    # ---------- 5. 收集黄色框中心 ----------
    yellow_centers = []
    for r in results:
        if r.boxes is None:
            continue
        xyxy = r.boxes.xyxy.cpu().numpy()
        cls  = r.boxes.cls.cpu().numpy()
        conf = r.boxes.conf.cpu().numpy()
        for box, c, cf in zip(xyxy, cls, conf):
            if int(c) != 0:          # 只关心 Class 0
                continue
            x1, y1, x2, y2 = map(int, box)

            # 画黄色矩形框
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            # 类别 + 置信度文字
            cv2.putText(frame, f'Class:{int(c)} Conf:{cf:.2f}',
                        (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 2)

            # 记录中心点
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            yellow_centers.append((cx, cy))

    # ---------- 6. 计算最近中心 ----------
    if yellow_centers:
        # 选距离图像中心最近的中心点
        cx, cy = min(yellow_centers,
                     key=lambda p: (p[0] - img_cx)**2 + (p[1] - img_cy)**2)
        dx = cx - img_cx   # 水平偏移（右正左负）
        dy = cy - img_cy   # 垂直偏移（下正上负）
        dist = (dx**2 + dy**2)**0.5

        # ---------- 7. 画方向箭头 ----------
        # 主方向箭头（青色）
        cv2.arrowedLine(frame, (img_cx, img_cy), (cx, cy),
                        (255, 255, 0), 2, tipLength=0.05)
        # 水平分量箭头（绿色）
        cv2.arrowedLine(frame, (img_cx, img_cy), (cx, img_cy),
                        (0, 255, 0), 2, tipLength=0.05)
        # 垂直分量箭头（品红）
        cv2.arrowedLine(frame, (cx, img_cy), (cx, cy),
                        (255, 0, 255), 2, tipLength=0.05)

        # ---------- 8. 标注数值 ----------
        cv2.putText(frame, f"dx:{dx:+d}  dy:{dy:+d}  dist:{dist:.1f}px",
                    (img_cx + 10, img_cy - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # ---------- 9. 鼠标 PID 微调 ----------
        # 距离门限：>90 px 不动作
        MAX_DIST = 90

        # 单轴 PID 简易类
        class PID:
            def __init__(self, kp=0.9, ki=0.0, kd=0.1):
                self.kp, self.ki, self.kd = kp, ki, kd
                self.prev_err = 0
                self.integral = 0
            def __call__(self, err, dt):
                if dt <= 0:
                    return 0
                self.integral += err * dt
                derivative = (err - self.prev_err) / dt
                out = self.kp * err + self.ki * self.integral + self.kd * derivative
                self.prev_err = err
                return int(max(-20, min(20, out)))      # 每帧限制 ±20 像素

        # 在主循环外初始化（防止重复创建）
        if 'pid_x' not in locals():
            pid_x = PID(kp=1.1, ki=0.01, kd=0.03)
            pid_y = PID(kp=0.5, ki=0.00, kd=0.00)
            last_t = now

        dt = now - last_t
        last_t = now

        # 只有按住侧键且距离 ≤ MAX_DIST 才执行 PID
        if pressed_flag and dist <= MAX_DIST:
            mv_x = pid_x(dx, dt)
            mv_y = pid_y(dy, dt)
            driver.move_R(int(mv_x), int(mv_y))
            # driver.move_Abs(int(1280+dx), int(720+dy))


    # ---------- 10. 显示 FPS ----------
    cv2.putText(frame, f'FPS: {fps:.1f}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # ---------- 11. 等比放大 ----------
    new_size = (int(w * SCALE), int(h * SCALE))
    frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_LINEAR)

    # ---------- 12. 显示 ----------
    cv2.imshow('YOLOv8 Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ---------- 13. 清理 ----------
cap.release()
cv2.destroyAllWindows()
listener.stop()
