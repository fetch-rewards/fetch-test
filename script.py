#!/usr/bin/env python3

import yaml
import boto3

with open("inp.yaml", 'r') as inp_data:
        inp=yaml.safe_load(inp_data)


client = boto3.client('ec2', region_name='us-east-1')

#Get latest Amazon Linux 2 AMI
filters = [ {'Name': 'name', 'Values': ['amzn2-ami-hvm-*']},
            {'Name': 'architecture','Values': ['x86_64']},
            {'Name': 'owner-alias','Values': ['amazon']},
            {'Name': 'state','Values': ['available']},
            {'Name': 'root-device-type','Values': ['ebs']},
            {'Name': 'virtualization-type','Values': ['hvm']},
            {'Name': 'hypervisor','Values': ['xen']}
          ]
response = client.describe_images(Owners=['amazon'], Filters=filters)

#Parsing input
imgId=response['Images'][0]['ImageId'] #Image Id
instType=inp['server']['instance_type'] #Instance Type

#Create Block devices mappings from list of volumes, also setup userdata
dev_list=[]  #Initialize device list for block mappings
init_config="#!/bin/bash \ncp /etc/fstab /etc/fstab/bkp ;\n"  #Initialize userdata script

for each in inp['server']['volumes']:
  block_devices={}
  block_devices['DeviceName']=each['device']
  block_devices['Ebs']={'DeleteOnTermination': True,'VolumeType': 'gp2','VolumeSize': each['size_gb']}
  dev_list.append(block_devices)
  init_config+="mkfs -t "+each['type']+" "+each['device']+";\nmkdir "+each['mount']+" ;\n"+"echo '"+each['device']+"  "+each['mount']+"  "+each['type']+" defaults,nofail 0 0' >> /etc/fstab ;\n"

init_config+="mount -a\n"  #Persist mounts


#Parse input and create userdata scripts for user creation and add ssh keys
for each in inp['server']['users']:
  init_config+="\nuseradd -m "+each['login']
  init_config+="\nmkdir -p /home/"+each['login']+"/.ssh"
  init_config+="\necho '"+inp['server']['users'][0]['ssh_key']+"' >> /home/"+each['login']+"/.ssh/authorized_keys"

#print(init_config)
print("Creating new instance with image {} and instance type {} .........".format(imgId,instType))

#init_config+="echo '"+inp['server']['users'][0]['ssh_key']+"' >> /home/ec2-user/.ssh/authorized_keys"
instance = client.run_instances(MinCount=1,MaxCount=1,ImageId=imgId,InstanceType=instType,BlockDeviceMappings=dev_list,UserData=init_config)
print("Instance created with instance id : {} and private IP {}".format(instance['Instances'][0]['InstanceId'] ,instance['Instances'][0]['PrivateIpAddress']))
