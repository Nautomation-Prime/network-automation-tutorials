# tests/test_decorators.py
import pytest
import time
from unittest.mock import MagicMock, patch
from src.decorators import retry

class TestRetryDecorator:
    """Test retry decorator behaviour."""
    
    def test_succeeds_on_first_attempt(self):
        """Function succeeds immediately—no retries needed."""
        @retry(max_attempts=3)
        def succeeds():
            return "success"
        
        result = succeeds()
        assert result == "success"
    
    def test_retries_on_transient_failure(self):
        """Function fails twice, succeeds on third—should return success."""
        attempts = []
        
        @retry(max_attempts=3, delay=0)  # delay=0 speeds up test
        def fails_twice():
            attempts.append(1)
            if len(attempts) < 3:
                raise ConnectionError("Transient failure")
            return "success"
        
        result = fails_twice()
        
        assert result == "success"
        assert len(attempts) == 3  # Verify it actually retried
    
    def test_raises_after_max_attempts(self):
        """After max attempts, exception should be raised."""
        @retry(max_attempts=2, delay=0)
        def always_fails():
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError, match="Persistent failure"):
            always_fails()
    
    def test_exponential_backoff(self):
        """Verify backoff multiplier is applied correctly."""
        attempts = []
        
        @retry(max_attempts=3, delay=0, backoff=2)
        def fails_twice():
            attempts.append(time.time() if attempts else 0)
            if len(attempts) < 3:
                raise ConnectionError()
            return "success"
        
        # For precise timing tests, use @patch to mock time.sleep
        with patch('time.sleep') as mock_sleep:
            @retry(max_attempts=3, delay=1, backoff=2)
            def fails_twice_with_sleep():
                if mock_sleep.call_count < 2:
                    raise ConnectionError()
                return "success"
            
            fails_twice_with_sleep()
            
            # Verify sleep called with correct delays: 1s, then 2s
            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0][0][0] == 1  # First delay
            assert mock_sleep.call_args_list[1][0][0] == 2  # Second delay
    
    def test_catches_only_specified_exceptions(self):
        """Retry only catches specified exceptions, not others."""
        @retry(max_attempts=3, exceptions=(ConnectionError,))
        def raises_value_error():
            raise ValueError("Not caught by retry")
        
        with pytest.raises(ValueError):
            raises_value_error()
    
    def test_preserves_function_metadata(self):
        """@retry should preserve original function name and docstring."""
        @retry()
        def my_function():
            """My docstring."""
            pass
        
        assert my_function.__name__ == "my_function"
        assert "docstring" in my_function.__doc__
