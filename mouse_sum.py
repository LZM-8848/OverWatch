import ctypes
import os
import winsound
import time
import pyautogui
from pynput import mouse
import time

pressed_flag = False        # 用布尔值更直观

def on_click(x, y, button, pressed):
    global pressed_flag
    if button == mouse.Button.x1:
        pressed_flag = pressed
        print('4 号侧键', '按下' if pressed else '释放')


def linear_interpolation( x_end, y_end, num_steps, delay):# 绝对平滑移动
    start_x, start_y = pyautogui.position()
    dx = (x_end - start_x) / num_steps
    dy = (y_end - start_y) / num_steps

    for i in range(1,num_steps+1):
        next_x = int(start_x + dx * i)
        next_y = int(start_y + dy * i)

        driver.move_Abs(int(next_x), int(next_y))

        time.sleep(delay)

def r_linear_interpolation(r_x, r_y, num_steps, delay):
    r_y = -r_y                      # 方向修正
    dx = r_x / num_steps
    dy = r_y / num_steps
    for _ in range(num_steps):
        driver.move_R(int(dx), int(dy))
        time.sleep(delay)

# 启动后台监听（不阻塞）
listener = mouse.Listener(on_click=on_click)
listener.start()

x_end = 10
y_end = 10
root = os.path.abspath(os.path.dirname(__file__))
driver = ctypes.CDLL(r'C:\Users\R\Desktop\Project\Anaconda\object\OVERWATCH\lib\MouseControl.dll')




# ===== 主线程可以干别的事 =====
try:
    while True:
        if pressed_flag:
            r_linear_interpolation(x_end, y_end, num_steps=20, delay=0.01)
        time.sleep(0.01)
except KeyboardInterrupt:
    listener.stop()
    listener.join()
