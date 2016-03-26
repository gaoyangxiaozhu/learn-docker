# coding=utf-8
'''
Created on 2014骞�鏈�鏃�

@author: zcan
'''
import os
import string
import thread
import time
class vcpu():
    def __init__(self,dataSlot,dataKeeper):
        #self.__conn=dataKeeper["conn"]
        #self.__domain=dataKeeper["domain"]
        self.__dataSlot=dataSlot 
        self.__name=dataKeeper["name"]
        self.__pid=dataKeeper["pid"]
        self.__db=dataKeeper["minidb"]
    def usageAct(self):
        name=self.__name
        pid=self.__pid
        useAge="top -bn 1 -p %s |grep %s | awk '{print $9}'"%(pid,pid)
        vcpustime="virsh vcpuinfo %s |grep 'CPU time'|awk '{split($3,b,\"s\");print b[1]}'"%(name)
        usedtime="virsh cpu-stats %s --total|awk 'NR>2{print $2}'|awk 'BEGIN{sum=0}{sum+=$1}END{print sum}'"%(name)
        
        files=os.popen(useAge)
        useAgeTmp=files.readline()
        
        if useAgeTmp:
            useAge=string.atof(useAgeTmp)
        else:
            useAge=0
            
        files=os.popen(usedtime)
        usedTimeTmp=files.readline()
        if usedTimeTmp:
            usedTime=string.atof(usedTimeTmp)
        else:
            usedTime=0
        files=os.popen(vcpustime)
        sts=""
        while True:
            strs=files.readline()
            if strs:
                sts+=strs[:-1]+","
            else:
                break
        self.__dataSlot["cpu"]["core_time"]=sts
        self.__dataSlot["cpu"]["usedTime"]="%.3f"%(usedTime)
        self.__dataSlot["cpu"]["useAge"]=useAge
        
    def mhz(self):
        db=self.__db
        if not db.has_key("cpu"):
            db["cpu"]={}
            self.__dataSlot['cpu']['mhz']=os.popen("virsh nodeinfo |grep 'CPU frequency:'| awk '{printf(\"%d\",$3)}'").readline()
            db["cpu"]['mhz']=self.__dataSlot['cpu']['mhz']
        else:
            self.__dataSlot['cpu']['mhz']=db["cpu"]['mhz']
         
def start(dataSlot,dataKeeper):#dataSlot鏁版嵁鏍煎紡涓簕"__name1":{'useage':'d.d.d.d','mhz':int1,...},"__name2":{'useage':'d.d.d.d','mhz':int1,...}}
    cpu=vcpu(dataSlot,dataKeeper)
    cpu.usageAct()
    cpu.mhz()

'''
if __name__=="__main__":
    dataslot={"cpu":{}}
    dataKeeper={"conn":None,"domain":None,"minidb":{},"name":"instance-000000f9","pid":"141890"}
    
    for i in range(5):
        thread.start_new_thread(start, (dataslot,dataKeeper,))
        time.sleep(5)
        print dataslot                
'''
    
