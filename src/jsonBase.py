"""
多产品json适配

cmd["method"]="setUserNumber"
cmd["params"]={"user_num":userNum}
cmd.dump() # json序列化
"""
from typing import Dict
import jsonpickle

class JsonBase():
    def __init__(self):
        self.__data={"jk":"none"}
    def arm(self):
        """
        生成Arm SDK基础框架
        :return:
        """
        self.__data= {
            "jsonrpc": "2.0",
            "method": "logRoute",
            "id": 1
        }
        return self
    def dump(self)->str:
        """
        json序列化
        :return:
        """
        # print("asdasd ",self.__data)
        return jsonpickle.dumps(self.__data,unpicklable=False)
    def __repr__(self)->str:
        return self.dump()
    def __getstate__(self)->Dict[str, str]:
        return self.__data
    def __getitem__(self, item:str)->any:
        return self.__data[item]
    def __setitem__(self, key:str, value:any)->None:
        self.__data[key]=value