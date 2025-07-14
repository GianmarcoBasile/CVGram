import os
import boto3
import json
import socket
import subprocess
import time

KEY_NAME = "cvgram-key"

with open('ec2.json') as f:
    ec2_data = json.load(f)
    
ec2 = boto3.client('ec2', region_name='eu-west-2')
    
instance_ids = [ec2_data[key]['instance_id'] for key in ec2_data]

if not instance_ids:
    print("Nessuna istanza trovata in ec2.json.")
else:
  master_id = ec2_data['master']['instance_id']
  print(f"Avvio istanze EC2: {', '.join(instance_ids)}")
  ec2.start_instances(InstanceIds=instance_ids)
  waiter = ec2.get_waiter("instance_running")
  waiter.wait(InstanceIds=[master_id])
  master_ip = ec2.describe_instances(InstanceIds=[master_id])['Reservations'][0]['Instances'][0].get('PublicIpAddress')

  print(f"Istanze EC2 avviate: {', '.join(instance_ids)}")

  key_path = os.path.expanduser(f"~/.ssh/{KEY_NAME}.pem")
  
  cmd = [
      "ssh", "-i", key_path, f"ubuntu@{master_ip}",
      "nohup python3 /home/ubuntu/webhook.py > webhook.log 2>&1 &"
  ]
  subprocess.run(cmd)
