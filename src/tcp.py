"""
tcp
"""
import socket

class Tcp:
    def __init__(self):
        self.__port = None
        self.__ip = None
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def connect(self,ip:str,port:int):
        """
        连接
        :param ip: ip地址
        :param port: 端口号
        :return:
        """
        self.__ip=ip
        self.__port=port
        try:
            self.__sock.connect((self.__ip, self.__port))
        except BaseException as e:
            print("_ip:",self.__ip,"port:",self.__port,"连接失败")
            exit(1)
    def close(self):
        """关闭TCP连接"""
        self.__sock.close()
    def send(self,data:str):
        """
        发送数据
        :param data: 要发送的数据
        :return:
        """
        self.__sock.send(bytes(data, "utf-8"))
    def sendBytes(self,data:bytes):
        self.__sock.send(data)
    def recv(self)->str:
        """接受数据"""
        return str(self.__sock.recv(2048),"utf-8")
    def recvBytes(self):
        return self.__sock.recv(2048)