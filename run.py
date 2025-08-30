"""
YOLOv8 实时检测脚本（带方向箭头 & 矩形框保留）
功能：
1. 黄色矩形框（Class 0）
2. 绿色图像中心点
3. 2 倍等比放大
4. 实时 FPS
5. 最近黄色框中心：
   - 方向箭头 + 水平/垂直箭头
   - 带符号 Δx、Δy 与直线距离
"""

import cv2
import time
from ultralytics import YOLO

# ----------------- 可调参数 -----------------
MODEL_PATH = r"C:\Users\R\Desktop\Project\Anaconda\object\OVERWATCH\runs\detect\train\weights\best.pt"
CAM_ID      = 2                 # 摄像头编号
CONF_THRES  = 0.7               # 置信度阈值
SCALE       = 2.0               # 显示放大倍率
# -------------------------------------------

# 加载模型
model = YOLO(MODEL_PATH)

# 打开摄像头
cap = cv2.VideoCapture(CAM_ID)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# FPS 计时器
prev_time = 0

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
    h, w = frame.shape[:2]                # 原图高宽
    img_cx, img_cy = w // 2, h // 2       # 图像中心坐标
    cv2.circle(frame, (img_cx, img_cy), 5, (0, 255, 0), -1)  # 画绿色中心点

    # ---------- 5. 收集黄色框中心 ----------
    yellow_centers = []
    for r in results:
        if r.boxes is None:
            continue
        xyxy = r.boxes.xyxy.cpu().numpy()
        cls  = r.boxes.cls.cpu().numpy()
        for box, c, conf in zip(xyxy, cls, r.boxes.conf.cpu().numpy()):
            if int(c) != 0:
                continue
            x1, y1, x2, y2 = map(int, box)

            # 画黄色矩形框
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            # 类别+置信度文字
            cv2.putText(frame, f'Class:{int(c)} Conf:{conf:.2f}',
                        (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 2)

            # 保存中心点
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            yellow_centers.append((cx, cy))

    # ---------- 6. 计算最近中心 ----------
    if yellow_centers:
        cx, cy = min(yellow_centers,
                     key=lambda p: (p[0] - img_cx)**2 + (p[1] - img_cy)**2)
        dx = cx - img_cx   # 水平偏移（右正左负）
        dy = cy - img_cy   # 垂直偏移（下正上负）
        dist = (dx**2 + dy**2)**0.5

        # ---------- 7. 画箭头 ----------
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

    # ---------- 9. 显示 FPS ----------
    cv2.putText(frame, f'FPS: {fps:.1f}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # ---------- 10. 等比放大 ----------
    new_size = (int(w * SCALE), int(h * SCALE))
    frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_LINEAR)

    # ---------- 11. 显示 ----------
    cv2.imshow('YOLOv8 Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ---------- 12. 清理 ----------
cap.release()
cv2.destroyAllWindows()
