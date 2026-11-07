#!/usr/bin/env python3
"""
Process large JSON files efficiently
Use streaming for memory-efficient parsing
"""

import json
import ijson  # pip install ijson

def process_large_json_standard(filename):
    """
    Standard approach: Load entire file into memory
    Works for small files, fails for large files (>1GB)
    """
    with open(filename) as f:
        data = json.load(f)  # Loads entire file into memory

    # Process data
    for item in data:
        process_item(item)

def process_large_json_streaming(filename):
    """
    Streaming approach: Process items one at a time
    Memory-efficient for large files
    """
    with open(filename, 'rb') as f:
        # Parse items incrementally
        items = ijson.items(f, 'item')  # Assumes JSON array

        for item in items:
            # Process one item at a time
            process_item(item)
            # Previous items are garbage collected

def process_item(item):
    """Process a single JSON item"""
    # Your processing logic here
    pass

# Example: Process 10GB JSON file with streaming
# process_large_json_streaming('huge_inventory.json')
