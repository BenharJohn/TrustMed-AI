"""
Simple utilities
Extracted minimal functions needed by other modules
"""

import uuid


def str_uuid():
    """Generate a unique ID string"""
    return str(uuid.uuid4())
