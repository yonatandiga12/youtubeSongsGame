import streamlit as st
import openai
import os
from dotenv import load_dotenv
from youtubesearchpython import VideosSearch
import json
import re

# Load environment variables
load_dotenv()

# Configure OpenAI - try Streamlit secrets first, then environment variables
if 'OPENAI_API_KEY' in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    openai.api_key = os.getenv("OPENAI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="YouTube Video Game",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF6B6B;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #4ECDC4;
        margin-bottom: 1rem;
    }
    .video-card {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .prompt-input {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def extract_youtube_links(text):
    """Extract YouTube video IDs from text using regex"""
    # Pattern to match YouTube URLs
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)'
    ]
    
    video_ids = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        video_ids.extend(matches)
    
    return list(set(video_ids))  # Remove duplicates

def get_video_info(video_id):
    """Get video information using YouTube Search Python"""
    try:
        search = VideosSearch(f"https://www.youtube.com/watch?v={video_id}")
        results = search.result()
        if results and 'result' in results and len(results['result']) > 0:
            video = results['result'][0]
            return {
                'title': video.get('title', 'Unknown Title'),
                'duration': video.get('duration', 'Unknown Duration'),
                'viewCount': video.get('viewCount', {}).get('text', 'Unknown Views'),
                'channel': video.get('channel', {}).get('name', 'Unknown Channel'),
                'thumbnail': video.get('thumbnails', [{}])[0].get('url', ''),
                'video_id': video_id
            }
    except Exception as e:
        st.error(f"Error fetching video info: {e}")
    
    return {
        'title': 'Unknown Title',
        'duration': 'Unknown Duration',
        'viewCount': 'Unknown Views',
        'channel': 'Unknown Channel',
        'thumbnail': '',
        'video_id': video_id
    }

def get_youtube_videos_with_chatgpt(prompt):
    """Use ChatGPT to get YouTube video suggestions"""
    try:
        system_prompt = """You are a helpful assistant that suggests YouTube videos based on user prompts. 
        For each suggestion, provide a YouTube video URL. Return exactly 10 video URLs, one per line.
        Only return the URLs, no additional text or formatting."""
        
        user_prompt = f"Find 10 YouTube videos related to: {prompt}. Return only the YouTube URLs, one per line."
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        video_ids = extract_youtube_links(content)
        
        # If ChatGPT didn't provide enough links, use YouTube search as fallback
        if len(video_ids) < 10:
            st.info("ChatGPT didn't provide enough links. Using YouTube search as fallback...")
            search = VideosSearch(prompt, limit=10)
            results = search.result()
            
            for video in results.get('result', []):
                video_url = video.get('link', '')
                video_id = extract_youtube_links(video_url)
                if video_id and video_id[0] not in video_ids:
                    video_ids.append(video_id[0])
        
        return video_ids[:10]  # Return max 10 videos
        
    except Exception as e:
        st.error(f"Error with ChatGPT API: {e}")
        # Fallback to direct YouTube search
        st.info("Using YouTube search as fallback...")
        try:
            search = VideosSearch(prompt, limit=10)
            results = search.result()
            video_ids = []
            
            for video in results.get('result', []):
                video_url = video.get('link', '')
                extracted_ids = extract_youtube_links(video_url)
                if extracted_ids:
                    video_ids.append(extracted_ids[0])
            
            return video_ids[:10]
        except Exception as e2:
            st.error(f"Error with YouTube search: {e2}")
            return []

def main():
    # Main header
    st.markdown('<h1 class="main-header">🎵 YouTube Video Game 🎵</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        # API Key input (only show if not in secrets)
        if 'OPENAI_API_KEY' not in st.secrets:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Enter your OpenAI API key to use ChatGPT for video suggestions"
            )
            
            if api_key:
                openai.api_key = api_key
        else:
            st.success("✅ API key loaded from secrets")
        
        st.markdown("---")
        st.markdown("### 🎮 How to Play")
        st.markdown("""
        1. Enter a prompt describing the type of videos you want
        2. Click 'Generate Videos' to get 10 YouTube links
        3. Click on any video to play it directly in the app
        4. Enjoy your personalized video collection!
        """)
        
        st.markdown("---")
        st.markdown("### 💡 Example Prompts")
        st.markdown("""
        - "songs from movies"
        - "funny cat videos"
        - "cooking tutorials"
        - "gaming highlights"
        - "educational content"
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h2 class="sub-header">🎯 Enter Your Video Prompt</h2>', unsafe_allow_html=True)
        
        # Prompt input
        with st.container():
            st.markdown('<div class="prompt-input">', unsafe_allow_html=True)
            prompt = st.text_input(
                "What kind of videos are you looking for?",
                placeholder="e.g., songs from movies, funny cat videos, cooking tutorials...",
                key="prompt_input"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Generate button
        if st.button("🎲 Generate Videos", type="primary", use_container_width=True):
            if not prompt:
                st.warning("Please enter a prompt first!")
            elif not openai.api_key:
                st.warning("Please enter your OpenAI API key in the sidebar!")
            else:
                with st.spinner("🎵 Generating your video collection..."):
                    video_ids = get_youtube_videos_with_chatgpt(prompt)
                    
                    if video_ids:
                        st.success(f"🎉 Found {len(video_ids)} videos!")
                        
                        # Store videos in session state
                        st.session_state.videos = []
                        for video_id in video_ids:
                            video_info = get_video_info(video_id)
                            st.session_state.videos.append(video_info)
                    else:
                        st.error("❌ No videos found. Please try a different prompt.")
    
    with col2:
        st.markdown('<h2 class="sub-header">📊 Stats</h2>', unsafe_allow_html=True)
        if 'videos' in st.session_state:
            st.metric("Videos Found", len(st.session_state.videos))
        else:
            st.metric("Videos Found", 0)
    
    # Display videos
    if 'videos' in st.session_state and st.session_state.videos:
        st.markdown('<h2 class="sub-header">🎬 Your Video Collection</h2>', unsafe_allow_html=True)
        
        # Create columns for video display
        cols = st.columns(2)
        
        for i, video in enumerate(st.session_state.videos):
            col_idx = i % 2
            with cols[col_idx]:
                with st.container():
                    st.markdown('<div class="video-card">', unsafe_allow_html=True)
                    
                    # Video thumbnail
                    if video['thumbnail']:
                        st.image(video['thumbnail'], use_column_width=True)
                    
                    # Video title
                    st.markdown(f"**{video['title']}**")
                    
                    # Video details
                    st.markdown(f"📺 **Channel:** {video['channel']}")
                    st.markdown(f"⏱️ **Duration:** {video['duration']}")
                    st.markdown(f"👁️ **Views:** {video['viewCount']}")
                    
                    # Play button
                    if st.button(f"▶️ Play Video", key=f"play_{i}", use_container_width=True):
                        st.session_state.selected_video = video['video_id']
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Video player
    if 'selected_video' in st.session_state:
        st.markdown('<h2 class="sub-header">🎥 Now Playing</h2>', unsafe_allow_html=True)
        
        # Create YouTube embed URL
        video_id = st.session_state.selected_video
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        
        # Display video using iframe with better compatibility
        st.markdown(f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <iframe 
                src="{embed_url}?rel=0&modestbranding=1" 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; border-radius: 10px;" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)
        
        # Alternative: Direct link
        st.markdown("---")
        st.markdown("**Alternative:** [Open in YouTube](https://www.youtube.com/watch?v=" + video_id + ")")
        
        # Close button
        if st.button("❌ Close Player"):
            del st.session_state.selected_video
            st.rerun()

if __name__ == "__main__":
    main() 