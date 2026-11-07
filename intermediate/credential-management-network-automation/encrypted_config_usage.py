# Generate encryption key (do this ONCE and save securely)
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Save this somewhere secure
# Set as: export ENCRYPTION_KEY="<key>"

# Encrypt credentials
from src.encrypted_config import EncryptedConfig
config = EncryptedConfig()
config.encrypt_credentials(
    {
        "router1": {"username": "admin", "password": "SecurePass123!"},
        "router2": {"username": "admin", "password": "SecurePass456!"}
    },
    "credentials.enc"
)

# Load encrypted credentials
creds = config.decrypt_credentials("credentials.enc")
