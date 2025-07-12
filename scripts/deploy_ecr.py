
import subprocess
import json

REPO_NAME = "cvgram-backend"
AWS_REGION = "eu-west-2"

def run(cmd, check=True):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result

def main():
    print(f"Verifico se il repository {REPO_NAME} esiste su ECR...")
    try:
        run(f"aws ecr describe-repositories --repository-names {REPO_NAME} --region {AWS_REGION}")
    except subprocess.CalledProcessError:
        print(f"Creo il repository {REPO_NAME} su ECR...")
        run(f"aws ecr create-repository --repository-name {REPO_NAME} --region {AWS_REGION}")

    # 2. Ottieni URI repo
    
    res = subprocess.check_output(f"aws ecr describe-repositories --repository-names {REPO_NAME} --region {AWS_REGION}", shell=True)
    repo_uri = json.loads(res)["repositories"][0]["repositoryUri"]
    print(f"Repository URI: {repo_uri}")

    # 3. Build docker image
    print("Build dell'immagine Docker...")
    run(f"docker build -t {REPO_NAME}:latest ../Backend")

    # 4. Tag
    print("Tag dell'immagine...")
    run(f"docker tag {REPO_NAME}:latest {repo_uri}:latest")

    # 5. Login ECR
    print("Login a ECR...")
    run(f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {repo_uri}")

    # 6. Push
    print("Push dell'immagine su ECR...")
    run(f"docker push {repo_uri}:latest")

    print("Deploy ECR completato!")

if __name__ == "__main__":
    main()
