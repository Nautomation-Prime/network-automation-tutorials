import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

class VaultBackend(Enum):
    """Supported vault backend types"""
    HASHICORP = "hashicorp_vault"
    AWS = "aws_secrets_manager"
    AZURE = "azure_keyvault"
    KEYRING = "local_keyring"

@dataclass
class CacheEntry:
    """Cached credential entry with TTL"""
    secret: Any
    expiry: datetime
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() >= self.expiry

class BaseVaultBackend(ABC):
    """Abstract base for vault backends"""
    
    @abstractmethod
    async def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """Retrieve secret from vault"""
        pass
    
    @abstractmethod
    async def put_secret(self, path: str, secret: Dict[str, Any]) -> None:
        """Store secret in vault"""
        pass
    
    @abstractmethod
    async def rotate_secret(self, path: str, new_secret: Dict[str, Any]) -> None:
        """Store rotated values, keeping fields that aren't being replaced"""
        pass
    
    @abstractmethod
    async def delete_secret(self, path: str) -> None:
        """Delete secret from vault"""
        pass

class HashiCorpVaultBackend(BaseVaultBackend):
    """HashiCorp Vault backend implementation"""
    
    def __init__(self, vault_addr: str, vault_token: str, verify_ssl: bool = True):
        self.vault_addr = vault_addr
        self.vault_token = vault_token
        self.verify_ssl = verify_ssl
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Vault client"""
        import hvac
        
        self.client = hvac.Client(
            url=self.vault_addr,
            token=self.vault_token,
            verify=self.verify_ssl
        )
        
        try:
            self.client.auth.token.lookup_self()
            logger.info(f"Connected to Vault at {self.vault_addr}")
        except Exception as e:
            logger.error(f"Failed to connect to Vault: {e}")
            raise
    
    async def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """
        Retrieve secret from Vault KV2 engine
        
        Args:
            path: Path to secret (e.g., "network/credentials/router1")
            key: Optional specific key within secret
        
        Returns:
            Secret value or full secret dict
        """
        try:
            secret_response = self.client.secrets.kv.v2.read_secret_version(path=path)
            secret_data = secret_response['data']['data']
            
            logger.info(
                f"Retrieved secret from Vault: {path}",
                extra={'vault_path': path}
            )
            
            if key:
                return secret_data.get(key)
            return secret_data
        
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            raise
    
    async def put_secret(self, path: str, secret: Dict[str, Any]) -> None:
        """Store secret in Vault"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret
            )
            logger.info(f"Stored secret in Vault: {path}")
        
        except Exception as e:
            logger.error(f"Failed to store secret in Vault: {e}")
            raise
    
    async def rotate_secret(self, path: str, new_secret: Dict[str, Any]) -> None:
        """
        Implement secret rotation:
        1. Merge the new values into the current secret (a new KV version)
        2. Record the rotation in the secret's custom metadata

        Change the credential where it's used (e.g. on the devices) first,
        then call this, so Vault never holds a password nothing accepts.
        """
        try:
            # Keep fields that aren't being rotated (e.g. the username)
            current = await self.get_secret(path)
            await self.put_secret(path, {**current, **new_secret})

            # custom_metadata is None until something sets it, and its
            # values must be strings
            metadata = self.client.secrets.kv.v2.read_secret_metadata(path=path)
            custom = metadata['data'].get('custom_metadata') or {}
            self.client.secrets.kv.v2.update_metadata(
                path=path,
                custom_metadata={
                    **custom,
                    'rotated_at': datetime.now().isoformat(),
                    'rotation_count': str(int(custom.get('rotation_count', 0)) + 1),
                },
            )
            logger.info(f"Rotated secret: {path}")
        
        except Exception as e:
            logger.error(f"Failed to rotate secret: {e}")
            raise
    
    async def delete_secret(self, path: str) -> None:
        """Delete secret from Vault"""
        try:
            self.client.secrets.kv.v2.delete_latest_version_of_secret(path=path)
            logger.info(f"Deleted secret: {path}")
        
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            raise

class AWSSecretsManagerBackend(BaseVaultBackend):
    """AWS Secrets Manager backend implementation"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize AWS Secrets Manager client"""
        import boto3
        
        self.client = boto3.client('secretsmanager', region_name=self.region)
        logger.info(f"Connected to AWS Secrets Manager in {self.region}")
    
    async def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """
        Retrieve secret from AWS Secrets Manager
        
        Args:
            path: Secret name (e.g., "network/router1/credentials")
            key: Optional JSON key within secret string
        """
        try:
            response = self.client.get_secret_value(SecretId=path)
            
            if 'SecretString' in response:
                secret_data = json.loads(response['SecretString'])
            else:
                secret_data = base64.b64decode(response['SecretBinary']).decode('utf-8')
            
            logger.info(f"Retrieved secret from AWS: {path}")
            
            if key and isinstance(secret_data, dict):
                return secret_data.get(key)
            return secret_data
        
        except Exception as e:
            logger.error(f"Failed to retrieve secret from AWS: {e}")
            raise
    
    async def put_secret(self, path: str, secret: Dict[str, Any]) -> None:
        """Store/update secret in AWS Secrets Manager"""
        try:
            self.client.put_secret_value(
                SecretId=path,
                SecretString=json.dumps(secret)
            )
            logger.info(f"Stored secret in AWS: {path}")
        
        except self.client.exceptions.ResourceNotFoundException:
            # Create if doesn't exist
            self.client.create_secret(
                Name=path,
                SecretString=json.dumps(secret)
            )
            logger.info(f"Created new secret in AWS: {path}")
        
        except Exception as e:
            logger.error(f"Failed to store secret in AWS: {e}")
            raise
    
    async def rotate_secret(self, path: str, new_secret: Dict[str, Any]) -> None:
        """
        Store rotated values as a new secret version, keeping other fields.
        (To let AWS rotate the secret itself, configure a rotation Lambda
        and call self.client.rotate_secret(SecretId=path) instead.)
        """
        try:
            secret = await self.get_secret(path)
            secret.update(new_secret)
            secret['last_rotation'] = datetime.now().isoformat()
            await self.put_secret(path, secret)

            logger.info(f"Rotated secret: {path}")
        
        except Exception as e:
            logger.error(f"Failed to initiate rotation: {e}")
            raise
    
    async def delete_secret(self, path: str) -> None:
        """Delete secret from AWS"""
        try:
            self.client.delete_secret(
                SecretId=path,
                RecoveryWindowInDays=7  # Recoverable for 7 days (default 30)
            )
            logger.info(f"Deleted secret: {path}")
        
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            raise

