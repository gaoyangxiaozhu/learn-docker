#coding=utf-8
'''
Created on 2014��5��15��

@author: zcan
'''
import subprocess
import time
#import time

class block():
    def __init__(self,dataSlot,dataKeeper):
        self.__dataSlot=dataSlot
        self.__pid=dataKeeper['pid']
        self.__name=dataKeeper["name"]
        self.__db=dataKeeper["minidb"]
        self.__int()
        
    def __int(self):
        minidb=self.__db
        if not minidb.has_key("interfaceNameList"):
            listcomm="virsh domiflist %s | awk 'NR>2{print $1}'"%(self.__name)
            Proc=subprocess.Popen(listcomm,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            error=Proc.stderr.readline()
            if not error:
                minidb["interfaceNameList"]=[]
                while True:
                    f=Proc.stdout.readline()[:-1]
                    if f:
                        minidb["interfaceNameList"].append(f)
                        self.__dataSlot["interface"][f]={}
                    else:
                        break
            else:
                print "block plugin error:",error
            Proc.terminate()
            
    def __getState(self): 
        name=self.__name
        nameList=self.__db["interfaceNameList"]
        statTmp={}
        if nameList:
            for dev in nameList:
                statTmp[dev]=[]
                #start=time.time()
                statTmp[dev].append(self.__getStateData(name,dev))
                time.sleep(0.5)
                statTmp[dev].append(self.__getStateData(name,dev))
        return statTmp
                
    def __getStateData(self,name,dev):
        tmp={}
        interfaceStat="virsh domifstat "+name+" %s | awk 'NR<9{print $2,$3}'"
        Proc=subprocess.Popen(interfaceStat%(dev),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        tmp['t']=time.time()
        #print "state",time.time()-start
        error=Proc.stderr.readline()
        if not error:
            while True:
                statsData=Proc.stdout.readline()
                if statsData:
                    keyToVal=statsData.split()
                    tmp[keyToVal[0]]=keyToVal[1]
                else:
                    break
        else:
            print "interface plugin Method state:",error
        Proc.terminate()
        return tmp
              
    def state(self):
        slot=self.__dataSlot['interface']
        stat=self.__getState()
        for netface in stat.keys():
            sta1=stat[netface][0]
            sta2=stat[netface][1]
            time_step=sta2['t']-sta1['t']
            slot[netface]['revs']=int((int(sta2['rx_bytes'])-int(sta1['rx_bytes']))/time_step)
            slot[netface]['trns']=int((int(sta2['tx_bytes'])-int(sta1['tx_bytes']))/time_step)
            slot[netface]['rb']=int(sta2['rx_bytes'])
            slot[netface]['tb']=int(sta2['tx_bytes'])
            slot[netface]['revpac']=int(sta2['rx_packets'])
            slot[netface]['trapac']=int(sta2['tx_packets'])
            
def start(dataSlot,dataKeeper):#dataSlot数据格式为{"__name1":{'useage':'d.d.d.d','mhz':int1,...},"__name2":{'useage':'d.d.d.d','mhz':int1,...}}
    blo=block(dataSlot,dataKeeper)
    #blo.usageAct()
    blo.state()
    #print dataSlot
'''
def getPidByName(name):
    comm="ps aux | grep %s | grep -v 'grep' | awk '{print $2}'"%(name)
    pid=subprocess.Popen(comm,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    pidstr=pid.stdout.readline()[:-1]
    pid.terminate()
    return pidstr

if __name__=="__main__":
    dataslot={"interface":{}}
    dataKeeper={"minidb":{},"pid":getPidByName('instance-00000051'),"name":'instance-00000051'}
    #dataKeeper["conn"]=libvirt.openReadOnly("qemu+ssh://root@virtmaster/system")
    #dataKeeper["domain"]=dataKeeper["conn"].lookupByName("instance-00000051")
    for i in range(50):
        s=time.time()
        thread.start_new_thread(start, (dataslot,dataKeeper,))
        print "used time",time.time()-s,dataslot
        time.sleep(5)
'''