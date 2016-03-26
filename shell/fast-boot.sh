image=d0a59d7c-0d60-43d5-9cd9-8e1942bde809
net=4ec0dedf-4658-4cea-87d8-f5fdd6237138
flavor=m1.small
security_group=default
key_name=root
name='test'
set -x
nova boot --flavor $flavor \
--image $image \
--nic net-id=$net \
$name
