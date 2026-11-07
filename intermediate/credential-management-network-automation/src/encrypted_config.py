# src/encrypted_config.py
from cryptography.fernet import Fernet
import json
import os

class EncryptedConfig:
    """Store credentials in encrypted YAML/JSON files."""
    
    def __init__(self, encryption_key=None):
        """
        Initialize with encryption key.
        
        Args:
            encryption_key: Fernet key (default: read from env var)
        """
        self.encryption_key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        
        self.cipher = Fernet(self.encryption_key.encode())
    
    def encrypt_credentials(self, credentials_dict, output_file):
        """
        Encrypt and save credentials.
        
        Args:
            credentials_dict: Dict with credentials
            output_file: File to save encrypted data
        """
        json_str = json.dumps(credentials_dict)
        encrypted = self.cipher.encrypt(json_str.encode())
        
        with open(output_file, 'wb') as f:
            f.write(encrypted)
        
        # Never commit encrypted file with sensitive data
        print(f"✓ Encrypted credentials saved to {output_file}")
    
    def decrypt_credentials(self, encrypted_file):
        """
        Decrypt and load credentials.
        
        Args:
            encrypted_file: File with encrypted credentials
        
        Returns:
            dict: Decrypted credentials
        """
        with open(encrypted_file, 'rb') as f:
            encrypted = f.read()
        
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
