# src/elasticsearch_logger.py
import json
import logging
from datetime import datetime, timezone
from elasticsearch import Elasticsearch
from structured_logger import StructuredLogger

class ElasticsearchHandler(logging.Handler):
    """Send logs to Elasticsearch."""
    
    def __init__(self, hosts: list, index_name: str = "network-automation"):
        """
        Initialize Elasticsearch handler.
        
        Args:
            hosts: Elasticsearch URLs, scheme included (e.g., ["http://localhost:9200"])
            index_name: Index name for logs
        """
        super().__init__()
        self.es = Elasticsearch(hosts=hosts)
        self.index_name = index_name
    
    def emit(self, record):
        """Send log record to Elasticsearch."""
        try:
            log_data = json.loads(self.format(record))
            
            # Add timestamp for Elasticsearch
            log_data["@timestamp"] = log_data.get("timestamp", datetime.now(timezone.utc).isoformat())
            
            # Send to Elasticsearch
            self.es.index(
                index=f"{self.index_name}-{datetime.now(timezone.utc):%Y.%m.%d}",
                document=log_data
            )
        except Exception as e:
            self.handleError(record)
