#!/bin/bash

# Deployment script for Karbon API Wrapper

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null
then
    echo "AWS CLI could not be found. Please install and configure it."
    exit 1
fi

# Build Docker image
docker build -t karbon-api-wrapper .

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Set AWS region
AWS_REGION="us-west-2"  # Change this to your preferred region

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names karbon-api-wrapper || aws ecr create-repository --repository-name karbon-api-wrapper

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push image to ECR
docker tag karbon-api-wrapper:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/karbon-api-wrapper:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/karbon-api-wrapper:latest

# Create EC2 instance and deploy container
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --count 1 \
    --instance-type t2.micro \
    --key-name my-key-pair \
    --security-group-ids sg-xxxxxxxx \
    --subnet-id subnet-xxxxxxxx \
    --user-data file://ec2-user-data.sh \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "EC2 instance $INSTANCE_ID is being created and configured."
echo "Please update the security group and subnet IDs in this script before running."

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP of the instance
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Deployment completed. Your API is accessible at: http://$PUBLIC_IP:8000"
echo "Note: It may take a few minutes for the instance to fully configure and start the Docker container."

# Create a simple health check script
cat << EOF > health_check.sh
#!/bin/bash
API_URL="http://$PUBLIC_IP:8000"
MAX_RETRIES=10
RETRY_INTERVAL=30

for i in \$(seq 1 \$MAX_RETRIES); do
    if curl -sSf \$API_URL/docs > /dev/null 2>&1; then
        echo "API is up and running!"
        exit 0
    else
        echo "Attempt \$i: API is not ready yet. Retrying in \$RETRY_INTERVAL seconds..."
        sleep \$RETRY_INTERVAL
    fi
done

echo "API failed to come up after \$MAX_RETRIES attempts."
exit 1
EOF

chmod +x health_check.sh

echo "Running health check..."
./health_check.sh

if [ $? -eq 0 ]; then
    echo "Deployment successful! The API is now accessible and functioning correctly."
else
    echo "Deployment may have issues. Please check the EC2 instance logs and troubleshoot as needed."
fi
