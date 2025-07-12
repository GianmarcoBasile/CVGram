import socket
import boto3
import botocore
from dotenv import load_dotenv
import os
import subprocess
import time

load_dotenv()


ec2 = boto3.client('ec2', region_name='eu-west-2')

AMI_ID_MASTER = os.getenv("EC2_AMI_ID")
AMI_ID_WORKER = os.getenv("EC2_AMI_ID")
INSTANCE_TYPE_MASTER = os.getenv("EC2_INSTANCE_TYPE")
INSTANCE_TYPE_WORKER = os.getenv("EC2_INSTANCE_TYPE")
KEY_NAME = os.getenv("EC2_KEY_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SECURITY_GROUP_NAME = 'cvgram-backend-sg'
SECURITY_GROUP_DESC = 'Security group per backend CVGram'


USER_DATA = '''#!/bin/bash
sudo apt-get update
sudo apt-get install ca-certificates curl awscli -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y


'''

def wait_for_ssh(ip, port=22, timeout=300):
    print(f"⏳ Attendo che SSH sia disponibile su {ip}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((ip, port), timeout=5):
                print("✅ SSH disponibile!")
                return
        except Exception:
            time.sleep(5)
    raise TimeoutError(f"Timeout: SSH non disponibile su {ip} dopo {timeout} secondi.")

def create_security_group():
    try:
        response = ec2.create_security_group(
            GroupName=SECURITY_GROUP_NAME,
            Description=SECURITY_GROUP_DESC
        )
        sg_id = response['GroupId']
        print(f"✅ Security Group creato: {sg_id}")

        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 2377,
                    'ToPort': 2377,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        print("✅ Regole SSH e HTTP aggiunte")
        return sg_id
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
            # Security group già esistente, recupera l'ID
            response = ec2.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
            sg_id = response['SecurityGroups'][0]['GroupId']
            print(f"ℹ️ Security Group già esistente: {sg_id}")
            return sg_id
        else:
            raise
        
def create_key_pair(key_name, key_path):
    """Crea la key pair EC2 se non esiste e salva la chiave privata in key_path."""
    import os
    try:
        ec2.describe_key_pairs(KeyNames=[key_name])
        print(f"ℹ️ Key pair '{key_name}' già esistente su AWS.")
        if not os.path.exists(key_path):
            print(f"❗ La chiave privata non esiste in locale: {key_path}. Devi scaricarla manualmente dalla console AWS se vuoi usarla.")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
            print(f"🔑 Creo key pair '{key_name}' su AWS e salvo la chiave privata in {key_path}...")
            key_pair = ec2.create_key_pair(KeyName=key_name)
            with open(key_path, 'w') as f:
                f.write(key_pair['KeyMaterial'])
            os.chmod(key_path, 0o600)
            print(f"✅ Key pair '{key_name}' creata e chiave privata salvata.")
        else:
            raise

def create_ec2_instance(ami_id, instance_type, name, security_group_id, user_data):
    # Associa Instance Profile IAM solo al worker
    instance_profile = None
    if name == "worker":
        instance_profile = {'Name': 'backend-cv-access-role'}
    run_args = {
        'ImageId': ami_id,
        'InstanceType': instance_type,
        'KeyName': KEY_NAME,
        'SecurityGroupIds': [security_group_id],
        'MinCount': 1,
        'MaxCount': 1,
        'UserData': user_data,
        'TagSpecifications': [
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': name}]
            }
        ]
    }
    if instance_profile:
        run_args['IamInstanceProfile'] = instance_profile
    response = ec2.run_instances(**run_args)
    instance_id = response['Instances'][0]['InstanceId']
    print(f"✅ Istanza EC2 creata con ID: {instance_id}")
    # Attendi che l'istanza sia in stato 'running' e abbia un IP pubblico
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    desc = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = desc['Reservations'][0]['Instances'][0].get('PublicIpAddress')
    print(f"🌐 IP pubblico EC2: {public_ip}")
    return public_ip

def post_deploy_ec2():
    key_path = os.path.expanduser(f"~/.ssh/{KEY_NAME}.pem")
    ecr_login_cmd = "aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 177873418246.dkr.ecr.eu-west-2.amazonaws.com"

    for ip in [public_ip_master, public_ip_worker]:
        print(f"🔑 Eseguo login ECR su {ip}...")
        ssh_cmd = [
            "ssh",
            "-i", key_path,
            f"ubuntu@{ip}",
            ecr_login_cmd
        ]
        subprocess.run(ssh_cmd, check=True)
        print(f"✅ Login ECR completato su {ip}")
        
        subprocess.run(["sudo usermod -aG docker"], check=True)
        
        if ip == public_ip_master:
            cmd = [
                "docker", "service", "create",
                "--name", "backend",
                "--replicas", "2",
                "-p", "80:80",
                "--with-registry-auth",
                "--env", f"AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY_ID}",
                "--env", f"AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY}",
                "177873418246.dkr.ecr.eu-west-2.amazonaws.com/cvgram-backend:latest"
            ]
            subprocess.run(cmd, check=True)

if __name__ == "__main__":
    key_name = KEY_NAME
    key_path = os.path.expanduser("~/.ssh/" + key_name + ".pem")
    create_key_pair(key_name, key_path)
    sg_id = create_security_group()
    public_ip_master = create_ec2_instance(AMI_ID_MASTER, INSTANCE_TYPE_MASTER, "master", sg_id, USER_DATA)
    public_ip_worker = create_ec2_instance(AMI_ID_WORKER, INSTANCE_TYPE_WORKER, "worker", sg_id, USER_DATA)
    post_deploy_ec2()