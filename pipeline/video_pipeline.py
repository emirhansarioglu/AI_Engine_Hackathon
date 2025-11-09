"""Main video pipeline orchestrator for Runware + Mirelo integration"""
import asyncio
import os
from typing import Dict, Optional
from datetime import datetime
import uuid

# Import services (will be created)
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from pipeline.pipeline_state import PipelineState, PipelineStage
from utils.downloader import download_video
from utils.file_manager import FileManager
from utils.logger import PipelineLogger


class VideoPipeline:
    """Orchestrates the complete video generation pipeline"""
    
    def __init__(self):
        """Initialize pipeline with services and state management"""
        Config.validate()
        
        self.state_manager = PipelineState(Config.STATE_FILE)
        self.file_manager = FileManager()
        self.logger = PipelineLogger(Config.LOG_FILE, Config.LOG_LEVEL)
        
        # Services will be initialized when needed
        self.runware_service = None
        self.mirelo_service = None
    
    async def _init_runware_service(self):
        """Initialize Runware service"""
        if self.runware_service is None:
            from services.runware_service import RunwareVideoGenerator
            self.runware_service = RunwareVideoGenerator()
            await self.runware_service.connect()
    
    async def process_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        duration: int = None,
        ratio: str = None,
        job_id: Optional[str] = None
    ) -> Dict:
        """
        Complete pipeline: Image -> Video -> Video with Audio
        
        Args:
            image_path: Path to input image
            prompt: Video generation prompt
            duration: Video duration in seconds
            ratio: Aspect ratio
            voice_config: Configuration for voice generation (for Mirelo)
            job_id: Optional job ID (will be generated if not provided)
        
        Returns:
            dict: Complete pipeline results
        """
        # Generate job ID if not provided
        if job_id is None:
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Use defaults if not specified
        duration = duration or Config.DEFAULT_DURATION
        ratio = ratio or Config.DEFAULT_RATIO
        prompt = prompt or Config.DEFAULT_PROMPT
        
        # Create job in state manager
        config = {
            'prompt': prompt,
            'duration': duration,
            'ratio': ratio
        }
        
        self.state_manager.create_job(job_id, image_path, config)
        self.logger.info(f"Starting pipeline for job: {job_id}")
        
        try:
            # ========================================
            # STEP 1: Generate Video with Runware
            # ========================================
            self.logger.info(f"[{job_id}] Step 1: Generating video from image")
            video_result = await self._generate_video_runware(
                job_id, image_path, prompt, duration, ratio
            )
            
            if not video_result['success']:
                raise Exception(f"Runware video generation failed: {video_result.get('error')}")
            
            # ========================================
            # STEP 2: Download Video (optional but recommended)
            # ========================================
            if Config.AUTO_DOWNLOAD_VIDEOS:
                self.logger.info(f"[{job_id}] Step 2: Downloading video")
                final_video_path = await self._download_video(
                    job_id,
                    video_result['video_url'],
                    Config.VIDEOS_DIR
                )
            else:
                final_video_path = video_result['video_url']
            
           
            self.state_manager.mark_completed(job_id, final_video_path)
            
            # ========================================
            # Complete
            # ========================================
            self.logger.info(f"[{job_id}] Pipeline completed successfully")
            
            return {
                'success': True,
                'job_id': job_id,
                'stages': {
                    'runware': video_result,
                    'video_path': final_video_path
                },
                'final_video_path': final_video_path
            }
            
        except Exception as e:
            self.logger.error(f"[{job_id}] Pipeline failed: {str(e)}")
            self.state_manager.add_error(job_id, str(e))
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e)
            }
    
    async def _generate_video_runware(
        self,
        job_id: str,
        image_path: str,
        prompt: str,
        duration: int,
        ratio: str
    ) -> Dict:
        """Step 1: Generate video using Runware"""
        try:
            await self._init_runware_service()
            
            # Upload image
            self.state_manager.update_stage(
                job_id,
                PipelineStage.IMAGE_UPLOADED,
                {'image_path': image_path}
            )
            
            # Generate video
            result = await self.runware_service.image_to_video(
                image_path=image_path,
                prompt=prompt,
                duration=duration,
                ratio=ratio
            )
            
            if result['success']:
                self.state_manager.update_stage(
                    job_id,
                    PipelineStage.VIDEO_GENERATED,
                    {
                        'video_url': result['video_url'],
                        'duration': duration,
                        'ratio': ratio
                    }
                )
            
            return result
            
        except Exception as e:
            raise Exception(f"Runware generation error: {str(e)}")
    
    async def _download_video(
        self,
        job_id: str,
        video_url: str,
        output_dir: str
    ) -> str:
        """Step 2: Download video from URL"""
        try:
            filename = f"{job_id}_runware.mp4"
            video_path = await asyncio.to_thread(
                download_video,
                video_url,
                output_dir,
                filename
            )
            
            if video_path:
                self.state_manager.update_stage(
                    job_id,
                    PipelineStage.VIDEO_DOWNLOADED,
                    {'local_video_path': video_path}
                )
            
            return video_path
            
        except Exception as e:
            raise Exception(f"Video download error: {str(e)}")
    
    
    async def cleanup(self):
        """Cleanup resources and close connections"""
        if self.runware_service:
            await self.runware_service.close()
        
        self.logger.info("Pipeline cleanup completed")
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a specific job"""
        return self.state_manager.get_job(job_id)
    
    def get_pipeline_summary(self) -> Dict:
        """Get summary of all pipeline jobs"""
        return self.state_manager.get_summary()