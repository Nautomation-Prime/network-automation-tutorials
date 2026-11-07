# src/aws_secrets.py
import boto3
import json

from src.vault_client import CredentialRetrievalError, CredentialsNotFoundError

class AWSSecretsManager:
    """Retrieve credentials from AWS Secrets Manager."""
    
    def __init__(self, region_name="us-east-1"):
        """Initialize AWS Secrets Manager client."""
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def get_secret(self, secret_name):
        """
        Retrieve secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of secret (e.g., 'network/router1')
        
        Returns:
            dict: Parsed secret data
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse JSON if stored as string
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                # Binary secret
                return response['SecretBinary']
        
        except self.client.exceptions.ResourceNotFoundException:
            raise CredentialsNotFoundError(
                f"Secret '{secret_name}' not found in AWS"
            )
        except Exception as e:
            raise CredentialRetrievalError(str(e))
    
    def get_device_credentials(self, device_name):
        """Retrieve device credentials from AWS."""
        secret_name = f"network/{device_name}"
        return self.get_secret(secret_name)
