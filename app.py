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
    """Get basic video information and check availability"""
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
                'video_id': video_id,
                'available': True
            }
        else:
            # Try alternative method - check if video page exists
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.head(video_url, timeout=5, allow_redirects=True)
            
            if response.status_code == 200:
                return {
                    'title': f'Video {video_id[:8]}...',
                    'video_id': video_id,
                    'available': True
                }
            else:
                return {
                    'title': f'Video {video_id[:8]}...',
                    'video_id': video_id,
                    'available': False
                }
    except Exception as e:
        # If all methods fail, assume video is available (let YouTube handle it)
        return {
            'title': f'Video {video_id[:8]}...',
            'video_id': video_id,
            'available': True  # Changed to True to be less restrictive
        }

def get_youtube_videos_with_chatgpt(prompt, exclude_songs=None):
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
        
        # Add exclusion instruction if we have previous songs
        if exclude_songs:
            exclude_list = [f"{song['title']} by {song['artist']}" for song in exclude_songs]
            user_prompt = f"Suggest 10 songs related to: {prompt}. Please avoid these songs: {', '.join(exclude_list)}"
        else:
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
        #st.markdown("### ⚙️ Configuration")
        

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
                            st.session_state.current_song_index = 0
                            
                            # Initialize persistent song list
                            st.session_state.all_song_details = []
                            
                            # Reset revealed song state
                            if 'revealed_song' in st.session_state:
                                del st.session_state.revealed_song
                            
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
                        # Get ALL existing songs to exclude them (persistent across multiple presses)
                        all_existing_songs = []
                        if 'all_song_details' in st.session_state:
                            all_existing_songs.extend(st.session_state.all_song_details)
                        if 'song_details' in st.session_state:
                            all_existing_songs.extend(st.session_state.song_details)
                        
                        video_ids = get_youtube_videos_with_chatgpt(prompt, all_existing_songs)
                        
                        if video_ids:
                            st.success(f"🎉 Found {len(video_ids)} new songs!")
                            
                            # Store videos in session state
                            st.session_state.videos = []
                            st.session_state.current_song_index = 0
                            
                            # Move current songs to all_song_details for persistence
                            if 'song_details' in st.session_state:
                                if 'all_song_details' not in st.session_state:
                                    st.session_state.all_song_details = []
                                st.session_state.all_song_details.extend(st.session_state.song_details)
                            
                            # Reset revealed song state
                            if 'revealed_song' in st.session_state:
                                del st.session_state.revealed_song
                            
                            for video_id in video_ids:
                                video_info = get_video_info(video_id)
                                st.session_state.videos.append(video_info)
                        else:
                            st.error("❌ No songs found. Please try a different prompt.")
    

    # Display single song for guessing game
    if 'videos' in st.session_state and st.session_state.videos:
        st.markdown('<h2 class="sub-header" style="text-align: center;">🎵 Song Guessing Game</h2>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center;"><strong>Listen to each song and try to guess what it is and where it\'s from!</strong></div>', unsafe_allow_html=True)
        
        # Get current song index
        current_index = st.session_state.get('current_song_index', 0)
        total_songs = len(st.session_state.videos)
        
        if current_index < total_songs:
            current_video = st.session_state.videos[current_index]
            
            # Song counter
            st.markdown(f'<div style="text-align: center;"><strong>Song {current_index + 1} of {total_songs}</strong></div>', unsafe_allow_html=True)
            
            # Check video availability
            if not current_video.get('available', True):
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                st.warning("⚠️ This video may not be available. Trying to play anyway...")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Play and reveal buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("🔍 Reveal Song", key="reveal_current", use_container_width=True):
                    st.session_state.revealed_song = current_index
            
            with col2:
                if st.button("⏭️ Next Song", key="next_song", use_container_width=True):
                    if current_index < total_songs - 1:
                        st.session_state.current_song_index = current_index + 1
                        st.session_state.selected_video = st.session_state.videos[current_index + 1]['video_id']
                        st.session_state.current_song_number = current_index + 2
                        st.session_state.auto_play = True
                        st.rerun()
            
            with col3:
                if st.button("⏮️ Previous Song", key="prev_song", use_container_width=True):
                    if current_index > 0:
                        st.session_state.current_song_index = current_index - 1
                        st.session_state.selected_video = st.session_state.videos[current_index - 1]['video_id']
                        st.session_state.current_song_number = current_index
                        st.session_state.auto_play = True
                        st.rerun()
            
            # Show revealed song details
            if st.session_state.get('revealed_song') == current_index and 'song_details' in st.session_state:
                if current_index < len(st.session_state.song_details):
                    song_info = st.session_state.song_details[current_index]
                    st.markdown(f"""
                    <div style="text-align: center;">
                    <strong>🎵 {song_info['title']}</strong><br>
                    <strong>🎬 From:</strong> {song_info['source']}<br>
                    <strong>👤 Artist:</strong> {song_info['artist']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Play button for manual control
            if st.button("▶️ Play Song", key="play_current", use_container_width=True):
                st.session_state.selected_video = current_video['video_id']
                st.session_state.current_song_number = current_index + 1
                st.session_state.auto_play = True
                st.rerun()
    
    # Add extensive spacing to move video player much lower
    st.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    
    # Video player
    if 'selected_video' in st.session_state:
        song_number = st.session_state.get('current_song_number', '?')
        st.markdown(f'<h2 class="sub-header" style="text-align: center;">🎵 Now Playing: Song #{song_number}</h2>', unsafe_allow_html=True)
        
        # Check if current video is available
        current_index = st.session_state.get('current_song_index', 0)
        if 'videos' in st.session_state and current_index < len(st.session_state.videos):
            current_video = st.session_state.videos[current_index]
            if not current_video.get('available', True):
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                st.warning("⚠️ This video may not be available. If it doesn't play, try the alternative link below.")
                st.markdown('</div>', unsafe_allow_html=True)
        
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
        st.markdown('<div style="text-align: center;"><strong>Alternative:</strong> <a href="https://www.youtube.com/watch?v=' + video_id + '" target="_blank">Open in YouTube</a></div>', unsafe_allow_html=True)
        
        # Close button
        if st.button("❌ Close Player"):
            del st.session_state.selected_video
            st.rerun()

if __name__ == "__main__":
    main() 