# src/nornir_logging_task.py
from nornir import InitNornir
from nornir.core.task import Task, Result
from contextual_logging import OperationLogger
from structured_logger import StructuredLogger

logger = StructuredLogger(__name__)
op_logger = OperationLogger(logger)

def deploy_with_logging(task: Task) -> Result:
    """Nornir task with structured logging."""
    with op_logger.operation("device_deployment", device=task.host.name):
        device = task.host.get_connection("netmiko", task.nornir.config)
        
        with op_logger.operation("get_current_state", device=task.host.name):
            current_config = device.send_command("show running-config")
            logger.debug(
                "Current configuration retrieved",
                device=task.host.name,
                config_lines=len(current_config.split('\n'))
            )
        
        with op_logger.operation("apply_changes", device=task.host.name):
            device.send_config_set([f"hostname {task.host.name}"])
            logger.info(
                "Configuration changes applied",
                device=task.host.name
            )
        
        return Result(
            host=task.host,
            result="Deployment successful"
        )

# Usage
nr = InitNornir(config_file="config.yaml")
results = nr.run(task=deploy_with_logging)
