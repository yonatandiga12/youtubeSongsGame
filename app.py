import streamlit as st
from openai import OpenAI
from youtubesearchpython import VideosSearch
import json
import re
import subprocess


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





# def _build_search_query(song_info):
#     title = song_info.get("title", "").strip()
#     artist = song_info.get("artist", "").strip()
#     source = song_info.get("source", "").strip()

#     # Strong base: title + artist; append source if it seems helpful
#     parts = [title, artist]
#     if source and len(source) <= 40:
#         parts.append(source)
#     # Bias toward the right version
#     parts.append("official video")
#     return " ".join([p for p in parts if p])


# def _is_bad_candidate(title: str) -> bool:
#     """Filter out likely non-originals unless we have no choice."""
#     t = title.lower()
#     bad_words = ["cover", "karaoke", "instrumental", "remix", "sped up", "slowed", "nightcore"]
#     return any(w in t for w in bad_words)


# def _score_candidate(item, song_info) -> int:
#     """Heuristic score to prefer official sources."""
#     score = 0
#     title = (item.get("title") or "").lower()
#     channel = (item.get("channel", {}).get("name") or "").lower()
#     artist = (song_info.get("artist") or "").lower()

#     # Title contains full song title words
#     if (song_info.get("title") or "").lower() in title:
#         score += 3

#     # Channel heuristics
#     if "vevo" in channel:
#         score += 4
#     if f"{artist} - topic" in channel or " - topic" in channel:
#         score += 3
#     if artist and artist in channel:
#         score += 2

#     # “Official”
#     if "official" in title:
#         score += 2

#     # Penalize bad candidates
#     if _is_bad_candidate(title):
#         score -= 3

#     # Longer than 60s usually means it’s not a short/teaser
#     duration = item.get("duration")
#     if duration:
#         try:
#             m, s = duration.split(":") if ":" in duration else ("0", duration)
#             total = int(m) * 60 + int(s)
#             if total >= 60:
#                 score += 1
#         except Exception:
#             pass

#     return score


# def _search_youtube_by_song(song_info, limit=10):
#     """Return best video_id (or None) for a given song_info."""
#     query = _build_search_query(song_info)
#     search = VideosSearch(query, limit=limit)
#     results = search.result().get("result", [])

#     if not results:
#         # Relax query: drop 'official video'
#         fallback_query = f"{song_info.get('title','')} {song_info.get('artist','')}"
#         search = VideosSearch(fallback_query, limit=limit)
#         results = search.result().get("result", [])

#     if not results:
#         return None

#     # Rank candidates
#     ranked = sorted(results, key=lambda it: _score_candidate(it, song_info), reverse=True)

#     # Try candidates until one passes your availability check
#     for it in ranked:
#         video_url = it.get("link", "")
#         ids = extract_youtube_links(video_url)
#         if not ids:
#             continue
#         vid = ids[0]
#         info = get_video_info(vid)
#         if info.get("available"):
#             return vid

#     # If none “available”, return best id anyway as a fallback
#     for it in ranked:
#         ids = extract_youtube_links(it.get("link", ""))
#         if ids:
#             return ids[0]

#     return None




# def extract_youtube_links(text):
#     """Extract YouTube video IDs from text using regex"""
#     # Pattern to match YouTube URLs
#     patterns = [
#         r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
#         r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
#         r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)'
#     ]
    
#     video_ids = []
#     for pattern in patterns:
#         matches = re.findall(pattern, text)
#         video_ids.extend(matches)
    
#     return list(set(video_ids))  # Remove duplicates


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
            return {
                'title': f'Video {video_id[:8]}...',
                'video_id': video_id,
                'available': False
            }
    except Exception as e:
        # If oEmbed fails, video might not be available
        return {
            'title': f'Video {video_id[:8]}...',
            'video_id': video_id,
            'available': False
        }



# def get_youtube_videos_with_chatgpt(prompt, exclude_songs=None):
#     """Use ChatGPT to get song suggestions, then search YouTube for those songs"""
#     try:
#         # First, use ChatGPT to suggest songs based on the prompt
#         system_prompt = """You are a helpful assistant that suggests songs based on user prompts.
#         For each suggestion, provide:
#         1. The song title
#         2. The movie/show/game it's from (if applicable)
#         3. The artist/band name
#         4. link to youtube

