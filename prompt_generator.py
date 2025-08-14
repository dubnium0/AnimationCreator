import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_animal_story_with_client(client, animal_name, num_scenes=5):
    """
    Creates an animal's life story scene by scene using provided OpenAI client.
    
    Args:
        client: OpenAI client instance
        animal_name (str): Name of the animal
        num_scenes (int): Number of scenes to create
    
    Returns:
        dict: List of created scenes
    """
    # Create prompt request
    system_prompt = """
    You are a children's nature story writer who generates scene-by-scene English narration and image prompts about an animal's life.
    Each scene should be educational, engaging, and suitable for children.
    Focus on the animal's natural behaviors, habitat, and life cycle.
    """
    
    user_prompt = f"""
    Create a story about a {animal_name}'s life with {num_scenes} scenes.
    
    Provide the response in the following JSON format:
    {{
        "scenes": [
            {{
                "scene_number": 1,
                "narration": "English narration text for this scene",
                "image_prompt": "Detailed image generation prompt for this scene",
                "duration": 5,
                "background_music": "nature_sounds_gentle"
            }}
        ],
        "story_title": "Title of the story",
        "total_duration": 25
    }}
    """
    
    try:
        # Send request to OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4096
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

def generate_animal_story(animal_name, num_scenes=5):
    """
    Creates an animal's life story scene by scene.
    
    Args:
        animal_name (str): Name of the animal
        num_scenes (int): Number of scenes to create
    
    Returns:
        dict: List of created scenes
    """
    # Create prompt request
    system_prompt = """
    You are a children's nature story writer who generates scene-by-scene English narration and image prompts about an animal's life.
    Each scene should be educational, engaging, and suitable for children.
    Focus on the animal's natural behaviors, habitat, and life cycle.
    """
    
    user_prompt = f"""
    Create a story about a {animal_name}'s life with {num_scenes} scenes.
    
    Provide the response in the following JSON format:
    {{
        "scenes": [
            {{
                "scene_number": 1,
                "narration": "English narration text for this scene",
                "image_prompt": "Detailed image generation prompt for this scene",
                "duration": 5,
                "background_music": "nature_sounds_gentle"
            }}
        ],
        "story_title": "Title of the story",
        "total_duration": 25
    }}
    """
    
    try:
        # Send request to OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4096
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

def save_story_to_json(story_data, output_file):
    """
    Saves story data to JSON file.
    
    Args:
        story_data (dict): Story data
        output_file (str): Output file path
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, indent=2, ensure_ascii=False)
        print(f"Story successfully saved: {output_file}")
    except Exception as e:
        print(f"File save error: {str(e)}")

def main():
    # Create example animal story
    animal_name = "Lion"
    num_scenes = 10
    story_data = generate_animal_story(animal_name, num_scenes)
    
    if story_data:
        # Save story to JSON file
        output_file = f"{animal_name}_story.json"
        save_story_to_json(story_data, output_file)
        
        # Show results
        print("\nGenerated Story:")
        print(json.dumps(story_data, indent=2, ensure_ascii=False))

# ===== GEMINI FUNCTIONS =====













if __name__ == "__main__":
    main()