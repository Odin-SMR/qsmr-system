#!/usr/bin/env bash
set -euo pipefail

awslocal s3 mb "${RESULT_BUCKET:-s3://odin-level2-batch}" || true
awslocal sqs create-queue --queue-name "${TASK_QUEUE_NAME:-tasks}" >/dev/null 2>&1 || true

echo "LocalStack bootstrap done."
