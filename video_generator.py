import os
import json
import sys
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image
import requests
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_tts_openai(text, output_file, voice="alloy"):
    """
    Converts text to audio file using OpenAI TTS API.
    
    Args:
        text (str): Text to convert
        output_file (str): Output audio file path
        voice (str): Voice model (alloy, echo, fable, onyx, nova, shimmer)
    """
    try:
        response = client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice=voice,
            input=text
        )
        
        response.stream_to_file(output_file)
        print(f"Audio created with OpenAI TTS: {output_file}")
        return True
    except Exception as e:
        print(f"OpenAI TTS error: {str(e)}")
        return False

def generate_image_with_openai(prompt, output_file):
    """
    Creates image using OpenAI DALL-E API.
    
    Args:
        prompt (str): Image generation prompt
        output_file (str): Output image file path
    """
    try:
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
        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1024x1024",
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

def create_scene(scene_data, scene_number, output_dir, story_context=None):
    """
    Creates a single scene.
    
    Args:
        scene_data (dict): Scene data
        scene_number (int): Scene number
        output_dir (str): Output directory
        story_context (dict): Story context
    
    Returns:
        tuple: (video_clip, duration)
    """
    # File paths
    image_file = os.path.join(output_dir, f"scene_{scene_number}.png")
    audio_file = os.path.join(output_dir, f"scene_{scene_number}.wav")
    
    # Create image
    if not generate_image_with_openai(scene_data["image_prompt"], image_file):
        return None, 0
    
    # Create audio (use default voice)
    if not generate_tts_openai(scene_data["narration"], audio_file, "alloy"):
        return None, 0
    
    # Create video clip
    try:
        image_clip = ImageClip(image_file)
        audio_clip = AudioFileClip(audio_file)
        
        # Set image duration to audio duration
        video_clip = image_clip.set_duration(audio_clip.duration)
        video_clip = video_clip.set_audio(audio_clip)
        
        return video_clip, audio_clip.duration
    except Exception as e:
        print(f"Scene creation error: {str(e)}")
        return None, 0

def create_video(story_file, output_dir="output"):
    """
    Converts story to video.
    
    Args:
        story_file (str): Story JSON file
        output_dir (str): Output directory
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read story data
    try:
        with open(story_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {story_file} file not found!")
        return
    except json.JSONDecodeError:
        print(f"Error: {story_file} is not a valid JSON file!")
        return
    
    # Check required fields
    required_fields = ['story_title', 'scenes']
    for field in required_fields:
        if field not in story_data:
            print(f"Error: '{field}' field not found in JSON file!")
            return
    
    print(f"Creating story: {story_data['story_title']}")
    print(f"Total number of scenes: {len(story_data['scenes'])}")
    
    # Create video clips for each scene
    video_clips = []
    total_duration = 0
    
    for i, scene in enumerate(story_data["scenes"], 1):
        print(f"\nCreating scene {i}/{len(story_data['scenes'])}...")
        print(f"Scene description: {scene['narration'][:50]}...")
        
        video_clip, duration = create_scene(scene, scene.get("scene_number", i), output_dir, story_data)
        if video_clip:
            video_clips.append(video_clip)
            total_duration += duration
            print(f"Scene {i} successfully created ({duration:.1f} seconds)")
        else:
            print(f"Scene {i} could not be created!")
    
    if not video_clips:
        print("No video clips could be created!")
        return
    
    print(f"\n{len(video_clips)} scenes successfully created. Combining video...")
    
    # Combine all clips
    final_video = concatenate_videoclips(video_clips)
    
    # Save video
    safe_title = "".join(c for c in story_data['story_title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    output_file = os.path.join(output_dir, f"{safe_title.replace(' ', '_')}.mp4")
    final_video.write_videofile(output_file, fps=24)
    
    print(f"\n✅ Video successfully created: {output_file}")
    print(f"📊 Total duration: {total_duration:.1f} seconds")
    print(f"🎬 Number of scenes: {len(video_clips)}")

def main():
    # Check command line arguments
    if len(sys.argv) > 1:
        story_file = sys.argv[1]
        
        if not os.path.exists(story_file):
            print(f"Error: {story_file} file not found!")
            return
    else:
        # Get filename from user
        story_file = input("Please enter the name of the story.json file: ")
        
        if not story_file:
            print("No filename entered!")
            return
            
        if not story_file.endswith('.json'):
            story_file += '.json'
        
        if not os.path.exists(story_file):
            print(f"Error: {story_file} file not found!")
            return
    
    print(f"🎬 {story_file} Video Creator")
    print("=" * 50)
    
    create_video(story_file)

if __name__ == "__main__":
    main()