#coding=utf-8
'''
Created on 2014骞�鏈�5鏃�

@author: zcan
'''
import subprocess
import string
'''
import thread
import time
'''
class domainMem():
    def __init__(self,dataSlot,dataKeeper):
#         self.__conn=dataKeeper["conn"]
#         self.__domain=dataKeeper["domain"]
        self.__dataSlot=dataSlot
        self.__pid=dataKeeper['pid']
        self.__name=dataKeeper["name"]
        self.__db=dataKeeper["minidb"]
    def usageAct(self):
        pid=self.__pid
        name=self.__name
        memUse="cat /proc/%s/smaps | grep Private_ | awk 'BEGIN{sum=0}{sum+=$2}END{print sum}'"%(pid)
        rss="virsh dommemstat %s |grep rss|awk '{print $2}'"%(name)
        
        useProc=subprocess.Popen(memUse,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        dataTmp=None
        if not useProc.stderr.readline():
            dataTmp=string.atoi(useProc.stdout.readline())
        else:
            dataTmp=0
        self.__dataSlot["mem"]["use"]=dataTmp
        useProc.terminate()
        
        rssProc=subprocess.Popen(rss,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if not rssProc.stderr.readline():
            dataTmp=string.atoi(rssProc.stdout.readline())
        else:
            dataTmp=0
        self.__dataSlot["mem"]["rss"]=dataTmp
        rssProc.terminate()
        
    def actual(self):
        db=self.__db
        if not db.has_key("mem"):
            db["mem"]={}
            size="virsh dommemstat %s | awk 'NR==1{print $2}'"%(self.__name)
            sizeProc=subprocess.Popen(size,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            useData=None
            if not sizeProc.stderr.readline():
                useData=string.atoi(sizeProc.stdout.readline())
            self.__dataSlot["mem"]["actual"]=useData
            db["mem"]["actual"]=useData
            sizeProc.terminate()
        else:
            self.__dataSlot["mem"]["actual"]= db["mem"]["actual"]
            
def start(dataSlot,dataKeeper):#dataSlot鏁版嵁鏍煎紡涓簕"__name1":{'useage':'d.d.d.d','mhz':int1,...},"__name2":{'useage':'d.d.d.d','mhz':int1,...}}
    mem=domainMem(dataSlot,dataKeeper)
    mem.usageAct()
    mem.actual()
    #print dataSlot

'''
if __name__=="__main__":
    dataslot={"mem":{}}
    dataKeeper={"conn":None,"domain":None,"minidb":{},"pid":'2531',"name":'instance-0000008c'}
    #dataKeeper["conn"]=libvirt.openReadOnly("qemu+ssh://root@virtmaster/system")
    #dataKeeper["domain"]=dataKeeper["conn"].lookupByName("instance-00000051")
    
    for i in range(5):
        thread.start_new_thread(start, (dataslot,dataKeeper,))
        time.sleep(5)
            
'''