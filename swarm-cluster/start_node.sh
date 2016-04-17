#!/bin/bash
if [ ! $1 ]; then
	echo "usage: $0 name"
fi
NAME=$1
docker rm -f $NAME 2>/dev/null
docker run --privileged --name $NAME --hostname $NAME --restart=always -P -v /tmp/shares:/shares -v `pwd`/data/docker/$NAME:/var/lib/docker -d docker:dind --registry-mirror=http://xxx.m.daocloud.io # --api-cors-header='*'
