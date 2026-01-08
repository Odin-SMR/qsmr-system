#!/usr/bin/env bash
set -euo pipefail

awslocal s3 mb "s3://odin-level2-batch/l2/" || true
awslocal sqs create-queue --queue-name "${TASK_QUEUE_NAME:-tasks}" >/dev/null 2>&1 || true

echo "LocalStack bootstrap done."
