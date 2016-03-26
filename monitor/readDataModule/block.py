#coding=utf-8
'''
Created on 2014��5��15��

@author: zcan
'''
import subprocess
import time
#import time
import thread

class block():
    def __init__(self,dataSlot,dataKeeper):
        #self.__conn=dataKeeper["conn"]
        #self.__domain=dataKeeper["domain"]
        self.__dataSlot=dataSlot
        self.__pid=dataKeeper['pid']
        self.__name=dataKeeper["name"]
        self.__db=dataKeeper["minidb"]
        self.__int()
        
    def __int(self):
        minidb=self.__db
        if not minidb.has_key("blockNameList"):
            listcomm="virsh domblklist %s | grep -v .swap | awk 'NR>2{print $1}'"%(self.__name)
            Proc=subprocess.Popen(listcomm,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            error=Proc.stderr.readline()
            if not error:
                minidb["blockNameList"]=[]
                while True:
                    f=Proc.stdout.readline()[:-1]
                    if f:
                        minidb["blockNameList"].append(f)
                        self.__dataSlot["block"][f]={}
                    else:
                        break
            else:
                print "block plugin error:",error
            Proc.terminate()
            self.__initState()
            
    def __initState(self):
        minidb=self.__db
        if not minidb.has_key("blockStat"):
            minidb["blockStat"]={}
            minidb["blockStat"]["time"]=time.time()         
        name=self.__name
        nameList=self.__db["blockNameList"]
        if nameList:
            blockstat="virsh domblkstat "+name+" %s | awk 'NR<9{print $2,$3}'"
            blockStateCache=minidb["blockStat"]
            for dev in nameList:
                blockStateCache[dev]={}
                #start=time.time()
                Proc=subprocess.Popen(blockstat%(dev),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                #print "state",time.time()-start
                error=Proc.stderr.readline()
                if not error:
                    dataTmp=blockStateCache[dev]
                    while True:
                        statsData=Proc.stdout.readline()
                        if statsData:
                            keyToVal=statsData.split()
                            dataTmp[keyToVal[0]]=keyToVal[1]
                        else:
                            break
                else:
                    print "block plugin Method state error:",error  
                Proc.terminate()
            
    def usageAct(self):
        name=self.__name
        nameList=self.__db["blockNameList"]
        if nameList:
            blockinfo="virsh domblkinfo "+name+" %s | awk 'NR>0&&NR<3{print $2}'"
            for dev in nameList:
                #start=time.time()
                Proc=subprocess.Popen(blockinfo%(dev),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                #print "usageAct",time.time()-start
                dataTmp=self.__dataSlot["block"][dev]
                if not Proc.stderr.readline():
                    statsData=Proc.stdout.readlines()
                    dataTmp["total"]=int(statsData[0])
                    dataTmp["used"]=int(statsData[1])
                else:
                    dataTmp="null"
                Proc.terminate()
        else:
            self.__dataSlot["block"]="null"
        
        
    def state(self):
        name=self.__name
        blockCache=self.__db['blockStat']
        nameList=self.__db["blockNameList"]
        blockTmp={}
        blockTmp["time"]=time.time()
        if nameList:
            blockstat="virsh domblkstat "+name+" %s | awk 'NR<9{print $2,$3}'"
            for dev in nameList:
                blockTmp[dev]={}
                #start=time.time()
                Proc=subprocess.Popen(blockstat%(dev),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                #print "state",time.time()-start
                error=Proc.stderr.readline()
                if not error:
                    dataTmp=blockTmp[dev]
                    while True:
                        statsData=Proc.stdout.readline()
                        if statsData:
                            keyToVal=statsData.split()
                            dataTmp[keyToVal[0]]=keyToVal[1]
                        else:
                            break
                else:
                    print "block plugin Method state error:",error  
                Proc.terminate()              
        if nameList:
            for dev in nameList:
                lastDevStat=blockCache[dev]
                currDevStat=blockTmp[dev]
                rd_time=float(int(currDevStat['rd_total_times'])-int(lastDevStat['rd_total_times']))/(10**9)
                if rd_time:
                    tmp=(int(currDevStat['rd_bytes'])-int(lastDevStat['rd_bytes']))/rd_time
                    self.__dataSlot["block"][dev]['rds']=int(tmp)
                else:
                    self.__dataSlot["block"][dev]['rds']=0
                                  
                wr_time=float(int(currDevStat['wr_total_times'])-int(lastDevStat['wr_total_times']))/(10**9)
                
                if wr_time:
                    tmp=(int(currDevStat['wr_bytes'])-int(lastDevStat['wr_bytes']))/wr_time
                    self.__dataSlot["block"][dev]['wds']=int(tmp)
                else:
                    self.__dataSlot["block"][dev]['wds']=0
                flush_time=float(int(currDevStat['flush_total_times'])-int(lastDevStat['flush_total_times']))/(10**9)
                self.__dataSlot["block"][dev]['active_time']=round((flush_time+wr_time+rd_time)*1000,2)
        self.__db['blockStat']=blockTmp
            
def start(dataSlot,dataKeeper):#dataSlot数据格式为{"__name1":{'useage':'d.d.d.d','mhz':int1,...},"__name2":{'useage':'d.d.d.d','mhz':int1,...}}
    blo=block(dataSlot,dataKeeper)
    blo.usageAct()
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
    dataslot={"block":{}}
    dataKeeper={"minidb":{},"pid":getPidByName('instance-00000051'),"name":'instance-00000051'}
    #dataKeeper["conn"]=libvirt.openReadOnly("qemu+ssh://root@virtmaster/system")
    #dataKeeper["domain"]=dataKeeper["conn"].lookupByName("instance-00000051")
    for i in range(50):
        s=time.time()
        thread.start_new_thread(start, (dataslot,dataKeeper,))
        print "used time",time.time()-s,dataslot
        time.sleep(5)
'''       