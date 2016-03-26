#!/bin/bash
# 测试集群是否正常
trap "echo 'interrupted!';exit 1" SIGHUP SIGINT SIGTERM
declare -a ips=(
controller
network
region1
node1
node2
node3
node4
node5
node6
node7
node8
)
for i in ${ips[@]}
do
    if ping -c 2 $i &>/dev/null
    then
        echo $i ok!
    else
        echo $i dead!
    fi
done
