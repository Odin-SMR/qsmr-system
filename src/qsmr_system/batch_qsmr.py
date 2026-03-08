from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from boto3 import client
from pydantic import BaseModel

if TYPE_CHECKING:
    from mypy_boto3_sqs import SQSClient
    from mypy_boto3_sqs.type_defs import MessageTypeDef

QSMR_BINARY = "/qsmr/run_qsmr.sh"
MATLAB_ROOT = "/opt/MATLAB/R2024b"
QUEUE_ENV = "QUEUE_NAME"

QUEUE = os.environ.get(QUEUE_ENV, "Unknown")

logger = Logger(service="QSMR")
metrics = Metrics(namespace="QSMR", service=QUEUE)


class QSMRTask(BaseModel):
    source: str
    target: str


class Task:
    def __init__(self, sqs_client: SQSClient, queue_url: str, msg: MessageTypeDef):
        self._yielded_monotonic = time.perf_counter()
        self._client = sqs_client
        self._queue_url = queue_url
        self._receipt = msg["ReceiptHandle"]
        self._received = msg["Attributes"]["ApproximateReceiveCount"]
        self.task = QSMRTask.model_validate(json.loads(msg["Body"]))
        paths = urlparse(self.task.source).path.strip("/").split("/")
        if len(paths) != 6:
            raise ValueError(f"Unexpected source format: {self.task.source}")
        self.freq_mode = int(paths[3])
        self.stw = paths[4]
        logger.info(
            "Starting task",
            extra={
                "queue": QUEUE,
                "source": self.task.source,
                "freq_mode": self.freq_mode,
                "stw": self.stw,
            },
        )
        metrics.add_metric(name="TasksStarted", unit=MetricUnit.Count, value=1)
        metrics.flush_metrics()

    @property
    def processing_time_ms(self) -> int:
        return int((time.perf_counter() - self._yielded_monotonic) * 1000)

    def ack(self, reason: str | None = None):
        """Acknowledge successful handling of the SQS message.

        The optional *reason* is used to improve observability in CloudWatch
        by tagging why the task completed (e.g. "success", "empty_log",
        "freqmode_mismatch", "drop_after_retry").
        """

        logger.info(
            "Ack message",
            extra={
                "queue": QUEUE,
                "source": self.task.source,
                "reason": reason or "success",
            },
        )

        metrics.add_metric(name="TaskFinished", unit=MetricUnit.Count, value=1)
        # Reason-specific counters for finer breakdown in CloudWatch
        if reason:
            metrics.add_metric(
                name=f"TaskFinished_{reason}",
                unit=MetricUnit.Count,
                value=1,
            )
        metrics.add_metric(
            name="TaskProcessingTime",
            unit=MetricUnit.Milliseconds,
            value=self.processing_time_ms,
        )
        metrics.flush_metrics()
        if self._receipt:
            self._client.delete_message(
                QueueUrl=self._queue_url, ReceiptHandle=self._receipt
            )

    def nack(self, delay_seconds: int = 900, reason: str | None = None):
        logger.warning(
            "Nack message",
            extra={
                "queue": QUEUE,
                "source": self.task.source,
                "reason": reason or "processing_error",
            },
        )
        if self._received and int(self._received) >= 2:
            logger.error(
                "Drop message",
                extra={
                    "queue": QUEUE,
                    "source": self.task.source,
                },
            )
            metrics.add_metric(name="TaskDrop", unit=MetricUnit.Count, value=1)
            # Mark this completion explicitly as a drop after retries
            self.ack("drop_after_retry")
            return
        if self._receipt:
            metrics.add_metric(name="TaskRetry", unit=MetricUnit.Count, value=1)
            self._client.change_message_visibility(
                QueueUrl=self._queue_url,
                ReceiptHandle=self._receipt,
                VisibilityTimeout=int(delay_seconds),
            )
        metrics.flush_metrics()


def yield_queue_messages(queue_name=None):
    """
    Generator that yields messages from the SQS queue one at a time, blocking if none
    are available. Intended for use by MATLAB's Python integration.
    """

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
                    logger.debug(f"Yielding job: {job.task.source}")
                    yield job
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    metrics.add_metric(
                        name="TaskInvalidMessage", unit=MetricUnit.Count, value=1
                    )
                    metrics.flush_metrics()
                    if "ReceiptHandle" in message:
                        sqs_client.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
        else:
            logger.debug(
                "No messages received, polling again...", extra={"queue": QUEUE}
            )
            time.sleep(5)


queue_name = os.environ.get(QUEUE_ENV, None)

if not queue_name:
    logger.critical(f"{QUEUE_ENV} environment variable must be set.")
    exit(1)


# If run as a script, just print a message
if __name__ == "__main__":
    print("This module provides yield_queue_messages() for use by MATLAB.")
