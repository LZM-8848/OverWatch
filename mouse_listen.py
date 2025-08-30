from pynput import mouse
import time

pressed_flag = False        # 用布尔值更直观

def on_click(x, y, button, pressed):
    global pressed_flag
    if button == mouse.Button.x1:
        pressed_flag = pressed
        print('4 号侧键', '按下' if pressed else '释放')

# 启动后台监听（不阻塞）
listener = mouse.Listener(on_click=on_click)
listener.start()

# ===== 主线程可以干别的事 =====
try:
    while True:
        print(pressed_flag)
        # 例如这里可以检测 pressed_flag 并执行相应逻辑
        time.sleep(0.01)
except KeyboardInterrupt:
    listener.stop()
    listener.join()
