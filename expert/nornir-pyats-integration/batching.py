# batching.py
from typing import List, Dict, Callable
from dataclasses import dataclass
import time
import structlog

from orchestrator.integration import OrchestrationEngine, DeploymentRecord

logger = structlog.get_logger()


@dataclass
class BatchConfig:
    """Configuration for batched deployments"""
    batch_size: int = 50
    delay_between_batches: int = 30  # seconds
    continue_on_batch_failure: bool = False
    rollback_threshold: float = 0.30  # Rollback if >30% of batch fails


class BatchedDeploymentEngine:
    """
    Execute deployments in controlled batches.
    
    Use cases:
    - Deploy to 1000+ devices without overwhelming infrastructure
    - Maintain control plane stability
    - Allow staged rollouts with monitoring between batches
    """
    
    def __init__(self, engine: OrchestrationEngine, config: BatchConfig):
        self.engine = engine
        self.config = config
    
    def deploy_in_batches(
        self,
        devices: List[str],
        commands: List[str],
        validation_features: List[str],
    ) -> Dict[int, DeploymentRecord]:
        """
        Execute deployment across devices in batches.
        
        Returns:
            Dictionary mapping batch number to DeploymentRecord
        """
        # Split devices into batches
        batches = [
            devices[i:i + self.config.batch_size]
            for i in range(0, len(devices), self.config.batch_size)
        ]
        
        logger.info(
            "batched_deployment_starting",
            total_devices=len(devices),
            batch_count=len(batches),
            batch_size=self.config.batch_size
        )
        
        batch_results = {}
        
        for batch_num, batch_devices in enumerate(batches, 1):
            logger.info(
                "executing_batch",
                batch_num=batch_num,
                total_batches=len(batches),
                devices=len(batch_devices)
            )
            
            # Execute batch
            deployment = self.engine.deploy_with_validation(
                devices=batch_devices,
                commands=commands,
                validation_features=validation_features,
                rollback_on_failure=True,
                parallel=True
            )
            
            batch_results[batch_num] = deployment
            
            # Analyze batch results
            success_rate = self._calculate_success_rate(deployment)
            
            logger.info(
                "batch_complete",
                batch_num=batch_num,
                success_rate=f"{success_rate:.1%}"
            )
            
            # Check if we should continue
            if success_rate < (1 - self.config.rollback_threshold):
                logger.critical(
                    "batch_failure_threshold_exceeded",
                    batch_num=batch_num,
                    success_rate=f"{success_rate:.1%}",
                    threshold=f"{(1-self.config.rollback_threshold):.1%}"
                )
                
                if not self.config.continue_on_batch_failure:
                    logger.error("aborting_remaining_batches")
                    break
            
            # Delay between batches (except for last batch)
            if batch_num < len(batches):
                logger.info(
                    "batch_delay",
                    delay_seconds=self.config.delay_between_batches
                )
                time.sleep(self.config.delay_between_batches)
        
        return batch_results
    
    def _calculate_success_rate(self, deployment: DeploymentRecord) -> float:
        """Calculate success rate for a deployment"""
        if not deployment.change_records:
            return 0.0
        
        successful = sum(
            1 for cr in deployment.change_records.values()
            if cr.state.value == 'completed'
        )
        
        return successful / len(deployment.change_records)


# Usage Example
def large_scale_deployment():
    """Deploy to 500 devices in batches"""
    
    base_engine = OrchestrationEngine(
        nornir_config='config.yaml',
        pyats_testbed='testbed.yaml',
        dry_run=False
    )
    
    batch_config = BatchConfig(
        batch_size=50,
        delay_between_batches=60,
        continue_on_batch_failure=False,
        rollback_threshold=0.20
    )
    
    batched_engine = BatchedDeploymentEngine(base_engine, batch_config)
    
    # Execute across 500 devices
    all_devices = [f"device_{i:03d}" for i in range(1, 501)]
    commands = ['ntp server 10.0.0.1']
    
    results = batched_engine.deploy_in_batches(
        devices=all_devices,
        commands=commands,
        validation_features=['interface']
    )
    
    # Analyze overall results
    total_success = sum(
        len([cr for cr in dep.change_records.values() if cr.state.value == 'completed'])
        for dep in results.values()
    )
    
    print(f"Deployment complete: {total_success}/{len(all_devices)} successful")
