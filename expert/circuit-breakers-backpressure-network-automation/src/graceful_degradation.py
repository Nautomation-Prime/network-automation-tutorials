# src/graceful_degradation.py
class DeploymentStrategy:
    """Deployment strategy with graceful degradation."""
    
    @staticmethod
    def incremental_deploy(
        devices: list,
        deploy_func,
        max_failures: int = 5,
        batch_size: int = 10,
        min_sample: int = 5
    ) -> dict:
        """
        Deploy incrementally, stopping if failure rate is too high.

        Args:
            devices: List of devices
            deploy_func: Function to deploy to device
            max_failures: Stop if failures reach this
            batch_size: Deploy in batches
            min_sample: Attempts needed before the failure-rate rule applies
        """
        results = {
            "total": len(devices),
            "success": 0,
            "failed": 0,
            "completed_batches": 0,
            "failures_detail": []
        }
        
        # Deploy in batches
        for batch_num, i in enumerate(range(0, len(devices), batch_size)):
            batch = devices[i:i+batch_size]
            
            print(f"\nBatch {batch_num+1}: Deploying {len(batch)} devices...")
            
            for device in batch:
                try:
                    deploy_func(device)
                    results["success"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["failures_detail"].append({
                        "device": device,
                        "error": str(e)
                    })
                    
                    # Stop if failures exceed threshold
                    failure_rate = results["failed"] / (results["success"] + results["failed"])
                    
                    if results["failed"] >= max_failures:
                        print(f"✗ Failure threshold ({max_failures}) reached, stopping deployment")
                        return results
                    
                    # A rate means nothing after one or two devices: without
                    # min_sample, a single first-device failure is "100%" and
                    # stops the run before max_failures ever applies
                    attempts = results["success"] + results["failed"]
                    if attempts >= min_sample and failure_rate > 0.5:
                        print(f"✗ Failure rate >50%, stopping deployment")
                        return results
            
            results["completed_batches"] += 1
            
            # Summary after batch
            print(f"  ✓ Success: {results['success']}")
            print(f"  ✗ Failed: {results['failed']}")
        
        return results
