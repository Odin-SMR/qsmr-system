#!/bin/bash

# AWS & Docker Variables
REPO="991049544436.dkr.ecr.eu-north-1.amazonaws.com/qsmr"
AWS_PROFILE="odin-cdk"
AWS_REGION="eu-north-1"

# Define FM and INVMODE combinations
declare -A FM_VALUES
FM_VALUES[stnd]="1 2 8 17"
FM_VALUES[meso]="13 14 19 21 22 24"

# Get Git commit short hash
GIT_HASH=$(git rev-parse --short HEAD)

# Login to AWS ECR
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $REPO

# Build and push images
for INVMODE in "${!FM_VALUES[@]}"; do
    for FM in ${FM_VALUES[$INVMODE]}; do
        TAG="${INVMODE}${FM}"
        echo "🚀 Building and pushing: $TAG (FM=$FM, INVMODE=$INVMODE)..."
        
        docker buildx build --push \
            --build-arg FM=$FM --build-arg INVMODE=$INVMODE \
            --provenance=false \
            --tag $REPO:$TAG \
            --tag $REPO:$TAG-$GIT_HASH .
        
        # Update ECS service
        aws ecs update-service --profile $AWS_PROFILE --cluster OdinApiCluster --service QSMR-$TAG --force-new-deployment &> /dev/null
    done
done

echo "✅ Build and deployment complete. Images tagged with Git hash: $GIT_HASH"
