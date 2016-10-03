# coding=utf-8
'''
Created on 2014

@author: zcan
'''
import MySQLdb
import threading
import string
import time
########mysql的配置信息####################
mysql_user="root"
mysql_passwd="1q2w3e4r"
mysql_database="monitor"
mysql_port=3306
mysql_host="10.103.242.128"
max_record_table_num=10 #监控数据最大保留天数
########################################
class backupServer(threading.Thread):

    def __init__(self,data,tableName,tableKeeper):
        threading.Thread.__init__(self)
        self.__data=data
        self.__tableName=tableName
        self.__tableKeeper=tableKeeper

    #格式化为tuple格式数据(uuid,time,data)
    def __formatData(self,data):
        return (self.__tableName,data[1],int(string.atof(data[2])),data[0])

    def run(self):
        conn=self.__tableKeeper.getconnect()
        if conn:
            dataTmp=self.__data
            cur=conn.cursor()
            if type(dataTmp) is list:
                for item in self.__data:
                    formatData=self.__formatData(item)
                    cur.execute('''insert into %s(uuid,time,data) values('%s',%f,'%s')'''%formatData)
            else:
                formatData=self.__formatData(dataTmp)
                cur.execute('''insert into %s(uuid,time,data) values('%s',%f,'%s')'''%formatData)
            conn.commit()
            cur.close()
        else:
            print "updata fail because there is a error..."
        self.__tableKeeper.close()

class tableKeeper():
    def __init__(self):
        self.__tableName=None
        self.__connect=None

    def __removeTableByNum(self,cur):
        #开始删除多余的表
        cur.execute("show tables like 'instance%'")
        tables=cur.fetchall()
        remove_num=len(tables)-max_record_table_num
        if remove_num:
            table_list=[]
            for t in tables:
                table_list.append(t[0])
            table_list.sort()
            for i in range(remove_num):
                cur.execute("drop table %s"%table_list[i])
                print "delete table",table_list[i]

    def  getconnect(self):
        if self.__connect and self.__connect.open==True:
            return self.__connect

        connTime=0;
        conn=None
        while not conn and connTime<5:
            connTime+=1
            try:
                conn=MySQLdb.Connect(host=mysql_host,
                                     user=mysql_user,
                                     passwd=mysql_passwd,
                                     db=mysql_database,
                                     port=mysql_port)
            except MySQLdb.Error, e:
                print "Error %d:%s" % (e.args[0], e.args[1]),"try again to get table name %d"%connTime
            time.sleep(3)
        return conn

    def close(self):
        if self.__connect and self.__connect.open==True:
            self.__connect.close()

    def __check(self,conn):

        #开始检测是否存在
        if conn:
            tableName="instance"+time.strftime("%Y%m%d")
            cur=conn.cursor()
            res=cur.execute("show tables like '%s'"%tableName)
            if not res:
                cur.execute(''' CREATE TABLE `%s` (
                              `id` int(11) NOT NULL AUTO_INCREMENT,
                              `uuid` varchar(40) NOT NULL,
                              `time` double DEFAULT NULL,
                              `data` varchar(800) DEFAULT NULL,
                              PRIMARY KEY (`id`),
                              KEY `index_name` (`time`)
                            ) ENGINE=InnoDB '''%tableName)
                self.__removeTableByNum(cur) #该方法为删除多余table的信息
            conn.commit()
            cur.close()
            return tableName
        return None

    def getTableName(self, conn):
        if not self.__tableName or self.__tableName.find(time.strftime("%Y%m%d"))<0:
            self.__tableName=self.__check(conn)
        return self.__tableName


if __name__ =="__main__":
    '''
    threads=backupServer("10.103.242.57",("data data","uuid",time.time()),"instance")
    threads.start();
    '''
#     con=MySQLdb.Connect(host="10.103.242.128",user="root",passwd="1q2w3e4r",port=3306,db="monitor")
#     cur=con.cursor()
#     cur.execute("show databases")
#     print cur.fetchall()
#     cur.close()
#     con.close()
