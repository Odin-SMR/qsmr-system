#!/bin/env python3

import os
import json
import subprocess
import logging
import sys
from time import sleep
from boto3 import client

QSMR_BINARY = "/qsmr/run_qsmr.sh"
MATLAB_ROOT = "/opt/MATLAB/R2024b"
QUEUE_ENV = "QUEUE_NAME"

logger = logging.getLogger("odin.qsmr")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def process_message(message: str) -> bool:
    process_logger = logger.getChild("process")
    logger.setLevel(logging.INFO)
    try:
        json_data = json.loads(message)
    except json.JSONDecodeError as err:
        process_logger.error(f"Failed to parse JSON from message: {err}")
        return False

    source = json_data.get("source")
    target = json_data.get("target")

    if source and target:
        process_logger.info(f"starting Qsmr for {source}, results to {target}")
        process = subprocess.Popen(
            [QSMR_BINARY, MATLAB_ROOT, source, target],
            cwd="/tmp",
        )
        process.wait()
        process_logger.info(f"Exit code: {process.returncode}")
        if process.returncode != 0:
            process_logger.error(f"QSMR process failed with exit code {process.returncode}")
            return False
    else:
        process_logger.error(
            'Skipped a task due to missing "source" or "target" properties'
        )
        return False
    process_logger.info("completed job")
    return True


queue_name = os.environ.get(QUEUE_ENV, None)

if not queue_name:
    logger.critical(f"{QUEUE_ENV} environment variable must be set.")
    exit(1)

sqs_client = client("sqs")
while True:
    queue = sqs_client.get_queue_url(QueueName=queue_name)
    if not "QueueUrl" in queue:
        logger.warning(f'No queue "{queue_name}" found')
        sleep(30)
        continue
    logger.debug(f"Waiting for new messages from {queue['QueueUrl']}")
    response = sqs_client.receive_message(
        QueueUrl=queue["QueueUrl"],
        AttributeNames=["All"],
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,
    )

    if "Messages" in response:
        logger.info(
            f"Processing {len(response['Messages'])} messages from {queue_name}"
        )
        for message in response["Messages"]:
            if process_message(message["Body"]):
                sqs_client.delete_message(
                    QueueUrl=queue["QueueUrl"], ReceiptHandle=message["ReceiptHandle"]
                )
    logger.debug(f"No messages available")
    sleep(30)
