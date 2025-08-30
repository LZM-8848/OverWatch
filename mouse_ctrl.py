import ctypes
import os
import winsound
import time
import pyautogui
def linear_interpolation( x_end, y_end, num_steps, delay):# 绝对平滑移动
    start_x, start_y = pyautogui.position()
    dx = (x_end - start_x) / num_steps
    dy = (y_end - start_y) / num_steps

    for i in range(1,num_steps+1):
        next_x = int(start_x + dx * i)
        next_y = int(start_y + dy * i)

        driver.move_Abs(int(next_x), int(next_y))

        time.sleep(delay)


# def r_linear_interpolation(r_x,r_y,num_steps,delay):
#     r_y = 0-r_y
#     dx = r_x/num_steps
#     dy = r_y/num_steps
#     for i in range(1,num_steps+1):
#         next_x,next_y = (dx),(dy)
#         driver.move_R(int(next_x),int(next_y))
#         time.sleep(delay)

def r_linear_interpolation(r_x, r_y, num_steps, delay):
    r_y = -r_y                      # 方向修正
    dx = r_x / num_steps
    dy = r_y / num_steps
    for _ in range(num_steps):
        driver.move_R(int(dx), int(dy))
        time.sleep(delay)


time.sleep(2)
x_end = 10
y_end = 10
root = os.path.abspath(os.path.dirname(__file__))
driver = ctypes.CDLL(r'C:\Users\R\Desktop\Project\Anaconda\object\OVERWATCH\lib\MouseControl.dll')



# r_linear_interpolation(2560*0.6167*0.5,1440*0.6167*0, num_steps=1, delay=0.01)

driver.move_R(int(2560*0.6167*0.5), int(1440*0.46458*0.5))