#         Return the information in this exact JSON format:
#         [
#             {
#                 "title": "Song Title",
#                 "source": "Movie/Show/Game Name",
#                 "artist": "Artist/Band Name",
#                 "link": "url link"
#             }
#         ]
        
#         Return exactly 10 songs. Make sure the JSON is valid."""
        
#         # Add exclusion instruction if we have previous songs
#         if exclude_songs:
#             exclude_list = [f"{song['title']} by {song['artist']}" for song in exclude_songs]
#             user_prompt = f"Suggest 10 songs related to: {prompt}. Please avoid these songs: {', '.join(exclude_list)}"
#         else:
#             user_prompt = f"Suggest 10 songs related to: {prompt}"
        
#         from openai import OpenAI
        
#         # Get API key from Streamlit secrets
#         api_key = get_openai_api_key()
#         if not api_key:
#             st.error("❌ OpenAI API key not found in Streamlit Cloud secrets!")
#             return []
            
#         client = OpenAI(api_key=api_key)
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ],
#             max_tokens=1000,
#             temperature=0.7
#         )
        
#         content = response.choices[0].message.content.strip()
        
#         # Try to parse JSON response
#         try:
#             import json
#             song_data = json.loads(content)
#             video_ids = []
#             song_details = []
            
#             # Process each song suggested by GPT
#             for song_info in song_data:
#                 # Extract video ID from the link provided by GPT
#                 video_link = song_info.get('link', '')
#                 extracted_ids = extract_youtube_links(video_link)
                
#                 if extracted_ids:
#                     video_ids.append(extracted_ids[0])
#                     song_details.append({
#                         'title': song_info.get('title', 'Unknown Title'),
#                         'source': song_info.get('source', 'Unknown Source'),
#                         'artist': song_info.get('artist', 'Unknown Artist'),
#                         'video_id': extracted_ids[0]
#                     })
            
#             # Store song details in session state
#             st.session_state.song_details = song_details
            
#             return video_ids[:10]  # Return max 10 videos
            
#         except json.JSONDecodeError:
#             st.warning("ChatGPT didn't return valid JSON. Using fallback method...")
#             # Fallback to direct YouTube search
#             search = VideosSearch(prompt, limit=10)
#             results = search.result()
#             video_ids = []
            
#             for video in results.get('result', []):
#                 video_url = video.get('link', '')
#                 extracted_ids = extract_youtube_links(video_url)
#                 if extracted_ids:
#                     video_ids.append(extracted_ids[0])
            
#             return video_ids[:10]
        
#     except Exception as e:
#         st.error(f"Error: {e}")
#         return []


def debug_message(message: str):
    st.markdown(
        f"""
        <div style="background-color:#ffe8cc; padding:10px; border-radius:5px; border-left: 4px solid #ffa94d; margin-top:20px;">
            <strong>🛠 Debug:</strong> {message}
        </div>
        """,
        unsafe_allow_html=True
    )


# Helper: extract video ID from YouTube URL
def extract_youtube_links(url):
    import re
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return [match.group(1)] if match else []


def search_youtube_for_song(title, artist):
    query = f"{title} {artist} official"
    search_url = f"ytsearch5:{query}"  # Try 5 results instead of 1
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", search_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # yt-dlp outputs one JSON line per video
            for line in result.stdout.splitlines():
                try:
                    video_json = json.loads(line)
                    if not video_json.get("is_unavailable"):
                        video_id = video_json["id"]
                        debug_message(f"✅ Found video: {video_id}")
                        return video_id
                except json.JSONDecodeError:
                    continue

            debug_message("⚠️ No available videos found")
        else:
            debug_message(f"❌ yt-dlp error: {result.stderr}")
    except Exception as e:
        debug_message("❌ yt-dlp exception")
        st.error(f"Error using yt-dlp: {e}")

    return None




