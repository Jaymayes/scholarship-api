"""
ETag Generation and Validation Utilities
CEO v2.3 Section 3.2 Requirement: ETag support for caching
"""

import hashlib
import json
from typing import Any


def generate_etag(data: Any) -> str:
    """
    Generate an ETag from response data using SHA-256 hash.
    
    Args:
        data: Response data (dict, list, or Pydantic model)
        
    Returns:
        ETag value as a quoted string (e.g., "abc123...")
    """
    if hasattr(data, 'model_dump'):
        json_str = json.dumps(data.model_dump(), sort_keys=True, default=str)
    elif hasattr(data, 'dict'):
        json_str = json.dumps(data.dict(), sort_keys=True, default=str)
    elif isinstance(data, (dict, list)):
        json_str = json.dumps(data, sort_keys=True, default=str)
    else:
        json_str = str(data)
    
    hash_value = hashlib.sha256(json_str.encode()).hexdigest()[:16]
    return f'"{hash_value}"'


def etag_matches(etag: str, if_none_match: str | None) -> bool:
    """
    Check if ETag matches If-None-Match header value.
    
    Args:
        etag: Current ETag value
        if_none_match: If-None-Match header from request
        
    Returns:
        True if ETags match (304 should be returned), False otherwise
    """
    if not if_none_match:
        return False
    
    if if_none_match == "*":
        return True
    
    provided_etags = [tag.strip() for tag in if_none_match.split(',')]
    return etag in provided_etags
