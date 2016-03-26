
#!/bin/bash
declare -f showHelp
declare -f isReachable 
SERVER=10.3.8.211 # Change this value!
showHelp()
{
cat <<EOF
usage: $0 [-u username] [-p password] [-s url] [-h][-t]
	-u username
	-p password
	-s authentication server, default 10.3.8.211
	-h display this help and exit
	-t test the current network state and exit
EOF
exit 1
}
isReachable()
{
    ADDR=${1:-baidu.com}
    if which curl &>/dev/null
    then
	    curl -i $ADDR 2>/dev/null | head -n 1 | grep -q "200 OK"
	    return $?
    else
	    # FIXME ICMP may be disabled ?
	    ping -c 1 -w 2 $ADDR &>/dev/null
	    return $?
    fi
}
parseOpts()
{
    while getopts ":u:p:i:ht" arg
    do
        case $arg in
            u)
                ID=$OPTARG
                ;;
            p)
                PASSWORD=$OPTARG
                ;;
            h)
                showHelp
                exit 0
                ;;
            s)
                SERVER=$OPTARG
                ;;
            t)
                if isReachable 
                then
                    echo "OK"
                else
                    echo "Faild"
                fi
                exit 0
                ;;
            :|?|*)
                showHelp
                exit 1
                ;;
        esac
    done
}
inputUserName()
{
	read -p "Please type your username(学号): " ID
}
inputPassword()
{
	stty -echo
	read -p"Please type your password(密码): " PASSWORD
	stty echo
	echo
}
getRequest()
{
    if [ $# -lt 1 ]
    then
        echo "Usage $0 <url>"
        exit 1
    fi
    ADDRESS=$1
    curl -X GET $ADDRESS
}
postRequest()
{
    if [ $# -lt 2]
    then
        echo "Usage $0 <data> <url>"
        echo "For example: postRequest 'a=1&b=2' example.com"
        exit 1
    fi
    DATA=$1
    ADDRESS=$2
    curl -X POST -d $DATA $ADDRESS
}
request()
{
    getRequest $@
}
login()
{
    if [ x == x$SERVER ]
    then
        echo "The address of server not set"
        exit 1
    fi
    if ! isReachable $SERVER
    then
        echo "Cann't connect to authentication server!"
        exit 1
    fi
    [ x$ID == x ] && inputUserName
    [ x$PASSWORD == x ] && inputPassword
    postRequest "DDDDD=$ID&upass=$PASSWORD&save_me=1&R1=0" "$SERVER" &>/dev/null
}
checkDeps()
{
	declare -a deps # array
	deps=('curl')
	for package in ${deps[@]}
	do
		if ! which $package &>/dev/null
		then
			read -p "$package is not installed, now install? (y/n):" YES
			if [[ x$YES != xy ]]
			then
				echo "'$package' is not installed, exit..."
				exit 1
			else
				sudo apt-get -y install $package
				if ! which $package &>/dev/null
				then
					echo "Failed to install '$package', exit..."
					exit 1
				fi
			fi
		fi
	done
}
main()
{
    checkDeps
    parseOpts $@
    if isReachable baidu.com
    then
        echo "The network is OK!"
        exit 0
    fi
    login
    if isReachable baidu.com
    then
        echo "OK"
        exit 0
    else
        echo "Failed"
        exit 1
    fi
}
main $@
