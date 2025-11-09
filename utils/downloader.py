"""Utility functions for downloading videos from URLs"""
import os
import aiohttp
import asyncio
from urllib.parse import urlparse
from typing import Optional


async def download_video_async(
    url: str, 
    output_dir: str = "output/videos", 
    filename: Optional[str] = None
) -> str:
    """
    Download video from URL asynchronously
    
    Args:
        url: Video URL to download
        output_dir: Directory to save the video
        filename: Optional custom filename
    
    Returns:
        str: Path to downloaded video file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.endswith('.mp4'):
                filename = "video_output.mp4"
        
        output_path = os.path.join(output_dir, filename)
        
        # Download video asynchronously
        print(f"Downloading video to: {output_path}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"\rProgress: {progress:.1f}%", end='')
        
        print(f"\n✓ Video downloaded successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        raise


def download_video(
    url: str, 
    output_dir: str = "output/videos", 
    filename: Optional[str] = None
) -> str:
    """
    Synchronous wrapper for download_video_async
    
    Args:
        url: Video URL to download
        output_dir: Directory to save the video
        filename: Optional custom filename
    
    Returns:
        str: Path to downloaded video file
    """
    import requests
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.endswith('.mp4'):
                filename = "video_output.mp4"
        
        output_path = os.path.join(output_dir, filename)
        
        # Download video
        print(f"Downloading video to: {output_path}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end='')
        
        print(f"\n✓ Video downloaded successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        raise


def get_video_info(file_path: str) -> dict:
    """
    Get basic info about a video file
    
    Args:
        file_path: Path to video file
    
    Returns:
        dict: Video information
    """
    if not os.path.exists(file_path):
        return None
    
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    
    return {
        'path': file_path,
        'size_bytes': file_size,
        'size_mb': round(file_size_mb, 2),
        'filename': os.path.basename(file_path)
    }