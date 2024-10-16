#!/bin/bash

# Update the system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Pull the latest image from ECR
docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/karbon-api-wrapper:latest

# Run the container
docker run -d -p 80:8000 --name karbon-api-container $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/karbon-api-wrapper:latest

# Set up automatic updates (optional)
echo "0 2 * * * docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/karbon-api-wrapper:latest && docker stop karbon-api-container && docker rm karbon-api-container && docker run -d -p 80:8000 --name karbon-api-container $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/karbon-api-wrapper:latest" | crontab -
