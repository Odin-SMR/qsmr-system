# Project Overview

This project handles the Odin SMR Level 2 using ECR images built with compiled
Matlab code. The images are deployed and run in AWS ECS Fargate. The full
deployment needs to be done manually using the provided `deploy.sh` script in
an enviroment with matlab installed.

Python code used by Matlab can be tested without a complete build.

Matlab calls python code to handle parquet file creation and SQS operations.

qsmr.m - Main Matlab function to process Level 2 data.

# Project aims

Provide a cost-effective and scalable solution for processing Level 2 data
using AWS services.

# Coding guidelines

- Follow code style enforced by `ruff`.
- Use type hints and validate with `ty`.
- Write unit tests using `pytest`.

For detailed setup and development instructions, please refer to our
[Development Guide](../README.md).