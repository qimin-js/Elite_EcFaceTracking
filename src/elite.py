from __future__ import annotations

import jsonpickle as json
import time
from threading import Lock
import threading
from icecream import ic
ic.configureOutput(includeContext=True,prefix="")

# from src import Tcp,JsonBase,Pose
from src.tcp import Tcp
from src.jsonBase import JsonBase
from src.pose import Pose
class Elite (Tcp):
    def __init__(self,ip:str,port:int):
        super(Elite, self).__init__()
        self.speed:int = 16
        """速度 0-100"""
        self.acc:int = 25
        """加速度 0-100"""
        self.status:int = 0
        """停止状态 0，暂停状态 1，急停状态 2，运行状态 3，错误状态 4，碰撞状态 5"""
        self._lock = Lock()
        """进程锁"""
        self.errorType = 0
        """错误状态"""
        self.connect(ip,port)
        """连接机械臂"""
        # self.toolNum=0
        """默认工具号"""
        # self.poseNum=0
        """默认用户号"""
        self.end = 0
        self.startPose = self.getCartPose()

    def getUserNum(self)->int:
        """获取当前用户坐标号"""
        return int(self.sendCmdName("getUserNumber"))
    def setUserNum(self,userNum:int):
        cmd= self.__basicJson()
        cmd["method"]="setUserNumber"
        cmd["params"]={"user_num":userNum}
        return self.sendCmdJson(cmd)
    def connect(self,ip:str,port:int):
        super(Elite, self).connect(ip, port)
        jk=threading.Thread(target=self.__childThread)
        jk.start()
    def __childThread(self):
        while 1:
            self.status = self.getStatus()
            # print(self.status)
            time.sleep(0.001)
    def __callback(self):
        while 1:
            time.sleep(0.01)
            self.status = self.getStatus()
    def __basicJson(self)->JsonBase:
        return JsonBase().arm()
    def sendCmd(self,cmd:str):
        with self._lock:
            """childThread可能会数据错乱，加同步锁"""
            self.send(cmd + '\n')
            message= json.loads(self.recv())
            # print(message)
            try :
                message = message["result"]
            except BaseException as e:
                message=message["error"]["message"]
                ic(message)
            # python 没有[]运算符，需要再解析一次
            if message[0] == '[':
                return json.loads(message)
            elif message == 'true' or message == "false":
                return json.loads(message)
            else:
                return message
    def sendCmdJson(self,cmd):
        # print(cmd.dump())
        return self.sendCmd(cmd.dump())
    def sendCmdName(self,cmdName:str):
        cmd= self.__basicJson()
        cmd["method"]=cmdName
        return self.sendCmd(cmd.dump())
    def getStatus(self)->int:
        """
        获取机器人状态
        :return: 停止状态 0，暂停状态 1，急停状态 2，运行状态 3，报警状态 4，碰撞状态 5
        """
        return int(self.sendCmdName("getRobotState"))
    def clearCollisionState(self):
        """清楚碰撞状态"""
        return self.sendCmdName("resetCollisionState")
    def getUserFrame(self,poseNum)->list:
        """
        获取用户坐标系数据 数组 角度为弧度
        :param poseNum:
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="getUserFrame"
        cmd["params"]={"user_num":poseNum}
        return self.sendCmdJson(cmd)
    def getUserPose(self)->Pose:
        """获取当前用户坐标"""
        """getRobotPose加参数会出现回去坐标错乱问题"""
        return self.poseCartToUser(Pose(self.sendCmdName("getTcpPose")))
    def getCartPose(self)->Pose:
        """获取直角坐标"""
        return Pose(self.sendCmdName("getRobotPose"))
    def getNowPos(self)->list:
        """获取当前关节坐标"""
        return self.sendCmdName("getRobotPos")
    def setToolNum(self,num:int):
        """
        设置当前工具坐标系
        :param num: 工具号 0-7
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="setAutoRunToolNumber"
        cmd["params"]={"tool_num":num}
        return self.sendCmdJson(cmd)
    def getToolNumber(self)->int:
        """获取当前工具坐标系"""
        return int(self.sendCmdName("getAutoRunToolNumber"))
    def getTcpPos(self):
        cmd= self.__basicJson()
        cmd["method"]="getTcpPos"
        cmd["params"]={"tool_num":0}
        return Pose(self.sendCmdJson(cmd))
    def poseCartToJoint(self,pose:Pose)->list:
        """直角坐标->关节坐标"""
        cmd= self.__basicJson()
        cmd["method"]="inverseKinematic"
        cmd["params"]={"targetPose":pose}
        return self.sendCmdJson(cmd)
    def poseUserToCart(self,pose:Pose)->Pose:
        """用户坐标->直角坐标"""
        cmd= self.__basicJson()
        cmd["method"]="convertPoseFromUserToCart"
        cmd["params"]={"targetPose":pose}
        return Pose(self.sendCmdJson(cmd))
    def poseUserToJoint(self,pose:Pose)->list:
        """
        用户坐标->关节角度
        :param pose:用户坐标
        :return:
        """
        pos= self.poseUserToCart(pose)
        return self.poseCartToJoint(pos)
    def poseJointToUser(self,pos:list)->Pose:
        """
        关节角度->用户坐标
        :param pos:关节角度
        :return:
        """
        pose= self.poseJointToCart(pos)
        return self.poseCartToUser(pose)
    def poseJointToCart(self,pos:list)->Pose:
        """关节坐标->直角坐标"""
        cmd= self.__basicJson()
        cmd["method"]="positiveKinematic"
        cmd["params"]={"targetPos":pos}
        return Pose(self.sendCmdJson(cmd))
    def poseCartToUser(self,pose:Pose)->Pose:
        """直角坐标->用户坐标"""
        cmd= self.__basicJson()
        cmd["method"]="convertPoseFromCartToUser"
        cmd["params"]={"targetPose":pose,"userNo":self.getUserNum()}
        return Pose(self.sendCmdJson(cmd))
    def poseMul(self,pose1:Pose,pose2:Pose)->Pose:
        """位姿相乘"""
        cmd= self.__basicJson()
        cmd["method"]="poseMul"
        cmd["params"]={"pose1":pose1,"pose2":pose2,"unit_type":1}
        print(cmd)
        return Pose(self.sendCmdJson(cmd))
    def poseInv(self,pose:Pose)->Pose:
        """位姿求逆"""
        cmd= self.__basicJson()
        cmd["method"]="poseInv"
        cmd["params"]={"pose":pose}
        return Pose(self.sendCmdJson(cmd))
    def moveTo(self,pose:Pose,wait=True)->bool:
        """
        绝对移动
        :param pose 当前用户坐标:
        """
        if self.errorType != 0:
            return False
        # globVar.ic(pose.pose)
        pos= self.poseCartToJoint(pose)
        cmd= self.__basicJson()
        cmd["method"]="moveByLine"
        cmd["params"]={"targetpos":pos,"speed":500,"speed_type":0,"acc":30,"dec":30}
        message= self.sendCmdJson(cmd)
        if wait == True:
            self.wait()
        return message
    def move(self,pose:Pose,wait=True):
        message = self.moveTo(Pose.poseMul(pose,self.getCartPose()),wait)
        return message
    def moveByArc(self,middlePose:Pose,targetpose:Pose):
        """
        圆弧运动，中间点和目标点都在 圆弧上
        :param middlePose: 中间点 不是中心点
        :param targetpose: 目标点
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="moveByArc"
        middlePos=self.poseCartToJoint(middlePose)
        targetpos=self.poseCartToJoint(targetpose)
        cmd["params"]={"midPos":middlePos,"targetpos":targetpos,"Speed":self.speed,"speed_type":2,"acc":self.acc}

        message= self.sendCmdJson(cmd)
        self.wait()
        return message
    def jog(self,index:int,speed:int):
        cmd= self.__basicJson()
        cmd["method"]="jog"
        cmd["params"]={"index":index,"speed":speed}
        message= self.sendCmdJson(cmd)
        return message
    def wait(self):
        """等待运动结束"""
        while 1:
            time.sleep(0.001)
            # if self.startPose.get(0)-self.getCartPose().get(0) < 0.01:
            #     print(self.startPose.get(0),self.getCartPose().get(0))
            #     print(int(round(time.time() * 1000)))
            self.status = self.getStatus()
            if self.status == 0:
                # self.end = int(round(time.time() * 1000))
                break
    def stop(self)->bool:
        """停止运行"""
        return self.sendCmdName("stop")
    def pause(self):
        """暂停运行"""
        return self.sendCmdName("pause")
    def run(self):
        """继续运行"""
        return self.sendCmdName("run")
    def setB(self,addr:int,value:int):
        cmd= self.__basicJson()
        cmd["method"]="setSysVarB"
        cmd["params"]={"addr":addr,"value":value}
        return self.sendCmdJson(cmd)
    def setOutput(self,addr:int,value:int):
        cmd= self.__basicJson()
        cmd["method"]="setOutput"
        cmd["params"]={"addr":addr,"status":value}
        return self.sendCmdJson(cmd)
    def setP(self,addr:int,pos:list)->bool:
        """
        设置P变量 (必须在remote模式)
        :param addr: 0-255
        :param pos: 关节角度
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="setSysVarP"
        cmd["params"]={"addr":addr,"pos":pos}
        return self.sendCmdJson(cmd)
    def setV(self,addr:int,pose:Pose)->bool:
        """
        设置V变量 (必须在remote模式)
        :param addr: 0-255
        :param pose: 直角坐标系
        """
        cmd= self.__basicJson()
        cmd["method"]="setSysVarV"
        cmd["params"]={"addr":addr,"pose":pose}
        return self.sendCmdJson(cmd)
    def getV(self,addr:int)->Pose:
        """
        获取V变量 (必须在remote模式)
        :param addr: 0-255
        """
        cmd= self.__basicJson()
        cmd["method"]="getSysVarV"
        cmd["params"]={"addr":addr}
        return Pose(self.sendCmdJson(cmd))
    def getP(self,addr:int)->list:
        """
        获取P变量 (必须在remote模式)
        :param addr: 0-255
        """
        cmd= self.__basicJson()
        cmd["method"]="getSysVarP"
        cmd["params"]={"addr":addr}
        return self.sendCmdJson(cmd)
    def setI(self,addr:int,data:int)->bool:
        """
        设置I变量 (必须在remote模式)
        :param addr: 0-255
        :param data: -32767,32767
        """
        cmd= self.__basicJson()
        cmd["method"]="setSysVarI"
        cmd["params"]={"addr":addr,"pose":data}
        return self.sendCmdJson(cmd)
    def getI(self,addr:int)->int:
        """
        获取I变量 (必须在remote模式)
        :param addr: 0-255
        """
        cmd= self.__basicJson()
        cmd["method"]="getSysVarI"
        cmd["params"]={"addr":addr}
        return self.sendCmdJson(cmd)
    def getVar(self, type: str, addr: int):
        """
        获取机械臂内部变量
        :param type:b i d p v
        :param addr:
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="getSysVar"+type.upper()
        cmd["params"]={"addr":addr}
        message=self.sendCmdJson(cmd)
        if type.upper() == "V":
            message = Pose(message)
        if type.upper() == "D":
            message = float(message)
        return message
    def getInput(self,addr:int):
        cmd= self.__basicJson()
        cmd["method"]="getInput"
        cmd["params"]={"addr":addr}
        return self.sendCmdJson(cmd)
    def setVar(self,type:str,addr:int,value:int):
        """
        获取机械臂内部变量
        :param type:b i d p v
        :param addr:
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"] = "setSysVar"+type.upper()
        cmd["params"] = {"addr": addr, "value": value}
        message=self.sendCmdJson(cmd)
        return message
    def setServo(self,status:bool)->bool:
        """
        设置伺服
        :param status: True打开 False关闭
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="set_servo_status"
        if status == True:
            status=1
        else:
            status = 0
        cmd["params"]={"status":status}
        return self.sendCmdJson(cmd)
    def clearAlarm(self)->bool:
        """清楚报警"""
        return self.sendCmdName("clearAlarm")
    def ttInit(self,lookahead:int,t:int)->bool:
        """
        初始化透传服务
        :param lookahead:前瞻时间 10,1000
        :param t:采样时间 2,100
        """
        cmd= self.__basicJson()
        cmd["method"]="transparent_transmission_init"
        cmd["params"]={"lookahead":lookahead,"t":t,"smoothness":0.1}
        return self.sendCmdJson(cmd)
    def ttAdd(self,pos):
        """
        添加透传伺服目标关节点信息到缓存中
        """
        cmd= self.__basicJson()
        cmd["method"]="tt_put_servo_joint_to_buf"
        # targetPos= self.poseCartToJoint(pose)
        # print(pos)
        cmd["params"]={"targetPos":pos}
        return self.sendCmdJson(cmd)
    def ttClearBuf(self):
        """清空透传缓存"""
        return self.sendCmdName("tt_clear_servo_joint_buf")
    def getSoftVersion(self):
        """获取控制器软件版本号"""
        return self.sendCmdName("getSoftVersion")
    def getJointVersion(self,axis:int):
        """
        获取伺服版本号
        :param axis: [0-7] 对应轴号 1~8
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="getJointVersion"
        cmd["params"]={"axis":axis}
        return self.sendCmdJson(cmd)
    def getSafetyPower(self)->float:
        """获取安全功率"""
        return self.sendCmdName("getRobotSafetyPower")
    def getSafetyMomentum(self)->float:
        """获取安全动量"""
        return self.sendCmdName("getRobotSafetyMomentum")
    def getSafetyToolForce(self)->float:
        """获取安全工具力"""
        return self.sendCmdName("getRobotSafetyToolForce")
    def getSafetyElbowForce(self)->float:
        """获取安全肘部力"""
        return self.sendCmdName("getRobotSafetyElbowForce")
    def getSpeedPercentage(self)->float:
        """获取机器人的速度百分比"""
        return self.sendCmdName("getRobotSpeedPercentage")
    def getDragStartupMaxSpeed(self)->float:
        """获取拖动最大启动速度"""
        return self.sendCmdName("getRobotDragStartupMaxSpeed")
    def getTorqueErrorMaxPercents(self)->float:
        """获取机器的最大力矩误差百分比"""
        return self.sendCmdName("getRobotTorqueErrorMaxPercents")
    def checkFlangeButton(self,buttonNum:int):
        """
        获取末端按钮状态
        :param buttonNum:[0-1] 0:蓝色按钮,1:绿色按钮
        :return:禁用 0，拖动 1，记点 2
        """
        cmd= self.__basicJson()
        cmd["method"]="checkFlangeButton"
        cmd["params"]={"button_num":buttonNum}
        return self.sendCmdJson(cmd)
    def setFlangeButton(self,buttonNum:int,state:int):
        """
        设置末端按钮状态
        :param buttonNum:[0,1] 0:蓝色按钮,1:绿色按钮
        :param state:[0,2],0:禁用,1:拖动,2:记点
        """
        cmd= self.__basicJson()
        cmd["method"]="setFlangeButton"
        cmd["params"]={"button_num":buttonNum,"state":state}
        return self.sendCmdJson(cmd)
    def getCollisionEnableStatus(self):
        """
        获取碰撞检测使能状态
        :return:0:未使能,1:使能
        """
        return self.sendCmdName("get_collision_enable_status")
    def getRobotTorques(self):
        return self.sendCmdName("get_motor_torque")
    def runJbi(self,filename:str):
        """
        运行jbi文件
        :param filename: 文件名称
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"]="runJbi"
        cmd["params"]={"filename":filename}
        return self.sendCmdJson(cmd)
    def addPathPoint(self,point:Pose,circular_radius:int=2):
        """
        添加路点
        :param point: 位姿
        :param circular_radius: cr圆滑度
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"] = "addPathPoint"
        cmd["params"] = {"waypoint":self.poseCartToJoint(point),
                       "moveType":1,"speed":500,"circular_radius":circular_radius,"speed_type":0,"acc":30}
        message = self.sendCmdJson(cmd)
        return message
    def moveByPath(self):
        """
        路点移动
        :return:
        """
        message = self.sendCmdName("moveByPath")
        # self.wait()
        return message
    def getPathPointIndex(self):
        message = self.sendCmdName("getPathPointIndex")
        return message
    def clearPathPoint(self):
        """
        清楚路点缓存
        :return:
        """
        return self.sendCmdName("clearPathPoint")
    def startPushPos(self,path_lenth:int,pose:Pose):
        """
        初始化时间戳运行
        :param path_lenth: 点位数量
        :param pose: 第一个点的逆解
        """
        cmd= self.__basicJson()
        cmd["method"] = "start_push_pos"
        cmd["params"] = {"path_lenth":path_lenth,"pos_type":0,"ref_frame":[0,0,0,0,0,0],"ret_flag":1,"ref_joint_pos":self.poseCartToJoint(pose)}
        message = self.sendCmdJson(cmd)
        return message
    def pushPos(self,timestamp:float,pose:Pose):
        """
        添加时间戳运行点位
        :param timestamp: 时间
        :param pose: 位姿
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"] = "push_pos"
        cmd["params"] = {"timestamp":timestamp,"pos":self.poseCartToJoint(pose)}
        message = self.sendCmdJson(cmd)
        return message
    def stopPushPos(self):
        """
        停止时间戳运动
        :return:
        """
        return self.sendCmdName("stop_push_pos")
    def checkTrajectory(self):
        """
        检查时间戳运动
        :return:
        """
        return self.sendCmdName("check_trajectory")
    def startTrajectory(self,speed_percent:int):
        """
        开始时间戳运动
        :param speed_percent: 控制速度百分比 0-100
        :return:
        """
        cmd= self.__basicJson()
        cmd["method"] = "start_trajectory"
        cmd["params"] = {"speed_percent":speed_percent}
        message = self.sendCmdJson(cmd)
        self.wait()
        return message
    def flushTrajectory(self):
        """
        清楚时间戳缓存
        :return:
        """
        return self.sendCmdName("flush_trajectory")
    def encoderCalibration(self):
        return self.sendCmdName("calibt")


# {"jsonrpc": "2.0", "method": "getUserFrame", "id": 1, "params": {"user_num": 0}}
if __name__ == "__main__":
    nn = Elite("172.16.11.32",8055)
    nn.getInput(7)
