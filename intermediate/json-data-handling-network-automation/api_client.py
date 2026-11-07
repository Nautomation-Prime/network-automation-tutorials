#!/usr/bin/env python3
"""
Complete REST API client with JSON handling
Demonstrates best practices for network automation
"""

import json
import requests
import logging
from datetime import datetime, timezone
import time

# Configure logging with JSON formatter
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class NetworkAPIClient:
    """
    REST API client for network device management
    """

    def __init__(self, config_file='config.json'):
        """Initialize client with configuration from JSON file"""
        # Load configuration
        with open(config_file) as f:
            self.config = json.load(f)

        self.base_url = self.config['api']['base_url']
        self.timeout = self.config['api']['timeout']
        self.retry_attempts = self.config['api']['retry_attempts']
        self.api_key = self.config['credentials']['api_key']

        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })

    def _make_request(self, method, endpoint, **kwargs):
        """
        Make HTTP request with retry logic
        """
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                logger.error(json.dumps({
                    'event': 'http_error',
                    'status_code': e.response.status_code,
                    'url': url,
                    'attempt': attempt + 1
                }))

                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

            except requests.exceptions.RequestException as e:
                logger.error(json.dumps({
                    'event': 'request_error',
                    'error': str(e),
                    'url': url,
                    'attempt': attempt + 1
                }))

                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def get_device_info(self, device_name):
        """Get device information from API"""
        logger.info(json.dumps({
            'event': 'get_device_info',
            'device': device_name,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }))

        data = self._make_request('GET', f'devices/{device_name}')
        return data

    def update_device_config(self, device_name, config):
        """Update device configuration via API"""
        logger.info(json.dumps({
            'event': 'update_device_config',
            'device': device_name,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }))

        # Prepare JSON payload
        payload = {
            'device': device_name,
            'config': config,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        data = self._make_request(
            'PUT',
            f'devices/{device_name}/config',
            json=payload
        )

        return data

def main():
    """Main function"""
    # Initialize API client
    client = NetworkAPIClient('config.json')

    # Process devices from config
    for device in client.config['devices']:
        try:
            # Get device info
            info = client.get_device_info(device['name'])

            logger.info(json.dumps({
                'event': 'device_info_retrieved',
                'device': device['name'],
                'status': 'success'
            }))

        except Exception as e:
            logger.error(json.dumps({
                'event': 'device_info_failed',
                'device': device['name'],
                'error': str(e)
            }))

if __name__ == "__main__":
    main()