# def search_youtube_for_song(title, artist):
#     query = f"{title} {artist} official"
#     search_url = f"ytsearch1:{query}"  # ytsearch1: returns 1 result
#     try:
#         result = subprocess.run(
#             ["yt-dlp", "--dump-json", search_url],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             timeout=20
#         )
#         if result.returncode == 0:    
#             video_json = json.loads(result.stdout.splitlines()[0])
        
#             debug_message(f"17 {video_json["id"]} , {video_json["webpage_url"]}")
        
#             return video_json["id"]  # or video_json["webpage_url"]
#         else:
#             debug_message(f"error {result.stderr}")
#             print(result.stderr)
#     except Exception as e:
        
#         debug_message("error")
        
#         st.error(f"Error using yt-dlp: {e}")

#     return None




# MAIN FUNCTION
def get_youtube_videos_with_chatgpt(prompt, exclude_songs=None):
    try:
        # GPT SYSTEM PROMPT
        system_prompt = """You are a helpful assistant that suggests songs based on user prompts.
        For each suggestion, provide:
        1. The song title
        2. The movie/show/game it's from (if applicable)
        3. The artist/band name

        Return the information in this exact JSON format:
        [
            {
                "title": "Song Title",
                "source": "Movie/Show/Game Name",
                "artist": "Artist/Band Name"
            }
        ]

        Return exactly 20 songs. Make sure the JSON is valid."""

        # Compose user prompt
        if exclude_songs:
            exclude_list = [f"{song['title']} by {song['artist']}" for song in exclude_songs]
            user_prompt = f"Suggest 20 songs related to: {prompt}. Please avoid these songs: {', '.join(exclude_list)}"
        else:
            user_prompt = f"Suggest 20 songs related to: {prompt}"

        # Call OpenAI
        api_key = get_openai_api_key()
        if not api_key:
            st.error("❌ OpenAI API key not found.")
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
        song_data = json.loads(content)


        video_ids = []
        song_details = []


        for song in song_data:
            title = song.get('title', '')
            artist = song.get('artist', '')
            source = song.get('source', 'Unknown Source')
            yt_url = search_youtube_for_song(title, artist)

            if yt_url:
                extracted_ids = extract_youtube_links(yt_url)
                if extracted_ids:
                    video_ids.append(extracted_ids[0])
                    song_details.append({
                        'title': title,
                        'artist': artist,
                        'source': source,
                        'video_id': extracted_ids[0]
                    })

        

        st.session_state.song_details = song_details
        return video_ids[:20]

    except json.JSONDecodeError:
        st.error("❌ Couldn't parse song list. Try again.")
        return []

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
                st.warning("⚠️ This video may not be available. Skip to the next song...")
                st.markdown('</div>', unsafe_allow_html=True)
            

            
            # Play and reveal buttons - centered
            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
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
            st.markdown('</div>', unsafe_allow_html=True)
            
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
            
            # Play button for manual control - centered
            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
            if st.button("▶️ Play Song", key="play_current", use_container_width=True):
                st.session_state.selected_video = current_video['video_id']
                st.session_state.current_song_number = current_index + 1
                st.session_state.auto_play = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
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
        
        # Display video using iframe
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
        
        # Alternative: Direct link - more prominent
        st.markdown("---")
        
        # Try next song button
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        if st.button("🔄 Try Next Song", key="try_next", use_container_width=True):
            if current_index < total_songs - 1:
                st.session_state.current_song_index = current_index + 1
                st.session_state.selected_video = st.session_state.videos[current_index + 1]['video_id']
                st.session_state.current_song_number = current_index + 2
                st.session_state.auto_play = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # YouTube link section
        st.markdown('<div style="text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin: 20px 0;">', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #ff6b6b;">🎬 Open in YouTube</h3>', unsafe_allow_html=True)
        st.markdown('<p><strong>If the video doesn\'t play, try opening it directly on YouTube:</strong></p>', unsafe_allow_html=True)
        st.markdown('<a href="https://www.youtube.com/watch?v=' + video_id + '" target="_blank" style="background-color: #ff0000; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">▶️ Open in YouTube</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        

        # Close button
        if st.button("❌ Close Player"):
            del st.session_state.selected_video
            st.rerun()



if __name__ == "__main__":
    main() 

###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################