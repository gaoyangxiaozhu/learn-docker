#!/bin/bash
set -x
docker rm -f mysql 2>/dev/null
docker run --name mysql1 -v /tmp/mysql:/var/lib/mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=1q2w3e4r --restart=always -d mysql
