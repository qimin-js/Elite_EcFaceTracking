from __future__ import annotations
import copy

import numpy as np
import transformations
from transformations.transformations import euler_from_matrix, inverse_matrix

class Pose():
    def __init__(self,pose:list):
        """
        :param pose: 坐标数据
        """
        for params in range(len(pose)):
            pose[params-1]=float(pose[params-1])
        self._pose:list=pose
        """迭代使用"""
        self._count:int=-1
    def __repr__(self):
        """重载实例输出"""
        return "{0}".format(self._pose)
    def __eq__(self, other:Pose):
        """重载="""
        self._pose=other
    def __getstate__(self):
        """配置json输出"""
        return self._pose
    def __getitem__(self, index):
        """重载[]"""
        return self.get(index)
    def __iter__(self):
        return self
    def __next__(self):
        """
        迭代器，迭代 self._pose
        :return:
        """
        if self._count <=4:
            self._count+=1
            return self._pose[self._count]
        else:
            raise StopIteration
    def __copy__(self):
        """
        浅拷贝
        利用copy.copy()浅拷贝self._pose
        :return:
        """
        return Pose(copy.copy(self._pose))
    def __deepcopy__(self, memo=None):
        """
        深拷贝
        :return:
        """
        return Pose(copy.deepcopy(self._pose))
    @property
    def type(self):
        return self._type
    def get(self,index:int)->float:
        """
        获取
        :param index: 0-5
        :return:float 角度
        """
        return self._pose[index]
    def toString(self)->str:
        """
        pose 位姿 字符串化
        :return:
        """
        value="["
        for params in range(0,6):
            value+=str(self._pose[params])
            if params == 5:
                continue
            value+=','
        value+=']'
        return value
    def radianToAngle(self)->list:
        """
        弧度->角度
        """
        return [self._pose[0],self._pose[1],self._pose[2],self._pose[3]*57.29578,self._pose[4]*57.29578,self._pose[5]*57.29578]
    def angleToRadian(self)->Pose:
        """
        角度->弧度
        :return: self链式编程
        """
        self._pose[3]/=57.29578
        self._pose[4]/=57.29578
        self._pose[5]/=57.29578
        self._type = 1
        return self
    def clone(self)->Pose:
        return copy.deepcopy(self)
    def toList(self)->list:
        """
        输出数组
        :return:数组list
        """
        return self._pose
    @classmethod
    def eulerToMatrix(cls,pose:Pose)->list:
        """
        欧拉角转齐次变换矩阵
        :return: 变化矩阵
        """
        m = transformations.euler_matrix(pose[3], pose[4], pose[5])
        # print(m)
        m[0][3] = pose[0]
        m[1][3] = pose[1]
        m[2][3] = pose[2]
        return m
    @classmethod
    def matrixToEuler(cls,mat:list)->Pose:
        """
        齐次变换矩阵转欧拉角
        :param mat: 齐次变换矩阵
        :return: Pose
        """
        # print(mat)
        x, y, z = mat[0][3], mat[1][3], mat[2][3]
        mat[0][3] = 0
        mat[1][3] = 0
        mat[2][3] = 0
        # 旋转矩阵到弧度的欧拉角
        rx, ry, rz = euler_from_matrix(mat)
        # 由于使用了numpy导致数据类型出现问题，json解析出bug
        return Pose([float(x), float(y), float(z), float(rx), float(ry), float(rz)])
    @classmethod
    def matMul(cls,pose1:list,pose2:list)->list:
        """矩阵的乘"""
        return list(np.matmul(pose1, pose2))
    @classmethod
    def matInv(cls,pose:Pose)->list:
        """
        矩阵的逆
        :return: 矩阵
        """
        return inverse_matrix(Pose.eulerToMatrix(pose))
    @classmethod
    def poseInv(cls,pose:Pose)->Pose:
        """
        位姿的逆
        :return: 求逆后的欧拉角
        """
        return pose.matrixToEuler(Pose.matInv(pose))
    @classmethod
    def poseMul(cls, pose1:Pose, pose2:Pose)->Pose:
        """位姿的乘"""
        pose = cls.matrixToEuler(cls.matMul(Pose.eulerToMatrix(pose1), Pose.eulerToMatrix(pose2)))
        return pose
    def move(self,x:float,y:float,z:float)->Pose:
        """基于基坐标相对移动"""
        return Pose.poseMul(Pose([x, y, z,0,0,0]), self)
    def moveTo(self,x:float,y:float,z:float)->Pose:
        """绝对移动"""
        return Pose([x,y,z,self[3],self[4],self[5]])
    def rotation(self,rx:float,ry:float,rz:float,type=1)->Pose:
        """
        绕 基坐标 旋转
        :param rx:
        :param ry:
        :param rz:
        :param type: 1:弧度 2:角度 默认1
        :return:
        """
        if type == 2:
            rx/=57.29578
            ry/=57.29578
            rz/=57.29578
        return Pose.poseMul(Pose([0,0,0,rx,ry,rz]),self)
    def rotationTo(self,rx:float,ry:float,rz:float)->Pose:
        newPose= self.clone()
        newPose._pose[3]=rx
        newPose._pose[4]=ry
        newPose._pose[5]=rz
        return newPose
    def rotationTool(self,rx:float,ry:float,rz:float,type=1)->Pose:
        """
        绕末端 工具坐标 旋转
        :param rx:
        :param ry:
        :param rz:
        :param type: 1:弧度 2:角度 默认1
        :return:
        """
        if type == 2:
            rx/=57.29578
            ry/=57.29578
            rz/=57.29578
        return Pose.poseMul(self,Pose([0,0,0,rx,ry,rz]))
    def transform(self,do:list)->Pose:
        return self.move(do[0],do[1],do[2]).rotation(do[3],do[4],do[5])
    def interval(self,pose):
        """计算坐标之间间距"""
        return Pose.poseMul(Pose.poseInv(self), pose)
if __name__ == "__main__":
    jk = Pose([10,10,10,0.1,0,0])
    jkl = Pose([10,10,10,0,0,0])
    print(Pose.poseMul(jk,jkl))