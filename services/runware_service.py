import requests
import os
import uuid
import base64
import time
import os
import asyncio
from runware import Runware, IVideoInference
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RunwareVideoGenerator:
    def __init__(self, api_key: str = None):
        """Initialize Runware client with API key"""
        self.api_key = api_key or os.getenv("RUNWARE_API_KEY")
        if not self.api_key:
            raise ValueError("RUNWARE_API_KEY not found in environment variables")
        
        self.runware = Runware(api_key=self.api_key)
    
    async def connect(self):
        """Establish connection to Runware"""
        await self.runware.connect()
        print("✓ Connected to Runware")
    
    async def image_to_video(
        self,
        image_path: str,
        prompt: str = None,
        duration: int = 5,
        ratio: str = "16:9",
        output_path: str = "output"
    ) -> dict:
        """
        Convert an image to a video
        
        Args:
            image_path: Path to the input image file
            prompt: Optional text prompt to guide video generation
            duration: Video duration in seconds (default: 5)
            ratio: Aspect ratio (default: "16:9")
            output_path: Directory to save output video
        
        Returns:
            dict: Response with video URL and details
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Upload image first
        print(f"Uploading image: {image_path}")
        image_uuid = upload_image_to_runware(image_path)
        print(f"✓ Image uploaded: {image_uuid}")  
        url = "https://api.runware.ai/v1"  # Confirm if this is the correct endpoint
        headers = {
            "Authorization": f"Bearer {os.getenv('RUNWARE_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        video_request = [
            {
                "taskType": "videoInference",
                "taskUUID": str(uuid.uuid4()),
                "model": "bytedance:2@2",
                "positivePrompt": "smooth animation, natural movement, cartoonish style",
                "duration": 5,
                "width": 1440,
                "height": 1440,
                "frameImages": [      
                    {
                        "inputImage": image_uuid,
                        "frame": "first"
                    }
                ],
                "numberResults": 1,
                "outputType": "URL",
                "outputFormat": "MP4",
                "deliveryMethod": "async"
            }
        ]

        video_response = requests.post(url, headers=headers, json=video_request)
        data = video_response.json()
        task_uuid = data["data"][0]["taskUUID"]
        print(f"Generating video (duration: {duration}s)...")

        # Poll the status endpoint periodically
        status_url = f"https://api.runware.ai/v1/tasks/{task_uuid}"
        while True:
            status_request = [
                {
                    "taskType": "getResponse",
                    "taskUUID": task_uuid
                }
            ]
            status_response = requests.post(url, headers=headers, json=status_request)
            status_response.raise_for_status()

            status_data = status_response.json()

            task_data = status_data["data"][0]
            status = task_data["status"]

            if status == "success":
                video_url = task_data["videoURL"]
                print(f"✅ Video ready at: {video_url}")
                break
            elif status in ["failed", "error"]:
                print(f"❌ Task failed: {status_data}")
                break
            else:
                print(f"⌛ Status: {status}... waiting for completion")
                time.sleep(5)  # Wait before checking again

        return {
            'success': True,
            'video_url': video_url,
            'image_uuid': image_uuid,
            'duration': duration,
            'ratio': ratio
        }
        
    
    async def close(self):
        """Close Runware connection"""
        await self.runware.disconnect()
        print("✓ Connection closed")


async def main():
    """Main execution function"""
    try:
        # Initialize generator
        generator = RunwareVideoGenerator()
        
        # Connect to Runware
        await generator.connect()
        
        # Example: Generate video from image
        result = await generator.image_to_video(
            image_path="input/sample_image.jpg",
            prompt="smooth camera movement, cinematic",
            duration=5,
            ratio="16:9",
            output_path="output"
        )
        
        if result['success']:
            print("\n=== Video Generation Complete ===")
            print(f"Video URL: {result['video_url']}")
            print(f"Duration: {result['duration']}s")
            print(f"Ratio: {result['ratio']}")
        else:
            print(f"Error: {result.get('error')}")
        
        # Close connection
        await generator.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())

def generate_video_from_image(image_id: str) -> str:
    """
    Sends a video inference request to Runware API using an uploaded image ID.
    Returns the video URL or task result.
    """
    url = "https://api.runware.ai/v1"  # or the exact endpoint for video inference
    headers = {
        "Authorization": f"Bearer {os.getenv('RUNWARE_API_KEY')}",
        "Content-Type": "application/json"
    }

    task = {
        "taskType": "videoInference",
        "taskUUID": str(uuid.uuid4()),
        "positivePrompt": "smooth animation, natural movement, cinematic quality",
        "model": "klingai:3@2",
        "duration": 10,
        "width": 1920,
        "height": 1080,
        "frameImages": [
            {
                "inputImage": image_id,
                "frame": "first"
            }
        ],
        "numberResults": 1
    }

    payload = [task]  # API expects an array
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    # Adjust this depending on Runware's response structure
    return result

def upload_image_to_runware(image_path: str) -> str:
    """
    Uploads an image to the Runware API and returns the imageUUID
    to be used in later video inference requests.
    """
    url = "https://api.runware.ai/v1/tasks"  # Confirm if this is the correct endpoint
    headers = {
        "Authorization": f"Bearer {os.getenv('RUNWARE_API_KEY')}",
        "Content-Type": "application/json"
    }

    # Read and Base64-encode the image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    # Create the request object (list of one task)
    request_object = [
        {
            "taskType": "imageUpload",
            "taskUUID": str(uuid.uuid4()),  # generate a random unique ID
            "image": f"data:image/png;base64,{image_b64}"
        }
    ]

    # Send the POST request
    response = requests.post(url, headers=headers, json=request_object)
    response.raise_for_status()

    # Parse the response JSON
    data = response.json()
    # ✅ Extract imageUUID from the response
    # Expected format:
    # {
    #   "data": {
    #       "taskType": "imageUpload",
    #       "taskUUID": "...",
    #       "imageUUID": "..."
    #   }
    # }
    image_uuid = data["data"][0]["imageUUID"]
    return image_uuid