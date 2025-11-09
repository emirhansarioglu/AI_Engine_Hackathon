"""Logging utilities for the pipeline"""
import logging
import os
from datetime import datetime
from typing import Optional


class PipelineLogger:
    """Custom logger for video pipeline"""
    
    def __init__(self, log_file: str = "output/pipeline.log", level: str = "INFO"):
        """
        Initialize pipeline logger
        
        Args:
            log_file: Path to log file
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_file = log_file
        self.level = getattr(logging, level.upper(), logging.INFO)
        
        # Create log directory if needed
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('VideoPipeline')
        self.logger.setLevel(self.level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def log_stage(self, job_id: str, stage: str, status: str = "started"):
        """
        Log pipeline stage progress
        
        Args:
            job_id: Job identifier
            stage: Pipeline stage name
            status: Status (started, completed, failed)
        """
        message = f"[{job_id}] Stage '{stage}' - {status}"
        if status == "failed":
            self.error(message)
        else:
            self.info(message)
    
    def log_metrics(self, job_id: str, metrics: dict):
        """
        Log performance metrics
        
        Args:
            job_id: Job identifier
            metrics: Dictionary of metrics
        """
        metrics_str = ", ".join([f"{k}={v}" for k, v in metrics.items()])
        self.info(f"[{job_id}] Metrics: {metrics_str}")
    
    def log_api_call(self, service: str, endpoint: str, status: str):
        """
        Log API calls
        
        Args:
            service: Service name (Runware, Mirelo)
            endpoint: API endpoint
            status: Response status
        """
        self.info(f"API Call - {service}.{endpoint} - Status: {status}")