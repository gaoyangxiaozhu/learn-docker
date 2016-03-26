# coding=utf-8
'''
Created on 2014年4月30日
'''
import instanceKeeper
import copy
import multiprocessing
import random
import traceback
import threading
import socket
import json
import sys
import time
import subprocess
import snydata
monitorItemList=["mem","cpu","block","interface"]
#注册要监控的控件，后期将实现自动加载##################################################
#需要添加子进程socket无法通信父进程重启功能
class monitor(multiprocessing.Process):
    __proc_stop=False             #线程开启与停止信号
    __procSleepTime=None         #取样间隔时间
    __modules=None                  #侦测插件模块容器
    __instanceProcInfoDict=None   #注册虚拟机信息列表和监控的线程容器{"name000":{"UUID":"ddd-dd-dd","name":name,"pid":ddd,"proc":process,recvPort:ddd,startTime:122222},...}
    __ratroQueue=None                    #进程通信的消息队列
    __instanceListenPortDict=None
    __udpserver=None
    __subSleepTime=None
    __dataQue=None #用来收集各个线程的数据
    __snycDataServer=None
    __instanceNum=None #表示总共有instance的线程数
    
    def __init__(self,procName,sleeptime,subProcSleepTime):#procName为当前进程名称，sleeptime主进程休眠时间，mysqlHost数据持久层主机ip，subProcSleepTime监控进程间隔时间
        multiprocessing.Process.__init__(self)
        self.__proc_stop=False
        self.__procSleepTime=sleeptime
        self._name=procName
        self.__subSleepTime=subProcSleepTime
        self.__modules=[]
        self.__instanceProcInfoDict={}
        self.__ratroQueue=multiprocessing.Queue()
        self.__instanceListenPortDict={}
        self.__dataQue=multiprocessing.Queue()
        self.__instanceNum={"num":0}


    def __init(self):
        #初始化侦听插件模块容器
        try:
            for item in monitorItemList:#monitorItemList是一个模拟的数据组#############################################
                self.__modules.append("readDataModule."+item)
        except:
            print "modules load error..."
            return
        #扫描新的虚拟机进程并添加到相应的__instanceThreadInfoDict字典中
        self.scanNewInstance()
        self.__udpserver=udpForInstanServer(self.__instanceListenPortDict,self.__ratroQueue)
        self.__snycDataServer=snyDataServer(self.__dataQue,self.__instanceNum)

        #self.__backupserver=snydata.backupServer(self.__instanceListenPortDict,self.__mysqlHost,self.__subSleepTime)
    def reInit(self):
        print("")
        
    def scanNewInstance(self):
        currenInstance=self.__instanceProcInfoDict
        toInstanceList=[]
        newInstanceInfo=self.getinstanceInfo()
        for instanceName in newInstanceInfo.keys():
            if instanceName not in currenInstance:
                toInstanceList.append(instanceName)
        #开始实例化监控进程
        for toinstance in toInstanceList:
            self.__instanceNum["num"]+=1;
            #newInstanceInfo[toinstance]['pid']=self.getPidByName(toinstance)
            instanceUUID=self.getUUIDByName(toinstance)
            newInstanceInfo[toinstance]['UUID']=instanceUUID
            recvPort=self.allocatPort()
            newInstanceInfo[toinstance]['port']=recvPort#把新的进程监听端口加入到维护队列
            self.__instanceListenPortDict[instanceUUID]=recvPort
            newInstanceInfo[toinstance]['startTime']=time.time()  #用来记录该进程的迭代次数用来区别线程的年龄
            instanceProc=instanceKeeper.watchProcess(dataQue=self.__dataQue,
                                                     machineInfo=copy.deepcopy(newInstanceInfo[toinstance]),
                                                     MM=self.__modules,
                                                     retroQue=self.__ratroQueue,
                                                     sleepTime=self.__subSleepTime)
            newInstanceInfo[toinstance]['proc']=instanceProc#把新的进程加入到维护队列
            currenInstance[toinstance]=copy.copy(newInstanceInfo[toinstance])#把新的监控实例信息加入到列表中
            try:
                instanceProc.start()
            except Exception,e:
                print "can't create new instance proccess"
                print e
                print traceback.format_exc()
                instanceProc.terminate()
        del newInstanceInfo#释放资源
                   
    def allocatPort(self):
        instancePort=None
        while True:
            instancePort=random.randint(10000,60000)
            msg=subprocess.Popen("lsof -i:%d"%(instancePort),shell=True,
                             stdout=subprocess.PIPE)
            if msg.stdout.readline():
                continue
            else:
                msg.terminate()
                break
        return instancePort
    
    def getUUIDByName(self,name):
        while True:
            files=subprocess.Popen("virsh domuuid %s"%(name),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if files.stderr.readline():
                print "get %s uuid error ! will try again..."%(name)
                time.sleep(5)
                continue
            uuid=files.stdout.readline()[:-1]
            files.terminate()
            return uuid
        
    def getPidByName(self,name):
        comm="ps aux | grep %s | grep -v 'grep' | awk '{print $2}'"%(name)
        pid=subprocess.Popen(comm,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        pidstr=pid.stdout.readline()[:-1]
        pid.terminate()
        return pidstr
    
    def getinstanceInfo(self):#有待优化，可以为此方法申请一个缓存
        instanceInfoDict={}
        tep=subprocess.Popen("virsh list |awk 'NR>2{printf(\"%s,\",$2)}'",shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        files=tep.stdout.readline().split(",")
        for item in files:
            if item:
                instanceInfoDict[item]={"name":item}
        tep.wait()
        return instanceInfoDict
            
    def run(self):
        self.__init()#系统的初始化
        time.sleep(1)
        print self.__instanceProcInfoDict
        self.__udpserver.start()
        self.__snycDataServer.start()
        print "monitor sercie start..."
        while not self.__proc_stop:
            self.scanNewInstance()
            que=self.__ratroQueue
            try:
                ratroAction=que.get(True, self.__procSleepTime)
                self.ratroDataHandler(ratroAction)
            except:
                continue    
        if self.__proc_stop:
            print "begin shut down..."
            currentProcDict=self.__instanceProcInfoDict
            #self.__udpserver.stop()
            for item in currentProcDict.values():
                if item["proc"].is_alive():
                    #item["proc"].stop()
                    item["proc"].terminate()
                    item["proc"].join()
            print "it has shutdown the subprocess"
            sys.exit()
                     
    def getName(self):
        return self.getName()
    
    def setSleep(self,time):
        self.__procSleepTime=time
        
    def getSleep(self):
        return self.__procSleepTime
    
    def stop(self):
        self.__proc_stop=True
        
    def closeProc(self,name):
        currentDict=self.__instanceProcInfoDict
        if currentDict.has_key(name):
            self.__instanceNum["num"]-=1
            currentDict[name]["proc"].terminate()
            print "terminal the process %s"%(name)
            currentDict[name]["proc"].join()                
            del self.__instanceListenPortDict[currentDict[name]["UUID"]]
            del currentDict[name]
               
    def ratroDataHandler(self,data={}):#data数据格式说明，总共分为两种反馈信息，监听线程的反馈和监控进程的反馈，其中upd__XXX开始的是监听进程的反馈，instance_XXX是监控进程的反馈
        #currentDict=self.__instanceProcInfoDict
        #监听进程的反馈信息，表示无法找到监听的虚拟机，有可能虚拟机已经关机或者销毁了，需要停止
        if data.has_key("instance_del"):#domain进程反馈的信息
            keyname=data["instance_del"]
            self.closeProc(keyname)
        #客户端无法收到相关虚拟机的进程的数据需要重新启动进程       
        elif data.has_key("udp_unRecvDataFrom"):
            procname=data['udp_unRecvDataFrom']
            self.closeProc(procname)
             
        #来自用户的请求删除特定的机器监听进程或者结束全部进程               
        elif data.has_key("udp_shutdown"):
            if type(data["udp_shutdown"]) is list:
                for sname in data['udp_shutdown']:
                    self.closeProc(sname)
            else:
                self.stop()    
            
#监听类
class udpForInstanServer(threading.Thread):
    __portDict=None
    __sock=None
    __is_stop=None
    __lockQue=None
    
    def __init__(self,namePortDict,ratroQueue):
        threading.Thread.__init__(self)
        self.__portDict=namePortDict
        self.__sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.__is_stop=False
        self.__lockQue=ratroQueue
        
    def handler(self,data,addr):
        try:
            print data
            jsonData=json.loads(data)#数据格式为{"reqPort":["name1","name2"]}
        except Exception,e:
            self.__sock.sendto("error data format",addr)
            print e
            return
        
        if jsonData.has_key("reqPort"):
            reqData=jsonData["reqPort"]
            portList=self.__portDict
            Tmp={}
            if type(reqData)is list: 
                for uuid in reqData:
                    if portList.has_key(uuid):
                        Tmp[uuid]=portList[uuid]
                    else:Tmp[uuid]=-1
                self.__sock.sendto(json.dumps(Tmp),addr)
                
            elif portList.has_key(reqData):
                Tmp[reqData]=portList[reqData]
                self.__sock.sendto(json.dumps(Tmp),addr)
            else:
                self.__sock.sendto('null',addr)
        elif jsonData.has_key("config"):
            self.__lockQue.put(jsonData["config"])
            self.__sock.sendto("it will be shutdown",addr)
            
    def run(self):
        self.__sock.bind(("",8003))
        while not self.__is_stop:
            data,addr=self.__sock.recvfrom(1024)
            self.handler(data,addr)#改进的时候可能需要多进程        
                
    def stop(self):
        self.__is_stop=True
        
#数据同步类
class snyDataServer(threading.Thread):
    __dataQue=None#提交数据的队列
    __host=None#要同步的数据库主机
    __instanceNum=None
    __tableName=None
    
    def __init__(self,dataQueue,num):
        threading.Thread.__init__(self)
        self.__dataQue=dataQueue
        self.__is_stop=False
        self.__instanceNum=num
        self.__tableKeeper=snydata.tableKeeper();
        
    def __handler(self):
        num=self.__instanceNum["num"]
        dataTmp=[]
        for i in range(num):
            data=self.__dataQue.get()
            dataTmp.append(data)
        conn=self.__tableKeeper.getconnect() #获取连接
        tableName=self.__tableKeeper.getTableName(conn)
        if tableName:
            snycThread=snydata.backupServer(dataTmp,tableName,self.__tableKeeper)
            snycThread.start()
        else:
            raise Exception("the tableName is error")
            
    def run(self):
        while not self.__is_stop:
            try:
                self.__handler()   
            except Exception,e:
                print e
                
    def stop(self):
        self.__is_stop=True
    
if __name__=="__main__":
    name="monitor"
    main_process_time=5
    subthread_time=60
    mo=monitor(name,main_process_time,subthread_time)
    mo.start()
    
     
     
     
      
        