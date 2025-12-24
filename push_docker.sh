#!/bin/bash
# 替换为你的 DockerHub 用户名
USERNAME="hillerliao"
IMAGE_NAME="pyrsshub"
TAG="latest"

echo "Building Docker image..."
# Use --platform linux/amd64 to ensure compatibility with Zeabur/Server servers
docker build --platform linux/amd64 -t $USERNAME/$IMAGE_NAME:$TAG .

echo "Pushing to DockerHub..."
docker push $USERNAME/$IMAGE_NAME:$TAG

echo "Done! You can now deploy $USERNAME/$IMAGE_NAME:$TAG on Zeabur."
