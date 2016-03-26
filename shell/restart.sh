#!/bin/bash
declare -f restart-node
declare -f restart-region
declare -f restart-network
restart-node()
{
	if [[ $# -le 0 ]]
	then
		for i in node{1,2,3,4,5,6,7,8}
		do
			echo "restart $i ..." 
			ssh root@$i '~/restart-nova.sh'
		done
	else
		for i in $@
		do
			echo "restart $i ..." 
			ssh root@$i '~/restart-nova.sh'
		done
	fi
}
restart-region()
{
	echo "restart region..."
	ssh root@region1 '~/restart-nova.sh'
}
restart-network()
{

	echo "restart network..."
	ssh root@network '~/restart-neutron.sh'
}
cmd=${1:-"all"}
case $cmd in
	all)
		restart-region
		restart-network
		restart-node
		;;
	network)
		restart-network
		;;
	region)
		restart-region
		;;
	node)
		shift
		restart-node $@
		;;
	*)
		echo "$0 node|region|network args..."
esac
