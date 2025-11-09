"""File management utilities for the pipeline"""
import os
import shutil
from typing import List, Optional
from pathlib import Path


class FileManager:
    """Handles file operations for the pipeline"""
    
    @staticmethod
    def validate_image(file_path: str, supported_formats: List[str]) -> bool:
        """
        Validate if file is a supported image format
        
        Args:
            file_path: Path to image file
            supported_formats: List of supported extensions
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        ext = Path(file_path).suffix.lower()
        return ext in supported_formats
    
    @staticmethod
    def get_file_size(file_path: str) -> dict:
        """
        Get file size information
        
        Args:
            file_path: Path to file
        
        Returns:
            dict: Size information
        """
        if not os.path.exists(file_path):
            return None
        
        size_bytes = os.path.getsize(file_path)
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        size_gb = size_mb / 1024
        
        return {
            'bytes': size_bytes,
            'kb': round(size_kb, 2),
            'mb': round(size_mb, 2),
            'gb': round(size_gb, 2)
        }
    
    @staticmethod
    def create_directory(directory: str) -> bool:
        """
        Create directory if it doesn't exist
        
        Args:
            directory: Directory path
        
        Returns:
            bool: True if created or exists
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
    
    @staticmethod
    def list_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        List files in directory, optionally filtered by extension
        
        Args:
            directory: Directory to scan
            extensions: Optional list of extensions to filter
        
        Returns:
            List of file paths
        """
        if not os.path.exists(directory):
            return []
        
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                if extensions is None:
                    files.append(item_path)
                else:
                    ext = Path(item_path).suffix.lower()
                    if ext in extensions:
                        files.append(item_path)
        
        return sorted(files)
    
    @staticmethod
    def copy_file(source: str, destination: str) -> bool:
        """
        Copy file from source to destination
        
        Args:
            source: Source file path
            destination: Destination file path
        
        Returns:
            bool: True if successful
        """
        try:
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            os.makedirs(dest_dir, exist_ok=True)
            
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            print(f"Error copying file: {e}")
            return False
    
    @staticmethod
    def move_file(source: str, destination: str) -> bool:
        """
        Move file from source to destination
        
        Args:
            source: Source file path
            destination: Destination file path
        
        Returns:
            bool: True if successful
        """
        try:
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(source, destination)
            return True
        except Exception as e:
            print(f"Error moving file: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to file
        
        Returns:
            bool: True if successful
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str) -> int:
        """
        Clean up temporary files
        
        Args:
            temp_dir: Temporary directory path
        
        Returns:
            int: Number of files deleted
        """
        if not os.path.exists(temp_dir):
            return 0
        
        count = 0
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    count += 1
            except Exception as e:
                print(f"Error deleting {item_path}: {e}")
        
        return count
    
    @staticmethod
    def generate_unique_filename(base_name: str, directory: str, extension: str) -> str:
        """
        Generate a unique filename by appending numbers if file exists
        
        Args:
            base_name: Base filename without extension
            directory: Target directory
            extension: File extension (with or without dot)
        
        Returns:
            str: Unique filename
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        filename = f"{base_name}{extension}"
        full_path = os.path.join(directory, filename)
        
        counter = 1
        while os.path.exists(full_path):
            filename = f"{base_name}_{counter}{extension}"
            full_path = os.path.join(directory, filename)
            counter += 1
        
        return filename