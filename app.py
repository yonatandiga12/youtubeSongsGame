import streamlit as st
from openai import OpenAI
from youtubesearchpython import VideosSearch
import json
import re

# Configure OpenAI - only from Streamlit secrets
def get_openai_api_key():
    return st.secrets.get("OPENAI_API_KEY")

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
    """Get basic video information"""
    try:
        # Use a simpler approach to avoid the proxies issue
        import requests
        
        # Get video info from YouTube oEmbed API
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', 'Unknown Title'),
                'video_id': video_id
            }
    except Exception as e:
        # If oEmbed fails, just return basic info
        pass
    
    return {
        'title': f'Video {video_id[:8]}...',
        'video_id': video_id
    }

def get_youtube_videos_with_chatgpt(prompt):
    """Use ChatGPT to get song suggestions, then search YouTube for those songs"""
    try:
        # First, use ChatGPT to suggest songs based on the prompt
        system_prompt = """You are a helpful assistant that suggests songs based on user prompts.
        For each suggestion, provide:
        1. The song title
        2. The movie/show/game it's from (if applicable)
        3. The artist/band name
        4. link to youtube

        Return the information in this exact JSON format:
        [
            {
                "title": "Song Title",
                "source": "Movie/Show/Game Name",
                "artist": "Artist/Band Name",
                "link": "url link"
            }
        ]
        
        Return exactly 10 songs. Make sure the JSON is valid."""
        
        user_prompt = f"Suggest 10 songs related to: {prompt}"
        
        from openai import OpenAI
        
        # Get API key from Streamlit secrets
        api_key = get_openai_api_key()
        if not api_key:
            st.error("❌ OpenAI API key not found in Streamlit Cloud secrets!")
            return []
            
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            import json
            song_data = json.loads(content)
            video_ids = []
            song_details = []
            
            # Process each song suggested by GPT
            for song_info in song_data:
                # Extract video ID from the link provided by GPT
                video_link = song_info.get('link', '')
                extracted_ids = extract_youtube_links(video_link)
                
                if extracted_ids:
                    video_ids.append(extracted_ids[0])
                    song_details.append({
                        'title': song_info.get('title', 'Unknown Title'),
                        'source': song_info.get('source', 'Unknown Source'),
                        'artist': song_info.get('artist', 'Unknown Artist'),
                        'video_id': extracted_ids[0]
                    })
            
            # Store song details in session state
            st.session_state.song_details = song_details
            
            return video_ids[:10]  # Return max 10 videos
            
        except json.JSONDecodeError:
            st.warning("ChatGPT didn't return valid JSON. Using fallback method...")
            # Fallback to direct YouTube search
            search = VideosSearch(prompt, limit=10)
            results = search.result()
            video_ids = []
            
            for video in results.get('result', []):
                video_url = video.get('link', '')
                extracted_ids = extract_youtube_links(video_url)
                if extracted_ids:
                    video_ids.append(extracted_ids[0])
            
            return video_ids[:10]
        
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def main():
    # Main header
    st.markdown('<h1 class="main-header">🎵 YouTube Video Game 🎵</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        

        st.markdown("### 🎮 How to Play")
        st.markdown("""
        1. Enter a prompt describing the type of songs you want
        2. Click 'Generate Videos' to get 10 song links
        3. Click on any song button to play it
        4. Listen and try to guess what song it is and where it's from!
        """)
        
        st.markdown("---")
        st.markdown("### 💡 Example Prompts")
        st.markdown("""
        - "songs from movies"
        - "80s pop hits"
        - "classic rock songs"
        - "disney movie songs"
        - "video game music"
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
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🎲 Generate Videos", type="primary", use_container_width=True):
                if not prompt:
                    st.warning("Please enter a prompt first!")
                elif not get_openai_api_key():
                    st.error("❌ OpenAI API key not found!")
                    st.info("Please add your API key in Streamlit Cloud Settings → Secrets")
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
            if st.button("🔄 New Songs", use_container_width=True):
                if not prompt:
                    st.warning("Please enter a prompt first!")
                elif not get_openai_api_key():
                    st.error("❌ OpenAI API key not found!")
                    st.info("Please add your API key in Streamlit Cloud Settings → Secrets")
                else:
                    with st.spinner("🎵 Generating new songs..."):
                        video_ids = get_youtube_videos_with_chatgpt(prompt)
                        
                        if video_ids:
                            st.success(f"🎉 Found {len(video_ids)} new songs!")
                            
                            # Store videos in session state
                            st.session_state.videos = []
                            for video_id in video_ids:
                                video_info = get_video_info(video_id)
                                st.session_state.videos.append(video_info)
                        else:
                            st.error("❌ No songs found. Please try a different prompt.")
    
    with col2:
        st.markdown('<h2 class="sub-header">📊 Stats</h2>', unsafe_allow_html=True)
        if 'videos' in st.session_state:
            st.metric("Videos Found", len(st.session_state.videos))
        else:
            st.metric("Videos Found", 0)
    
    # Display videos for guessing game
    if 'videos' in st.session_state and st.session_state.videos:
        st.markdown('<h2 class="sub-header">🎵 Song Guessing Game</h2>', unsafe_allow_html=True)
        st.markdown("**Listen to each song and try to guess what it is and where it's from!**")
        
        # Hide all button
        if st.button("🙈 Hide All Reveals", key="hide_all"):
            if 'revealed_song' in st.session_state:
                del st.session_state.revealed_song
        
        # Create a grid of play buttons
        cols = st.columns(3)  # 3 columns for better layout
        
        for i, video in enumerate(st.session_state.videos):
            col_idx = i % 3
            with cols[col_idx]:
                with st.container():
                    st.markdown('<div class="video-card">', unsafe_allow_html=True)
                    
                    # Play and reveal buttons in a row
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Check if this song is currently playing
                        is_playing = (st.session_state.get('selected_video') == video['video_id'])
                        button_text = f"⏸️ Song #{i+1}" if is_playing else f"🎵 Song #{i+1}"
                        
                        if st.button(button_text, key=f"play_{i}", use_container_width=True):
                            st.session_state.selected_video = video['video_id']
                            st.session_state.current_song_number = i + 1
                            # Auto-start the video by setting autoplay parameter
                            st.session_state.auto_play = True
                    
                    with col2:
                        if st.button("🔍 Reveal", key=f"reveal_{i}", use_container_width=True):
                            st.session_state.revealed_song = i
                    
                    # Show revealed song details
                    if st.session_state.get('revealed_song') == i and 'song_details' in st.session_state:
                        if i < len(st.session_state.song_details):
                            song_info = st.session_state.song_details[i]
                            st.markdown(f"""
                            **🎵 {song_info['title']}**  
                            **🎬 From:** {song_info['source']}  
                            **👤 Artist:** {song_info['artist']}
                            """)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Video player
    if 'selected_video' in st.session_state:
        song_number = st.session_state.get('current_song_number', '?')
        st.markdown(f'<h2 class="sub-header">🎵 Now Playing: Song #{song_number}</h2>', unsafe_allow_html=True)
        
        # Create YouTube embed URL with autoplay
        video_id = st.session_state.selected_video
        autoplay_param = "&autoplay=1" if st.session_state.get('auto_play', False) else ""
        embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1{autoplay_param}"
        
        # Reset autoplay flag
        st.session_state.auto_play = False
        
        # Display video using iframe with better compatibility
        st.markdown(f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <iframe 
                src="{embed_url}" 
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