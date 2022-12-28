import numpy as np
import cv2
import dlib
from src.elite import Elite
from src.pose import Pose

camera = cv2.VideoCapture(0)

detector = dlib.get_frontal_face_detector()
# 使用dlib自带的frontal_face_detector作为我们的特征提取器
predictor = dlib.shape_predictor('./resources/shape_predictor_5_face_landmarks.dat')

nn = Elite("172.16.11.32",8055)
nn.setServo(True)
nn.ttClearBuf()
nn.ttInit(1000,100)
nowPose = nn.getCartPose()
invented = nowPose.moveTo(200,0,0) # 虚拟坐标
print("当前位置",nowPose)
interval = Pose.poseMul(nowPose,Pose.poseInv(invented))
temp = Pose([0,0,0,0,0,0])
rotateX = 0
rotateY = 0

while camera.isOpened():
    ret, img = camera.read() # 读取相机图片
    if ret == False:
        break
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # 转灰度
    rects = detector(img_gray, 0)
    for i in range(len(rects)):
        landmarks = np.matrix([[p.x, p.y] for p in predictor(img, rects[i]).parts()])
        for idx, point in enumerate(landmarks):
            pos = (point[0, 0], point[0, 1])
            # print(idx, pos)
            if idx == 4:
                print((pos[0]-320)/320,(240-pos[1])/240)
                offsetX = (pos[0]-320)/160
                offsetY = (240-pos[1])/120
                if pos[0] > 270 and pos[0] < 370 and pos[1] > 190 and pos[1] < 290:
                    print("中间")

                # print(offsetX, offsetY)
                print(rotateY, rotateX)
                rotateX += offsetX
                rotateY += offsetY
                temp = Pose.poseMul(Pose([0, 0, 0, 0, -rotateY, -rotateX]).angleToRadian(), invented)
                targetPose = Pose.poseMul(interval, temp)
                nn.ttAdd(nn.poseCartToJoint(targetPose))
            # 利用cv2.circle给每个特征点画一个圈，共68个
            cv2.circle(img, pos, 2, color=(0, 255, 0))
            # 利用cv2.putText输出1-68
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, str(idx + 1), pos, font, 0.2, (0, 0, 255), 5, cv2.LINE_AA)
    # 绘制辅助线条
    cv2.circle(img, (320,240), 50, color=(0, 255, 0))
    cv2.line(img, (0, 240), (640,240), (0, 255, 0), 5, 16)
    cv2.line(img, (320, 0), (320,480), (0, 255, 0), 5, 16)
    cv2.imshow('video', img)
    k = cv2.waitKey(1)
    if k == 27:  # press 'ESC' to quit
        break

camera.release()
cv2.destroyAllWindows()
