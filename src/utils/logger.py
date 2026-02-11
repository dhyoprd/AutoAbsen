import logging
import sys
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output logs as JSON.
    Useful for centralized logging systems (e.g., ELK stack, CloudWatch).
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name: str = "autoabsen", level: str = "INFO", json_format: bool = False) -> logging.Logger:
    """
    Configure strict logging setup.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        formatter = JsonFormatter()
    else:
        # Human readable format for CLI
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
