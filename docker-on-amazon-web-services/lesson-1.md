# Prepare the Instance and Install Docker

## Create an Ubuntu Instance

Create 1 Ubuntu 22.04 instance with following resources:

- Instance type: t2.small
- Number of instances: 1
- Name of the instance: Lesson1

## Install Docker on the Instance

```bash
wget https://releases.rancher.com/install-docker/20.10.sh
sh 20.10.sh
sudo systemctl status docker
sudo chmod 777 /var/run/docker.sock
```

or

```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

# First Application: Python/Flask service

1. Clone the repository:

   ```bash
   git clone https://github.com/Ttsartsidze/Python-Hello-World
   ```

2. Create Dockerfile with the following options (Frontend Application):

   1. Service version: `python:3-alpine`
   2. Working directory: `/service`
   3. Include `requirements.txt` file in the Docker image
   4. Build project with: `pip install -r requirements.txt`
   5. Copy all files from host to working directory
   6. Expose port 8080
   7. Execution command: `python3 app.py`

3. Build and run Docker container:

   1. Build Docker image with tag: `python-hello-world`
   2. Run the container in background (daemon mode)
   3. Map container port 8080 to host port 8081
   4. View container: `docker ps -a`
   5. Check logs: `docker logs <container-id>`
   6. Check port: `docker port <container-id>`
   7. Access the app via the instance's Public IPv4 DNS on port 8081

4. Add Security Group Inbound Rules:

   - Type: Custom TCP
   - Port range: 8081
   - CIDR Blocks: 0.0.0.0/0

5. Install AWS CLI and push to ECR:

   ```bash
   sudo apt-get update
   sudo apt install awscli
   ```

   - Create ECR Repository named: `python-hello-world`
   - Set up AWS credentials in `~/.aws/credentials`
   - Verify identity: `aws sts get-caller-identity`
   - Tag and push the image to ECR

<!-- Second Application:

1. Clone repo, we have Python Calculator service and we need to dockerize both of services: Create Dockerfile, Build Image and then run containers

1) git clone https://github.com/Ttsartsidze/Python-Calculator
2) Create Dockerfile with following options:
   Frontend Applicaton

1. Service version is python:2.7
2. Working directory is /app
3. You need /app folder in docker image to be able to run the command
4. Build this project with pip install -r requirements.txt
5. Expose this image on 5000 port
6. Exectuion command is python and app.py

3) Build Dockers
1) Build Docker image with tag python-calculator
1) Run the image in a container: 1) Run the calculator container in the background (daemon mode) with port 5000 from the container to port 8082 on the docker machine.
1) View your new container: docker ps -a
1) Check the logs for your containers: docker logs <container-id>
1) Check the port of the containers: docker port <container-id>
1) Open the app running on the docker machine:Browse this service with instance Public IPv4 DNS and Port 8082

2. For this instances you need to add Inbound rules on Security Groups with following options:
1. Type: Custom TCP
1. Port range: 8082
1. CIDR Blocks- 0.0.0.0/0
   Test Examples:
   input: (3+(4-1))_5 output: 30
   input: 2 _ x + 0.5 = 1 output: x = 0.25
   input: 2*x + 1 = 2*(1-x) output: x = 0.25
   Third Application
1. Clone repo, we have NodeJS service and we need to dockerize service: Create Dockerfile, Build Image and then run containers

1) git clone https://github.com/Ttsartsidze/NodeJS-web-app
2) Create Dockerfile with following options:

1. Service version is node:10
2. Working directory is /usr/app
3. You need package\*.json files in docker image to be able to run the command
4. Build this project with npm install
5. Copy all files from host to docker on working directory
6. Expose this image on 8080 port
7. Exectuion command is node and server.js

3) Build Docker image with tag nodejs-web-app
4) Run the image in a container: 1) Run the web-app container in the background (daemon mode) with port 8080 from the container to port 8080 on the docker machine.
5) View your new container: docker ps -a
6) Check the logs for your containers: docker logs <container-id>
7) Check the port of the containers: docker port <container-id>
8) Open the app running on the docker machine:Browse this service with instance Public IPv4 DNS and Port 8080

2. For this instances you need to add Inbound rules on Security Groups with following options:
1. Type: Custom TCP
1. Port range: 8080
1. CIDR Blocks- 0.0.0.0/0

1. Install Aws-cli on ubuntu instance
   a) sudo apt-get update
   b) sudo apt install awscli
1. Add ECR Repository on AWS with name nodejs-web-app From AWSUI
   a) Login to your ubuntu machine with aws credentials to push the image (Credentials can be found in Lab - aws details .) and then create this credentials in ~/.aws/credentials
   b) Create Repository with name: nodejs-web-app
   c) To get details about the current IAM identity: aws sts get-caller-identity
   d) Tag your frontend-middle-exam image so you can push the image to this repository.
   e) Push this image to your newly created AWS repository (ECR)

```

```-->
