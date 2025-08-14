import streamlit as st
import os
import json
import tempfile
from datetime import datetime
from streamlit_option_menu import option_menu
from prompt_generator import generate_animal_story, save_story_to_json, generate_animal_story_with_client
# Removed old video_generator imports - now using unified_video_generator
from video_generator import (
    generate_video_ui
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Animal Life Video Creator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.sub-header {
    font-size: 1.5rem;
    color: #ff7f0e;
    margin-bottom: 1rem;
}
.info-box {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #1f77b4;
    margin: 1rem 0;
}
.success-box {
    background-color: #d4edda;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #28a745;
    margin: 1rem 0;
}
.error-box {
    background-color: #f8d7da;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #dc3545;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def check_api_keys():
    """Check and manage API keys for different services"""
    with st.sidebar:
        st.markdown("### 🔑 API Keys")
        
        # OpenAI API Key - Always require manual input
        openai_key = st.session_state.get('openai_api_key')
        if openai_key:
            st.success("🟢 OpenAI: Active")
            if st.button("🔄 Change OpenAI Key", key="change_openai"):
                st.session_state.openai_api_key = None
                st.rerun()
        else:
            st.error("🔴 OpenAI: Missing")
            openai_input = st.text_input(
                "OpenAI API Key:",
                type="password",
                placeholder="sk-...",
                key="openai_input"
            )
            if st.button("💾 Save OpenAI", key="save_openai"):
                if openai_input.startswith('sk-'):
                    st.session_state.openai_api_key = openai_input
                    from openai import OpenAI
                    st.session_state.openai_client = OpenAI(api_key=openai_input)
                    st.success("✅ OpenAI API key saved!")
                    st.rerun()
                else:
                    st.error("❌ Invalid OpenAI API key!")
        
        st.markdown("---")
        

        

    
    # Initialize OpenAI client if key is available
    if openai_key and not hasattr(st.session_state, 'openai_client'):
        from openai import OpenAI
        st.session_state.openai_client = OpenAI(api_key=openai_key)
    
    return openai_key

def main():
    # Initialize session state
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = None

    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = 'openai'
    
    # Check API keys
    openai_key = check_api_keys()
    
    # Main header
    st.markdown('<h1 class="main-header">🎬 Animal Life Video Creator</h1>', unsafe_allow_html=True)
    
    # Navigation menu
    selected = option_menu(
        menu_title=None,
        options=["Create Story", "Generate Video", "File Management"],
        icons=["book", "play-circle", "folder"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "25px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#1f77b4"},
        },
    )
    
    if selected == "Create Story":
        story_creation_page()
    elif selected == "Generate Video":
        video_generation_page()
    elif selected == "File Management":
        file_management_page()

def story_creation_page():
    """Story creation page"""
    st.markdown('<h2 class="sub-header">📖 Create Story</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="info-box">🎯 Create educational stories about animal life</div>', unsafe_allow_html=True)
        
        # Model selection
        st.markdown("### 🤖 Model Selection")
        model_option = st.radio(
            "Story generation model:",
            options=["openai"],
            format_func=lambda x: "🔵 OpenAI GPT-4",
            horizontal=True,
            help="Select the AI model to use for story creation"
        )
        
        # Check if selected model's API key is available
        openai_key = st.session_state.get('openai_api_key')
        
        if model_option == "openai" and not openai_key:
            st.error("⚠️ OpenAI API key required! Please enter your API key from the sidebar.")
            return
        
        st.session_state.selected_model = model_option
        
        # Input form
        with st.form("story_form"):
            animal_name = st.text_input(
                "🦁 Animal Name",
                placeholder="e.g: Lion, Penguin, Elephant...",
                help="Enter the name of the animal you want to create a story about"
            )
            
            num_scenes = st.slider(
                "🎬 Number of Scenes",
                min_value=3,
                max_value=15,
                value=8,
                help="How many scenes do you want in your story?"
            )
            
            submitted = st.form_submit_button("✨ Create Story", type="primary")
            
            if submitted:
                if animal_name:
                    create_story(animal_name, num_scenes, model_option)
                else:
                    st.error("Please enter an animal name!")
    
    with col2:
        st.markdown("### 📊 Cost Estimate")
        cost_estimate = num_scenes * 0.027  # Approximate cost per scene
        st.metric("Estimated Cost", f"${cost_estimate:.3f}")

def create_story(animal_name, num_scenes, model="openai"):
    """Create story with progress tracking"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        if model == "openai":
            status_text.text("🤖 Creating story with OpenAI...")
            progress_bar.progress(25)
            
            # Generate story using OpenAI
            client = st.session_state.openai_client
            story_data = generate_animal_story_with_client(client, animal_name, num_scenes)
            
            if story_data:
                progress_bar.progress(75)
                status_text.text("💾 Saving story...")
                
                # Save story to output directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{animal_name.lower()}_openai_{timestamp}.json"
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                filepath = os.path.join(output_dir, filename)
                save_story_to_json(story_data, filepath)
        
        if story_data:
            progress_bar.progress(100)
            status_text.text("✅ Story created successfully!")
            
            # Display success message
            model_name = "OpenAI GPT-4"
            display_filename = os.path.basename(filename) if isinstance(filename, str) else filename
            st.markdown(f'<div class="success-box">🎉 <strong>{story_data["story_title"]}</strong> story created with {model_name}!<br>📁 File: {display_filename}</div>', unsafe_allow_html=True)
            
            # Display story preview
            with st.expander("📖 Story Preview", expanded=True):
                st.json(story_data)
                
            # Download button
            file_to_read = filename if isinstance(filename, str) else filepath
            with open(file_to_read, 'r', encoding='utf-8') as f:
                st.download_button(
                    label="📥 Download JSON File",
                    data=f.read(),
                    file_name=os.path.basename(file_to_read),
                    mime="application/json"
                )
        else:
            st.error(f"Could not create story ({model_name}). Please try again.")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

def video_generation_page():
    """Video generation page"""
    st.markdown('<h2 class="sub-header">🎬 Generate Video</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="info-box">🎥 Create video from JSON story file</div>', unsafe_allow_html=True)
        
        # Video generation method selection
        st.markdown("### 🎥 Video Generation Method")
        video_method_options = {
            "image_based": "🖼️ Image-Based (OpenAI DALL-E + TTS)"
        }
        
        video_method = st.selectbox(
            "🎯 Video Generation Model:",
            list(video_method_options.keys()),
            format_func=lambda x: video_method_options[x],
            help="Select video generation model"
        )
        
        # Show method description
        method_descriptions = {
            "image_based": "📝 Creates images with OpenAI DALL-E, adds audio with TTS"
        }
        
        st.info(method_descriptions[video_method])
        
        # Set default platform specs
        default_specs = {'width': 1024, 'height': 1792, 'ratio': '9:16', 'max_duration': 120}
        st.session_state['platform_specs'] = default_specs
        
        # Check API key requirements
        openai_key = st.session_state.get('openai_api_key')
        gemini_key = st.session_state.get('gemini_api_key')
        
        # API key validation based on selected method
        if video_method == "image_based" and not openai_key:
            st.error("⚠️ OpenAI API key required for image-based video!")
            return
        
        # File selection
        output_dir = "output"
        json_files = []
        
        if os.path.exists(output_dir):
            json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        
        if json_files:
            selected_file = st.selectbox(
                "📁 Select Story File",
                json_files,
                help="Select one of the JSON story files from the output folder"
            )
            
            # File upload option
            st.markdown("**or**")
            uploaded_file = st.file_uploader(
                "📤 Upload JSON File",
                type=['json'],
                help="Upload a JSON story file from your computer"
            )
            
            # Voice selection (for methods that use TTS)
            if video_method == "image_based":
                voice_options = {
                    "alloy": "🎭 Alloy (General)",
                    "echo": "🔊 Echo (Echoing)",
                    "fable": "📚 Fable (Storytelling)",
                    "onyx": "💎 Onyx (Deep)",
                    "nova": "⭐ Nova (Young)",
                    "shimmer": "✨ Shimmer (Bright)"
                }
                
                selected_voice = st.selectbox(
                    "🎤 Select Voice",
                    list(voice_options.keys()),
                    format_func=lambda x: voice_options[x],
                    index=0,
                    help="Select voice tone for TTS (Text-to-Speech)"
                )
            else:
                selected_voice = None
            
            if st.button("🎬 Create Video", type="primary"):
                file_to_process = None
                
                if uploaded_file:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                        json.dump(json.load(uploaded_file), tmp_file)
                        file_to_process = tmp_file.name
                elif selected_file:
                    file_to_process = os.path.join(output_dir, selected_file)
                
                if file_to_process:
                    generate_video(file_to_process, selected_voice)
                else:
                    st.error("Please select or upload a file!")
        else:
            st.warning("📁 No JSON story files found. First create a story from the 'Create Story' tab.")
    
    with col2:
        pass  # Tips section removed

def generate_video(story_file, voice):
    """Generate video with progress tracking using video generator"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Get platform specs from session state
        platform_specs = st.session_state.get('platform_specs', {'width': 1024, 'height': 1792})
        
        # Get OpenAI API key
        openai_key = st.session_state.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        
        # Generate video using video generator
        final_video_path, success, story_data = generate_video_ui(
            story_file, voice, platform_specs, openai_key, 
            progress_callback=progress_bar.progress,
            status_callback=status_text.text
        )
        
        if success and final_video_path and os.path.exists(final_video_path):
            # Display success message
            st.markdown(f'<div class="success-box">🎉 <strong>{story_data["story_title"]}</strong> video created!<br>📁 File: {final_video_path}</div>', unsafe_allow_html=True)
            
            # Video info
            total_duration = story_data.get('total_duration', len(story_data['scenes']) * 8)
            st.markdown(f"""
            **📊 Video Information:**
            - 🎬 Scene count: {len(story_data['scenes'])}
            - ⏱️ Total duration: {total_duration} seconds
            - 📐 Size: {platform_specs['width']}x{platform_specs['height']} px ({platform_specs.get('ratio', 'N/A')})
            - 🤖 Model: OpenAI DALL-E + TTS (Video Generator)
            - 📁 File path: {final_video_path}
            """)
            
            # Show video player
            if os.path.exists(final_video_path):
                st.video(final_video_path)
            
            # Download button
            with open(final_video_path, 'rb') as f:
                st.download_button(
                    label="📥 Download Video File",
                    data=f.read(),
                    file_name=os.path.basename(final_video_path),
                    mime="video/mp4"
                )
        else:
            st.error("Could not create video. Please check your API key and try again.")
            
    except Exception as e:
        st.error(f"Video creation error: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()





def file_management_page():
    """File management page"""
    st.markdown('<h2 class="sub-header">📁 File Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 JSON Story Files")
        output_dir = "output"
        
        if os.path.exists(output_dir):
            json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
            
            if json_files:
                for file in json_files:
                    file_path = os.path.join(output_dir, file)
                    with st.expander(f"📖 {file}"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            st.write(f"**Title:** {data.get('story_title', 'N/A')}")
                            st.write(f"**Scene count:** {len(data.get('scenes', []))}")
                            st.write(f"**Total duration:** {data.get('total_duration', 'N/A')} seconds")
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    st.download_button(
                                        "📥 Download",
                                        f.read(),
                                        file_name=file,
                                        mime="application/json",
                                        key=f"download_{file}"
                                    )
                            with col_b:
                                if st.button("🗑️ Delete", key=f"delete_{file}"):
                                    os.remove(file_path)
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Could not read file: {str(e)}")
            else:
                st.info("No JSON story files yet.")
        else:
            st.info("Output folder not found.")
    
    with col2:
        st.markdown("### 🎥 Video Files")
        output_dir = "output"
        
        if os.path.exists(output_dir):
            video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
            
            if video_files:
                for file in video_files:
                    file_path = os.path.join(output_dir, file)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    
                    with st.expander(f"🎬 {file}"):
                        st.write(f"**File size:** {file_size:.1f} MB")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                    "📥 Download",
                                    f.read(),
                                    file_name=file,
                                    mime="video/mp4",
                                    key=f"download_video_{file}"
                                )
                        with col_b:
                            if st.button("🗑️ Delete", key=f"delete_video_{file}"):
                                os.remove(file_path)
                                st.rerun()
                        
                        # Show video preview
                        st.video(file_path)
            else:
                st.info("No video files yet.")
        else:
            st.info("Output folder not found.")

if __name__ == "__main__":
    main()