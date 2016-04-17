#!/bin/bash
set -x
IP=`docker run --rm --net=host alpine ip route get 8.8.8.8 | awk '{ print $7;  }'`
NODES=`docker ps -f ancestor=docker:dind --format "{{.Ports}}" | awk -F'->' '{print $1}'`
NODES=$(echo $NODES | tr ' ' ',' | sed "s/0\.0\.0\.0/$IP/g")
docker rm -f controller &>/dev/null
docker run -d --restart=always --name controller --hostname controller -p 2377:2375 swarm manage   --api-enable-cors $NODES
