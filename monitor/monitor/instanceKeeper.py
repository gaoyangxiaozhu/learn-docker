# coding=utf-8
'''
Created on 2014年5月2日

@author: zcan
'''
import multiprocessing 
import json
import importlib
import traceback
import threading
import socket
import thread
import subprocess
import time
#需要添加的soket的通信监听进程
class watchProcess(multiprocessing.Process):
    ITEMS_SIZE=20
    SLEEP_TIME=60
    MAX_TIME_DIFFER=1
    #URI="qemu+ssh://root@virtmaster/system"
    #全局变量区,以下的数据为进程和监控模块的共享数据区封装到了shareData字典中了
    '''
    conn=None#共享连接=>libvirt
    domain=None#共享的虚拟机域信息=>libvirt
    machine=None#要监控的虚拟机的信息
    commonTmp={"cpu_last_time":100000}#监控模块的共享数据去
    '''
    __dataKeeper=None 
    __stop_monitor_proc=None
    __monitorModule=None#似有属性,用来存放要装载的监控模块
    __ratroQueue=None#反馈消息的队列
    __lockQue=None#队列锁机制，用于__domainData数据的安全
    __domainData=None#数据存储槽位，用来存储此进程所监控的虚拟机的数据，
    __slotCache=None#单个取样数据的缓存存放区
    __port=None
    __udpServer=None#传数据的udp服务器
    __machineInfo=None#数据格式为{"name":name,"UUID":'ddd-dd--ddd',"pid":ddd,"port":ddd,"cpu_cores":ddd}
    #__snyHost=None#同步数据的数据库主机名
    __moduleList=None#监控插件容器
    __dataQue=None
    __selfInitTime=None#初始化时的开始时间
    
    def __init__(self,machineInfo,MM,retroQue,sleepTime,dataQue):#name是虚拟机进程名也是id的名称，machine的结构为{“pid”:"ddd","uuid":"22323"}，MM(monitor mudole)监控组建
        multiprocessing.Process.__init__(self)
        self.__stop_monitor_proc=False
        self.__monitorModule=MM
        self.__sleepTime=sleepTime
        self.__ratroQueue=retroQue
        self.__machineInfo=machineInfo
        self.__dataQue=dataQue
    
    
    def __init(self):
        #初始化线程的基本属性
        self.__slotCache={}
        self._name=self.__machineInfo["name"]
        self.__port=self.__machineInfo["port"]
        self.__lockQue=multiprocessing.Queue()
        self.__lockQue.put("1")
        self.__dataKeeper={"minidb":{},"name":self.__machineInfo["name"]}
        self.__moduleList=[]  
        self.__dataKeeper["pid"]=self.__getPidByName(self.getName())
        if self.__sleepTime:
            self.SLEEP_TIME=self.__sleepTime
        #self.__udpServer=udpForInstanServer(self.__domainData,self.__lockQue,self.__port)
        #.setDaemon(True)
        for mm in self.__monitorModule:
            self.__moduleList.append(importlib.import_module(mm))
            self.__slotCache[mm.split(".")[1]]={}       
     
    def __getPidByName(self,name):
        comm="ps aux | grep %s | grep -v 'grep' | awk '{print $2}'"%(name)
        pid=subprocess.Popen(comm,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        pidstr=pid.stdout.readline()[:-1]
        pid.terminate()
        return pidstr
    
    def __doReInit(self):
        self.__dataKeeper["pid"]=self.__getPidByName(self.getName());
           
    def __doMonitor(self):
        cache=self.__slotCache
        start=time.time()
        for module in self.__moduleList:
            #start=time.time();
            module.start(cache,self.__dataKeeper)
        #print module,time.time()-start
        sampleTime=(time.time()+start)/2
        jsonStr=json.dumps(cache)
        self.__dataQue.put((jsonStr,self.__machineInfo['UUID'],sampleTime))
        #return sampleTime
          
    def __checkInstance(self):
        state=subprocess.Popen("virsh domstate %s"%(self.getName()),
                stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
        res=state.stdout.readline()
        status=0
        if res.count("running") or res.count("paused"):
            status=1
        state.terminate()
        return status
    
    #该进程主要负责向管理进程反馈信息，目前方法，只实现了请求删除本进程的内容
    def __doRatroActionToMonitor(self):
        print "%s apply shutdown"%(self.getName())
        self.__ratroQueue.put({"instance_del":self.getName()})
        
    #该方法负责计算时间误差，由于长时间的查询工作，可能会引起间隔时间内的误差，该误差特定为1秒  
    def __checkAndDoretra(self,curSampleTime):
        if not self.__selfInitTime:
            self.__selfInitTime=curSampleTime
        else:
            timeDiffer=(curSampleTime-self.__selfInitTime)%self.SLEEP_TIME
            return timeDiffer>self.SLEEP_TIME and self.SLEEP_TIME-timeDiffer>self.SLEEP_TIME
        return False
    
    def getName(self):
        return self._name
    
    def stop(self):
        self.__stop_monitor_proc=True
        
    def run(self):
        self.__init()
        print "start instance %s ..."%(self.getName())
        time.sleep(0.5)
        #self.__udpServer.start()
        start=time.time()
        while not self.__stop_monitor_proc:
            try:
                if self.__checkInstance():
                    self.__doReInit()
                    self.__doMonitor()
                    #self.__dataQue.get()
                else:
                    print "else statement"
                    self.__doRatroActionToMonitor()
                
                end=time.time()                   
                time.sleep(self.SLEEP_TIME-(end-start))
                start=time.time()
            except Exception ,e:
                print e
                print traceback.format_exc()
        if self.__stop_monitor_proc:
            print "%s will be shutdown"%(self._name)

class udpForInstanServer(threading.Thread):
    __domainData=None
    __sock=None
    __is_stop=None
    __lockQue=None
    __port=None
    def __init__(self,domainData,lockque,port):
        threading.Thread.__init__(self)
        self.__domainData=domainData
        self.__sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.__is_stop=False
        self.__lockQue=lockque
        self.__port=port

    def __getDataFromDomainDataByPoint(self):
        domainData=self.__domainData
        lock=self.__lockQue.get()
        tmp=domainData["items"][domainData["point"]]
        self.__lockQue.put(lock)
        return str(tmp)
       
    def __getAllDataFromDomainData(self):
        domainData=self.__domainData
        lock=self.__lockQue.get()
        point = domainData["point"]
        listTmp=str(domainData["items"][point::-1]+domainData["items"][:point:-1])
        self.__lockQue.put(lock)
        return listTmp
    
    def __dataStream(self,size,data,addr):
        sock=self.__sock
        point=0
        try:
            while True:
                tmp=data[point:point+size]
                sock.sendto(tmp,addr)
                if not tmp:break
                point+=size
        except Exception,e:
            print e
            print "time out"
                                  
    def handler(self,data,addr):
        try:
            jsonData=json.loads(data)#客户端数据格式为{"size":ddd,"initData":True|False}
        except Exception,e:
            self.__sock.sendto("error data format",addr)
            self.__sock.sendto("",addr)
            print e
            return       
        datatmp=None
        size=1024
        print jsonData        
        if jsonData.has_key("initData"):
            if jsonData["initData"]:
                datatmp=self.__getAllDataFromDomainData()
            else:
                datatmp=self.__getDataFromDomainDataByPoint()
        else:
            self.__sock.sendto("error there no initData key",addr)
            self.__sock.sendto("",addr)
            return
                
        if jsonData.has_key("size"):
            size=jsonData["size"]
        else:
            self.__sock.sendto("error there no size key",addr)
            self.__sock.sendto("",addr)
        self.__dataStream(size, datatmp, addr)
        
                         
    def run(self):
        self.__sock.bind(("",self.__port))
        while not self.__is_stop:
            data,addr=self.__sock.recvfrom(1024)    
            thread.start_new_thread(self.handler, (data,addr))
            
    def stop(self):
        self.__is_stop=True
'''
if __name__=="__main__":
    mm=["readDataModule.cpu","readDataModule.mem","readDataModule.block","readDataModule.interface"]
    name="instance-00000051"
    machinInfo={"port":23346,"name":"instance-00000032","UUID":"a483a6e0-bf48-4183-a413-7e3d3aaa1254"}
    que=multiprocessing.Queue()
    dataque=multiprocessing.Queue()
    watch=watchProcess(machinInfo,mm,que,10,dataque)
    watch.start()  
''' 
