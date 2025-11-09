"""Pipeline state management for tracking video processing progress"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum


class PipelineStage(Enum):
    """Pipeline processing stages"""
    INITIALIZED = "initialized"
    IMAGE_UPLOADED = "image_uploaded"
    VIDEO_GENERATED = "video_generated"
    VIDEO_DOWNLOADED = "video_downloaded"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineState:
    """Manages state for video processing pipeline"""
    
    def __init__(self, state_file: str = "output/pipeline_state.json"):
        """Initialize pipeline state manager"""
        self.state_file = state_file
        self.states: Dict[str, Dict] = {}
        self.load_state()
    
    def load_state(self):
        """Load existing state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.states = json.load(f)
                print(f"✓ Loaded pipeline state from {self.state_file}")
            except Exception as e:
                print(f"Warning: Could not load state file: {e}")
                self.states = {}
        else:
            self.states = {}
    
    def save_state(self):
        """Save current state to file"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.states, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state file: {e}")
    
    def create_job(
        self,
        job_id: str,
        image_path: str,
        config: Dict
    ) -> Dict:
        """
        Create a new pipeline job
        
        Args:
            job_id: Unique identifier for the job
            image_path: Path to input image
            config: Job configuration (duration, ratio, prompt, etc.)
        
        Returns:
            dict: Job state
        """
        job_state = {
            'job_id': job_id,
            'image_path': image_path,
            'config': config,
            'stage': PipelineStage.INITIALIZED.value,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'runware_data': {},
            'errors': []
        }
        
        self.states[job_id] = job_state
        self.save_state()
        return job_state
    
    def update_stage(
        self,
        job_id: str,
        stage: PipelineStage,
        data: Optional[Dict] = None
    ):
        """
        Update job stage and associated data
        
        Args:
            job_id: Job identifier
            stage: New pipeline stage
            data: Additional data to store
        """
        if job_id not in self.states:
            raise ValueError(f"Job {job_id} not found in state")
        
        self.states[job_id]['stage'] = stage.value
        self.states[job_id]['updated_at'] = datetime.now().isoformat()
        
        if data:
            # Store stage-specific data
            if stage in [PipelineStage.IMAGE_UPLOADED, 
                        PipelineStage.VIDEO_GENERATED,
                        PipelineStage.VIDEO_DOWNLOADED]:
                self.states[job_id]['runware_data'].update(data)

        self.save_state()
    
    def add_error(self, job_id: str, error: str):
        """Add error message to job"""
        if job_id in self.states:
            self.states[job_id]['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'message': error
            })
            self.states[job_id]['stage'] = PipelineStage.FAILED.value
            self.save_state()
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job state by ID"""
        return self.states.get(job_id)
    
    def get_jobs_by_stage(self, stage: PipelineStage) -> List[Dict]:
        """Get all jobs at a specific stage"""
        return [
            job for job in self.states.values()
            if job['stage'] == stage.value
        ]
    
    def get_incomplete_jobs(self) -> List[Dict]:
        """Get all jobs that haven't completed"""
        incomplete_stages = [
            PipelineStage.INITIALIZED.value,
            PipelineStage.IMAGE_UPLOADED.value,
            PipelineStage.VIDEO_GENERATED.value,
            PipelineStage.VIDEO_DOWNLOADED.value
        ]
        return [
            job for job in self.states.values()
            if job['stage'] in incomplete_stages
        ]
    
    def mark_completed(self, job_id: str, final_video_path: str):
        """Mark job as completed"""
        if job_id in self.states:
            self.states[job_id]['stage'] = PipelineStage.COMPLETED.value
            self.states[job_id]['final_video_path'] = final_video_path
            self.states[job_id]['completed_at'] = datetime.now().isoformat()
            self.save_state()
    
    def get_summary(self) -> Dict:
        """Get summary of all jobs"""
        summary = {
            'total_jobs': len(self.states),
            'by_stage': {}
        }
        
        for stage in PipelineStage:
            count = len(self.get_jobs_by_stage(stage))
            if count > 0:
                summary['by_stage'][stage.value] = count
        
        return summary