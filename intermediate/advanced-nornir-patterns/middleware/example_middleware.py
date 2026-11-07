"""
Nornir middleware for logging, metrics, and validation
"""

from nornir import InitNornir
from nornir.core.inventory import Host
from nornir.core.task import Task, AggregatedResult, MultiResult, Result
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

# =====================================================================
# PRE-TASK MIDDLEWARE: Validation and setup
# =====================================================================

def validate_device(host: Host) -> Optional[str]:
    """
    Pre-flight check, run BEFORE nr.run() (see main() below)
    Returns a description of the problem, or None if the host looks usable
    """
    logger.debug(f"[Pre-flight] Validating {host.name}")

    # Example: Check if device credentials are set
    if not host.password:
        return f"No password configured for {host.name}"

    # Could also do ping check, device type validation, etc.
    return None

# =====================================================================
# POST-TASK MIDDLEWARE: Logging and metrics
# =====================================================================

def log_results(host: Host, result: MultiResult) -> None:
    """
    Post-task logging and metrics
    """
    status = "✓ Success" if not result.failed else "✗ Failed"
    
    logger.info(f"[Post-task] {host.name}: {status}")
    
    if result.failed:
        logger.error(f"[Error] {host.name}: {result[0].exception}")

def alert_on_failure(host: Host, result: MultiResult) -> None:
    """
    Alert (send Slack/email) if task fails
    """
    if result.failed:
        # Example: Send Slack notification
        # send_slack_alert(f"Task failed on {host.name}")
        logger.warning(f"Alert: Task failed on {host.name}")

class LoggingProcessor:
    """Nornir 3 processor for validation, logging, and alerts."""

    def task_started(self, task: Task) -> None:
        pass

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        pass

    def task_instance_started(self, task: Task, host: Host) -> None:
        # Processors observe; they can't fail a single host. An exception
        # raised here aborts the whole run for EVERY host, which is why
        # validation happens before nr.run() instead
        logger.debug(f"[Pre-task] {host.name}: starting {task.name}")

    def task_instance_completed(self, task: Task, host: Host, result: MultiResult) -> None:
        log_results(host, result)
        alert_on_failure(host, result)

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        pass

    def subtask_instance_completed(self, task: Task, host: Host, result: MultiResult) -> None:
        pass

# =====================================================================
# Using Middleware in Nornir
# =====================================================================

def my_task(task: Task) -> Result:
    """Stand-in for whichever task you want the middleware around."""
    return Result(host=task.host, result="ok")


def main():
    nornir = InitNornir(config_file="nornir_config.yaml")

    # Pre-flight: report and drop hosts that can't work, before the run
    problems = {name: validate_device(host) for name, host in nornir.inventory.hosts.items()}
    for problem in filter(None, problems.values()):
        logger.error(f"[Pre-flight] {problem}: skipping")
    nornir = nornir.filter(filter_func=lambda host: problems[host.name] is None)

    # Register middleware (runs on ALL tasks)
    nornir = nornir.with_processors([LoggingProcessor()])
    
    # Now all tasks get pre/post processing automatically
    results = nornir.run(task=my_task)
