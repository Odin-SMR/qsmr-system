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

## Testing the python code
tooling used to test the build locally before deploying to AWS.
 - ruff
 - ty
 - pytest
 - pre-commit

### Installing pre-commit hooks
```
pre-commit install
```

### Running tests
```
pre-commit run --all-files --hook-stage manual
```

## devcontainer local execution instructions
To test the build locally in a devcontainer, open the folder in VSCode and select "Reopen in container".

start the qsmr_batch service in the devcontainer terminal:
```
uv run /qsmr/run_qsmr.sh /opt/MATLAB/R2024b/
```

add a task to the queue:
```
aws --endpoint-url="http://localstack:4566" sqs send-message --queue-url http://localhost:4566/000000000000/tasks --message-body '{"source":"https://odin-smr.org/rest_api/v5/level1/2/14205733121/Log/", "target":"projectx"}'
```
results will be found in the S3 bucket:
```
aws --endpoint-url="http://localstack:4566" s3 ls odin-level2-batch/ --recursive | grep parquet
```

```
2026-01-10 13:04:39      13155 l2/project=projectx/freq_mode=2/2026-01-10 13:48:33      13155 l2/project=projectx/freq_mode=2/product=H2O-545GHz-15to30km/year=2023/month=09/ff73df70936d497cb703b7190a3ce23f-0.parquet
2026-01-10 13:48:33      14951 l2/project=projectx/freq_mode=2/product=HNO3-545GHz-20to50km/year=2023/month=09/ff73df70936d497cb703b7190a3ce23f-0.parquet
2026-01-10 13:48:33      41028 l2/project=projectx/freq_mode=2/product=O3-545GHz-20to85km/year=2023/month=09/ff73df70936d497cb703b7190a3ce23f-0.parquet
2026-01-10 13:48:33      14983 l2/project=projectx/freq_mode=2/product=O3-668-545GHz-25to45km/year=2023/month=09/ff73df70936d497cb703b7190a3ce23f-0.parquet
2026-01-10 13:48:33      35580 l2/project=projectx/freq_mode=2/product=Temperature-545GHz-15to65km/year=2023/month=09/ff73df70936d497cb703b7190a3ce23f-0.parquet
2026-01-10 13:48:33      32443 l2i/project=projectx/freq_mode=2/scan_id_prefix=34e/2bd883de23b04101aa6686a20ef16184-0.parquet
```

More test cases:
Arts error
```
aws --endpoint-url="http://localstack:4566" sqs send-message --queue-url http://localhost:4566/000000000000/tasks --message-body '{"source":"https://odin-smr.org/rest_api/v5/level1/2/13858867319/Log/", "target":"projectx"}'
```
Arts error
```
aws --endpoint-url="http://localstack:4566" sqs send-message --queue-url http://localhost:4566/000000000000/tasks --message-body '{"source":"https://odin-smr.org/rest_api/v5/level1/2/14753266563/Log/", "target":"projectx"}'
```

FM102 
```
aws --endpoint-url="http://localstack:4566" sqs send-message --queue-url http://localhost:4566/000000000000/tasks --message-body '{"source":"https://odin-smr.org/rest_api/v5/level1/102/15035098693/Log/", "target":"projectx"}'
```
FM102 ok!
```
aws --endpoint-url="http://localstack:4566" sqs send-message --queue-url http://localhost:4566/000000000000/tasks --message-body '{"source":"https://odin-smr.org/rest_api/v5/level1/102/15034821707/Log/", "target":"projectx"}'
```