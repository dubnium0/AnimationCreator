import os
import json
import sys
import time
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips
from PIL import Image
import requests
from io import BytesIO
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv



# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class VideoGenerator:
    """Unified video generator class for all video generation methods"""
    
    def __init__(self, openai_api_key=None):
        """
        Initialize the video generator with API keys.
        
        Args:
            openai_api_key (str): OpenAI API key
        """
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        
        # Initialize OpenAI client if key is provided
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

class ImageBasedVideoGenerator(VideoGenerator):
    """Image-based video generator using OpenAI DALL-E + TTS"""
    
    def generate_tts_openai(self, text, output_file, voice="alloy"):
        """
        Converts text to audio file using OpenAI TTS API.
        
        Args:
            text (str): Text to convert
            output_file (str): Output audio file path
            voice (str): Voice model (alloy, echo, fable, onyx, nova, shimmer)
        """
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not initialized")
                
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            response.stream_to_file(output_file)
            print(f"Audio created with OpenAI TTS: {output_file}")
            return True
        except Exception as e:
            print(f"OpenAI TTS error: {str(e)}")
            return False

    def generate_image_with_openai(self, prompt, output_file, image_size="1024x1792"):
        """
        Creates image using OpenAI DALL-E API.
        
        Args:
            prompt (str): Image generation prompt
            output_file (str): Output image file path
            image_size (str): Image size (1024x1024, 1024x1792, 1792x1024)
        """
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not initialized")
                
            # General prompt enhancement
            enhanced_prompt = f"""
            Create a high-quality, engaging illustration for this scene:
            {prompt}
            
            The image should be:
            - Visually appealing and professional
            - Clear and easy to understand
            - Colorful and engaging
            - Detailed but not cluttered
            - Consistent with the overall story style
            """
            
            # Send request to OpenAI DALL-E API
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=image_size,
                quality="standard",
                n=1
            )
            
            # Get image URL
            image_url = response.data[0].url
            
            # Download and save image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(image_response.content)
                print(f"Image successfully created: {output_file}")
                return True
            else:
                print("Image could not be downloaded")
                return False
                
        except Exception as e:
            print(f"Image creation error: {str(e)}")
            return False

    def create_scene(self, scene_data, scene_number, output_dir, story_context=None, voice="alloy", platform_specs=None):
        """
        Creates a single scene using OpenAI DALL-E + TTS.
        
        Args:
            scene_data (dict): Scene data
            scene_number (int): Scene number
            output_dir (str): Output directory
            story_context (dict): Story context
            voice (str): Voice for TTS
            platform_specs (dict): Platform specifications with width, height, etc.
        
        Returns:
            tuple: (video_clip, duration)
        """
        # File paths
        image_file = os.path.join(output_dir, f"scene_{scene_number}.png")
        audio_file = os.path.join(output_dir, f"scene_{scene_number}.wav")
        
        # Determine image size based on platform specs
        image_size = "1024x1792"  # Default
        if platform_specs:
            width = platform_specs.get('width', 1024)
            height = platform_specs.get('height', 1792)
            
            # Map to supported DALL-E sizes
            if width == height:  # Square
                image_size = "1024x1024"
            elif width > height:  # Landscape
                image_size = "1792x1024"
            else:  # Portrait
                image_size = "1024x1792"
        
        # Create image
        if not self.generate_image_with_openai(scene_data["image_prompt"], image_file, image_size):
            return None, 0
        
        # Create audio
        if not self.generate_tts_openai(scene_data["narration"], audio_file, voice):
            return None, 0
        
        try:
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_file)
            duration = audio_clip.duration
            
            # Create image clip with audio duration
            image_clip = ImageClip(image_file, duration=duration)
            
            # Resize image to match platform specs
            if platform_specs:
                target_width = platform_specs.get('width', 1080)
                target_height = platform_specs.get('height', 1920)
                # Use newsize parameter to avoid PIL.Image.ANTIALIAS deprecation
                image_clip = image_clip.resize(newsize=(target_width, target_height))
            
            # Combine image and audio
            video_clip = image_clip.set_audio(audio_clip)
            
            return video_clip, duration
            
        except Exception as e:
            print(f"Scene creation error: {str(e)}")
            return None, 0

    def process_story_to_video(self, story_file, output_dir, voice="alloy", platform_specs=None):
        """
        Process entire story JSON file into a video.
        
        Args:
            story_file (str): Path to story JSON file
            output_dir (str): Output directory
            voice (str): Voice for TTS
            platform_specs (dict): Platform specifications
        
        Returns:
            tuple: (final_video_path, success_status)
        """
        try:
            # Read story data
            with open(story_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Process each scene
            video_clips = []
            for i, scene in enumerate(story_data['scenes'], 1):
                print(f"Processing scene {i}/{len(story_data['scenes'])}...")
                
                video_clip, duration = self.create_scene(scene, i, output_dir, story_data, voice, platform_specs)
                
                if video_clip:
                    video_clips.append(video_clip)
                else:
                    print(f"Failed to create scene {i}")
            
            if video_clips:
                # Combine all clips
                final_video = concatenate_videoclips(video_clips)
                
                # Save final video
                safe_title = "".join(c for c in story_data['story_title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_file = os.path.join(output_dir, f"{safe_title.replace(' ', '_')}_image_based.mp4")
                final_video.write_videofile(output_file, fps=24, verbose=False, logger=None)
                
                # Clean up
                for clip in video_clips:
                    clip.close()
                final_video.close()
                
                print(f"Final video created: {output_file}")
                return output_file, True
            else:
                print("No video clips were created")
                return None, False
                
        except Exception as e:
            print(f"Error processing story to video: {str(e)}")
            return None, False







# Factory function to create appropriate generator
def create_video_generator(method, openai_api_key=None, gemini_api_key=None):
    """
    Factory function to create the appropriate video generator.
    
    Args:
        method (str): Video generation method ('image_based')
        openai_api_key (str): OpenAI API key
        gemini_api_key (str): Google Gemini API key
    
    Returns:
        VideoGenerator: Appropriate generator instance
    """
    if method == 'image_based':
        return ImageBasedVideoGenerator(openai_api_key, gemini_api_key)


    else:
        raise ValueError(f"Unknown video generation method: {method}")

# Model information functions
def get_model_info(method):
    """
    Get information about a specific video generation method.
    
    Args:
        method (str): Video generation method
    
    Returns:
        dict: Model information
    """
    model_info = {
        'image_based': {
            "model_name": "Image-Based (OpenAI DALL-E + TTS)",
            "description": "Creates videos from generated images and audio",
            "features": [
                "High-quality image generation",
                "Natural voice synthesis",
                "Platform-specific optimization",
                "Multiple voice options"
            ],
            "requirements": ["OpenAI API key"],
            "status": "Fully implemented"
        },



    }
    
    return model_info.get(method, {"error": "Unknown method"})

# Convenience functions for backward compatibility
def process_story_to_videos_image_based(openai_api_key, story_file, output_dir, voice="alloy", platform_specs=None):
    """Backward compatibility function for image-based video generation"""
    generator = ImageBasedVideoGenerator(openai_api_key)
    return generator.process_story_to_video(story_file, output_dir, voice, platform_specs)







# Streamlit UI Video Generation Functions
def generate_video_ui(story_file, voice, platform_specs, openai_key, progress_callback=None, status_callback=None):
    """
    Generate video with Streamlit UI integration using unified generator
    
    Args:
        story_file (str): Path to story JSON file
        voice (str): Voice for TTS
        platform_specs (dict): Platform specifications
        openai_key (str): OpenAI API key
        progress_callback: Function to update progress
        status_callback: Function to update status text
    
    Returns:
        tuple: (final_video_path, success_status, story_data)
    """
    try:
        # Read story data
        with open(story_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        total_scenes = len(story_data['scenes'])
        if status_callback:
            status_callback(f"🎬 Video oluşturuluyor... ({total_scenes} sahne)")
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        if progress_callback:
            progress_callback(20)
        if status_callback:
            status_callback("🚀 Unified generator ile video işlemi başlatılıyor...")
        
        # Process story to video using unified generator
        final_video_path, success = process_story_to_videos_image_based(
            openai_key, story_file, output_dir, voice, platform_specs
        )
        
        if success and final_video_path and os.path.exists(final_video_path):
            if progress_callback:
                progress_callback(100)
            if status_callback:
                status_callback("✅ Video başarıyla oluşturuldu!")
            return final_video_path, True, story_data
        else:
            return None, False, story_data
            
    except Exception as e:
        print(f"Video generation error: {str(e)}")
        return None, False, None