"""
Centralized Logging Configuration and Utilities with Type Safety
Provides structured logging with configurable levels and JSON formatters.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any, Mapping

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if available
        if hasattr(record, 'trace_id') and record.trace_id:
            log_data["trace_id"] = record.trace_id
        
        if hasattr(record, 'user_id') and record.user_id:
            log_data["user_id"] = record.user_id
            
        if hasattr(record, 'method') and record.method:
            log_data["method"] = record.method
            
        if hasattr(record, 'path') and record.path:
            log_data["path"] = record.path
            
        if hasattr(record, 'status') and record.status:
            log_data["status"] = record.status
            
        if hasattr(record, 'latency_ms') and record.latency_ms is not None:
            log_data["latency_ms"] = record.latency_ms
        
        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'trace_id', 'user_id', 'method', 'path', 'status', 'latency_ms']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data)

def setup_logger(
    name: str = "scholarship_api", 
    level: int = logging.INFO,
    use_json: bool = False
) -> logging.Logger:
    """
    Set up and configure the application logger.
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding multiple handlers if logger already exists
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Create formatter
        if use_json:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Add formatter to handler
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"scholarship_api.{name}")

class APILogger:
    """
    Enhanced logger for API operations with structured logging capabilities.
    """
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_request(self, method: str, path: str, user_id: Optional[str] = None, **kwargs):
        """Log API request"""
        extra_info = f" | User: {user_id}" if user_id else ""
        kwargs_str = f" | Params: {kwargs}" if kwargs else ""
        self.logger.info(f"API Request: {method} {path}{extra_info}{kwargs_str}")
    
    def log_response(self, method: str, path: str, status_code: int, 
                    response_time_ms: Optional[float] = None, **kwargs):
        """Log API response"""
        timing_info = f" | {response_time_ms:.2f}ms" if response_time_ms else ""
        kwargs_str = f" | Data: {kwargs}" if kwargs else ""
        self.logger.info(f"API Response: {method} {path} -> {status_code}{timing_info}{kwargs_str}")
    
    def log_error(self, method: str, path: str, error: Exception, user_id: Optional[str] = None):
        """Log API error"""
        user_info = f" | User: {user_id}" if user_id else ""
        self.logger.error(f"API Error: {method} {path}{user_info} | Error: {str(error)}")
    
    def log_business_event(self, event: str, details: Optional[dict] = None):
        """Log business-specific events"""
        details_str = f" | Details: {details}" if details else ""
        self.logger.info(f"Business Event: {event}{details_str}")
    
    def log_performance(self, operation: str, duration_ms: float, **metadata):
        """Log performance metrics"""
        metadata_str = f" | {metadata}" if metadata else ""
        self.logger.info(f"Performance: {operation} took {duration_ms:.2f}ms{metadata_str}")
    
    def log_data_operation(self, operation: str, table: Optional[str] = None, count: Optional[int] = None, **kwargs):
        """Log data operations"""
        table_info = f" on {table}" if table else ""
        count_info = f" | Count: {count}" if count is not None else ""
        kwargs_str = f" | {kwargs}" if kwargs else ""
        self.logger.info(f"Data Operation: {operation}{table_info}{count_info}{kwargs_str}")

# Global logger instances
main_logger = setup_logger()
api_logger = APILogger("api")
