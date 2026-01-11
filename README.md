# qsmr-system

**This repo is deployed manually. Use the deploy.sh script to deploy to production**

The pupose of this repo is to build docker images with a compiled versions of qsmr with precompiled data from qsmr-data.

The reason to do this is to be able to run qmsr on any computer, without Matlab installed.

The docker images are deployed to AWS ECR and run in AWS ECS Fargate handled by repo:Odin-SMR/odin-l2-workflow

## Build requirements

Requirements to build the qsmr image to run in AWS ECS:

 1. Docker
 1. Matlab with Matlab compiler
 1. Credentials to odin on AWS

The repo have two submodules. To update the submodules i.e if qsmr or qsmr-data have changes to be incorporated in the build.
```
git submodule update --recursive
```
### Build and deploy instructions
```
./deploy.sh
```

## devcontainer local execution instructions
To test the build locally in a devcontainer, open the folder in VSCode and select "Reopen in container".

start the qsmr_batch service in the devcontainer terminal:
```
uv run /qsmr/run_qsmr.sh /opt/MATLAB/R2024b/
```

add a task to the queue:
```
aws --endpoint-url="http://localstack:4566" sqs send-message --queue-url http://localhost:4566/000000000000/tasks --message-body '{"source":"https://
odin-smr.org/rest_api/v5/level1/2/14205733121/Log/", "target":"projectx"}'
```
results will be in found:
```
aws --endpoint-url="http://localstack:4566" s3 ls odin-level2-batch/ --recursive | grep parquet
```

```
2026-01-10 13:04:39      13155 l2/project=projectx/freq_mode=2/product=H2O-545GHz-15to30km/year=2023/month=09/dfae3efc4020407088e8f77645f7d149-0.parquet
2026-01-10 13:04:39      14951 l2/project=projectx/freq_mode=2/product=HNO3-545GHz-20to50km/year=2023/month=09/dfae3efc4020407088e8f77645f7d149-0.parquet
2026-01-10 13:04:39      41028 l2/project=projectx/freq_mode=2/product=O3-545GHz-20to85km/year=2023/month=09/dfae3efc4020407088e8f77645f7d149-0.parquet
2026-01-10 13:04:39      14983 l2/project=projectx/freq_mode=2/product=O3-668-545GHz-25to45km/year=2023/month=09/dfae3efc4020407088e8f77645f7d149-0.parquet
2026-01-10 13:04:39      35580 l2/project=projectx/freq_mode=2/product=Temperature-545GHz-15to65km/year=2023/month=09/dfae3efc4020407088e8f77645f7d149-0.parquet
```