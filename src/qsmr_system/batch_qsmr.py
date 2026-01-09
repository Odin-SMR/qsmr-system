from __future__ import annotations

import json
import logging
import os
import sys
from typing import TYPE_CHECKING

from boto3 import client
from pydantic import BaseModel

if TYPE_CHECKING:  # Only needed for static type checkers, not at runtime
    from mypy_boto3_sqs import SQSClient
    from mypy_boto3_sqs.type_defs import MessageTypeDef

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


class QSMRTask(BaseModel):
    source: str
    target: str


class Task:
    def __init__(self, sqs_client: SQSClient, queue_url: str, msg: MessageTypeDef):
        self._client = sqs_client
        self._queue_url = queue_url
        self._receipt = msg["ReceiptHandle"]  # type: ignore
        self._received = msg["Attributes"]["ApproximateReceiveCount"]  # type: ignore
        self.task = QSMRTask.model_validate(json.loads(msg["Body"]))  # type: ignore

    def ack(self):
        print(f"Acknowledging message for task: {self.task.source}")
        if self._receipt:
            self._client.delete_message(
                QueueUrl=self._queue_url, ReceiptHandle=self._receipt
            )

    def nack(self, delay_seconds=0):
        print(f"Negatively acknowledging message for task: {self.task.source}")
        if self._received and int(self._received) >= 5:
            logger.error(
                f"Message {self.task.source} has failed processing {self._received} times. Dropping."
            )
            self.ack()
            return
        if self._receipt:
            self._client.change_message_visibility(
                QueueUrl=self._queue_url,
                ReceiptHandle=self._receipt,
                VisibilityTimeout=int(delay_seconds),
            )


def yield_queue_messages(queue_name=None):
    """
    Generator that yields messages from the SQS queue one at a time, blocking if none are available.
    Intended for use by MATLAB's Python integration.
    """
    import time

    if queue_name is None:
        queue_name = os.environ.get(QUEUE_ENV, None)
    if not queue_name:
        raise RuntimeError(f"{QUEUE_ENV} environment variable must be set.")
    # Use LocalStack endpoint if running in devcontainer
    region = os.environ.get("AWS_REGION")
    sqs_client = client("sqs", region_name=region)
    queue = sqs_client.get_queue_url(QueueName=queue_name)
    if "QueueUrl" not in queue:
        raise RuntimeError(f'No queue "{queue_name}" found')
    queue_url = queue["QueueUrl"]
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            AttributeNames=["All"],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,  # Long poll
        )
        if "Messages" in response:
            for message in response["Messages"]:
                try:
                    job = Task(sqs_client, queue_url, message)
                    print(f"Yielding job: {job.task.source}")
                    yield job
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    if "ReceiptHandle" in message:
                        sqs_client.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
        else:
            print("sleeping")
            time.sleep(5)


queue_name = os.environ.get(QUEUE_ENV, None)

if not queue_name:
    logger.critical(f"{QUEUE_ENV} environment variable must be set.")
    exit(1)


# If run as a script, just print a message
if __name__ == "__main__":
    print("This module provides yield_queue_messages() for use by MATLAB.")
