import boto3
import json

with open('ec2.json') as f:
    ec2_data = json.load(f)

instance_ids = [ec2_data[key]['instance_id'] for key in ec2_data]


if not instance_ids:
    print("Nessuna istanza trovata in ec2.json.")
else:
    ec2 = boto3.client('ec2', region_name='eu-west-2')
    ec2.stop_instances(InstanceIds=instance_ids)
    print(f"Istanze EC2 stoppate: {', '.join(instance_ids)}")
