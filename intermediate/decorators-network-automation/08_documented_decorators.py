def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Retry a function with exponential backoff.
    
    Args:
        max_attempts (int): Maximum number of attempts. Default: 3
        delay (float): Initial delay between retries in seconds. Default: 1
        backoff (float): Multiplier for exponential backoff. Default: 2
        exceptions (tuple): Exception types to catch and retry on. Default: (Exception,)
    
    Raises:
        The last caught exception if all retries fail.
    
    Example:
        @retry(max_attempts=3, delay=2, backoff=1.5)
        def connect_to_device(host):
            return device_connection(host)
    """


import unittest
from unittest.mock import patch, MagicMock

class TestRetryDecorator(unittest.TestCase):
    def test_succeeds_on_first_attempt(self):
        @retry(max_attempts=3)
        def succeeds():
            return "success"
        
        result = succeeds()
        self.assertEqual(result, "success")
    
    def test_retries_on_failure(self):
        attempts = []
        
        @retry(max_attempts=3, delay=0)
        def fails_twice():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("Failed")
            return "success"
        
        result = fails_twice()
        self.assertEqual(result, "success")
        self.assertEqual(len(attempts), 3)
    
    def test_raises_after_max_attempts(self):
        @retry(max_attempts=2, delay=0)
        def always_fails():
            raise ValueError("Always fails")
        
        with self.assertRaises(ValueError):
            always_fails()