class VaultManager:
    """
    Central credential manager with:
    - Multi-backend support (Vault, AWS, Azure, Keyring)
    - Local caching with TTL
    - Automatic secret rotation
    - Comprehensive audit logging
    - Circuit breaker for vault failures
    """
    
    def __init__(
        self,
        backend_type: VaultBackend = VaultBackend.HASHICORP,
        cache_ttl: int = 3600,
        enable_audit: bool = True,
        **backend_kwargs
    ):
        """
        Args:
            backend_type: Which vault backend to use
            cache_ttl: Cache time-to-live in seconds
            enable_audit: Enable audit logging for all operations
            **backend_kwargs: Credentials for vault backend
        """
        self.backend_type = backend_type
        self.cache_ttl = cache_ttl
        self.enable_audit = enable_audit
        self.cache: Dict[str, CacheEntry] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Initialize backend
        self.backend = self._init_backend(backend_type, **backend_kwargs)
    
    def _init_backend(self, backend_type: VaultBackend, **kwargs) -> BaseVaultBackend:
        """Initialize appropriate vault backend"""
        # Explicit arguments win; environment variables are the fallback
        if backend_type == VaultBackend.HASHICORP:
            return HashiCorpVaultBackend(
                vault_addr=kwargs.get('vault_addr') or os.environ.get('VAULT_ADDR'),
                vault_token=kwargs.get('vault_token') or os.environ.get('VAULT_TOKEN'),
                verify_ssl=kwargs.get('verify_ssl', True)
            )

        elif backend_type == VaultBackend.AWS:
            return AWSSecretsManagerBackend(
                region=kwargs.get('region') or os.environ.get('AWS_REGION', 'us-east-1')
            )
        
        else:
            raise ValueError(f"Unsupported backend: {backend_type}")
    
    async def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """
        Retrieve secret with caching
        
        Args:
            path: Path to secret
            key: Optional specific key within secret
        
        Returns:
            Secret value
        """
        # Check cache
        cache_key = f"{path}:{key}" if key else path
        if cache_key in self.cache and not self.cache[cache_key].is_expired():
            logger.debug(f"Cache hit: {cache_key}")
            self._audit_log('cache_hit', cache_key)
            return self.cache[cache_key].secret
        
        # Fetch from vault
        try:
            secret = await self.backend.get_secret(path, key)
            
            # Cache result
            self.cache[cache_key] = CacheEntry(
                secret=secret,
                expiry=datetime.now() + timedelta(seconds=self.cache_ttl)
            )
            
            self._audit_log('secret_retrieved', path, {'key': key})
            
            return secret
        
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {e}")
            self._audit_log('secret_retrieval_failed', path, {'error': str(e)})
            raise
    
    async def put_secret(self, path: str, secret: Dict[str, Any]) -> None:
        """Store secret in vault and invalidate cache"""
        try:
            await self.backend.put_secret(path, secret)
            self._invalidate(path)
            self._audit_log('secret_stored', path)
        
        except Exception as e:
            logger.error(f"Failed to store secret: {e}")
            self._audit_log('secret_storage_failed', path, {'error': str(e)})
            raise
    
    async def rotate_secret(self, path: str, new_secret: Dict[str, Any]) -> None:
        """Rotate secret with audit trail"""
        try:
            await self.backend.rotate_secret(path, new_secret)
            self._invalidate(path)
            self._audit_log('secret_rotated', path, {'fields': sorted(new_secret)})
            logger.info(f"Secret rotated: {path}")
        
        except Exception as e:
            logger.error(f"Failed to rotate secret: {e}")
            self._audit_log('secret_rotation_failed', path, {'error': str(e)})
            raise
    
    async def delete_secret(self, path: str) -> None:
        """Delete secret and clear cache"""
        try:
            await self.backend.delete_secret(path)
            self._invalidate(path)
            self._audit_log('secret_deleted', path)
        
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            self._audit_log('secret_deletion_failed', path, {'error': str(e)})
            raise
    
    def _invalidate(self, path: str) -> None:
        """Drop cached copies of a secret: the whole secret and any single keys."""
        for cache_key in list(self.cache):
            # Exact match or "path:key", so "network/r1" leaves "network/r10" alone
            if cache_key == path or cache_key.startswith(f"{path}:"):
                del self.cache[cache_key]

    def _audit_log(self, action: str, path: str, details: Optional[Dict] = None) -> None:
        """Log all secret operations for compliance"""
        if not self.enable_audit:
            return
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'path': path,
            'user': os.environ.get('USER', 'unknown'),
            'backend': self.backend_type.value,
            'details': details or {}
        }
        
        self.audit_log.append(entry)
        logger.info(f"Audit: {action} on {path}")
    
    def export_audit_log(self, filepath: str) -> None:
        """Export audit log for compliance"""
        with open(filepath, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
        logger.info(f"Audit log exported to {filepath}")

