# Elite人脸追踪

欢迎使用Elite人脸追踪

[[_TOC_]]

## 介绍

使用 Elite EC系列机械臂，实现人脸特征追踪

## 依赖
1. python3.8
2. opencv-python==3.4.11.45
3. dlib==19.22.1

Elite EC 3.5版本以上

```bash
pip install -r requirements.txt 
```

## 效果视频
https://www.bilibili.com/video/BV1AG4y1E7QX/?spm_id_from=444.41.list.card_archive.click&vd_source=34e025d264b0576a353acfc637b9aeae

![image-20221228160409204](https://aliyun-oss-img-bed.oss-cn-hangzhou.aliyuncs.com/elite_imgbed202212281604938.png)

## 原理

运行前准备

将机械臂调成下图姿态，将末端移至基坐标系x轴正方向上。

![image-20221228095755912](https://aliyun-oss-img-bed.oss-cn-hangzhou.aliyuncs.com/elite_imgbed202212280959945.png)

运动类型：

使用EC SDK提供的透传服务每隔几毫秒传输一个点位，机械臂平滑柔顺运动到传输的点位。

人脸识别：

使用dlib人脸特征识别，识别眼睛和鼻子。

根据鼻子在640x480屏幕上的坐标计算机械臂下一个点位的偏移值。

运动轨迹：

创建用户坐标系平行于坐标系，在机械臂工具坐标系x轴负200mm的位置。

用户坐标系下坐标： [200，0，0，基坐标rx，基坐标ry，基坐标rz]

根据用户坐标系进行左乘ry和rz，绕固定的用户坐标系的y轴和z轴旋转 ，就可以移动到以用户坐标系为原点半径为200mm的圆上任意一点。

对应到人脸特征上，人脸偏上就是绕用户坐标系ry反方向旋转

旋转完后，将用户坐标换算成基坐标进行移动。