import streamlit as st
from openai import OpenAI
import json
import re


# Configure OpenAI - only from Streamlit secrets
def get_openai_api_key():
    return st.secrets.get("OPENAI_API_KEY")




# Page configuration
st.set_page_config(
    page_title="Multi-Game Entertainment Hub",
    page_icon="🎮",
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
        text-align: center;
        margin-bottom: 1rem;
    }
    .quote-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        font-size: 1.2rem;
        font-style: italic;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .answer-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        font-size: 1.1rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_video_index' not in st.session_state:
    st.session_state.current_video_index = 0
if 'videos' not in st.session_state:
    st.session_state.videos = []
if 'current_quote_index' not in st.session_state:
    st.session_state.current_quote_index = 0
if 'quotes' not in st.session_state:
    st.session_state.quotes = []
if 'current_frame_index' not in st.session_state:
    st.session_state.current_frame_index = 0
if 'movies' not in st.session_state:
    st.session_state.movies = []
if 'hint_level' not in st.session_state:
    st.session_state.hint_level = 0


# Extract YouTube video IDs from text
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

# Get YouTube videos with ChatGPT
def get_youtube_videos_with_chatgpt(prompt, exclude_songs=None):
    """Use ChatGPT to get song suggestions, then search YouTube for those songs"""
    try:
        # First, use ChatGPT to suggest songs based on the prompt
        system_prompt = """You are a helpful assistant that suggests songs based on user prompts.
        For each suggestion, provide:
        1. The song title
        2. The movie/show/game it's from (if applicable)
        3. The artist/band name
        4. link to youtube - KARAOKE VERSION

        Return the information in this exact JSON format:
        [
            {
                "title": "Song Title",
                "source": "Movie/Show/Game Name",
                "artist": "Artist/Band Name",
                "link": "url link"
            }
        ]

        Return exactly 25 songs. Make sure the JSON is valid and return only the json."""

        # Compose user prompt
        if exclude_songs and isinstance(exclude_songs, list) and len(exclude_songs) > 0 and isinstance(exclude_songs[0], dict):
            exclude_list = [f"{song['title']} by {song['artist']}" for song in exclude_songs]
            user_prompt = f"Suggest 25 songs related to: {prompt}. Please avoid these songs: {', '.join(exclude_list)}"
        else:
            user_prompt = f"Suggest 25 songs related to: {prompt}"

        # Get API key
        api_key = get_openai_api_key()
        if not api_key:
            st.error("OpenAI API key not found in Streamlit secrets!")
            return []

        # Create OpenAI client
        client = OpenAI(api_key=api_key)

        # Make API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )

        # Extract response content
        response_content = response.choices[0].message.content.strip()

        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            json_start = response_content.find('[')
            json_end = response_content.rfind(']') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_content[json_start:json_end]
                songs_data = json.loads(json_str)
            else:
                st.error("No valid JSON found in ChatGPT response")
                return []
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON from ChatGPT response: {e}")
            return []

        # Extract video IDs from links
        video_ids = []
        for song in songs_data:
            if 'link' in song and song['link']:
                ids = extract_youtube_links(song['link'])
                if ids:
                    video_ids.extend(ids)
                    song['video_id'] = ids[0]  # Store the video ID

        return video_ids[:25]  # Return max 25 videos

    except Exception as e:
        st.error(f"Error getting videos: {str(e)}")
        return []

# Get movie quotes with ChatGPT
def get_movie_quotes_with_chatgpt(prompt, exclude_quotes=None):
    """Use ChatGPT to get movie quote suggestions"""
    try:
        # System prompt for movie quotes
        system_prompt = """You are a helpful assistant that suggests famous movie quotes based on user prompts.
        For each suggestion, provide:
        1. The quote text
        2. The movie/show it's from
        3. The character who said it (if known)
        4. The year of the movie/show (if known)

        Return the information in this exact JSON format:
        [
            {
                "quote": "The actual quote text here",
                "movie": "Movie/Show Name",
                "character": "Character Name",
                "year": "Year"
            }
        ]
        
        Return exactly 25 quotes. Make sure the JSON is valid and return only the json."""

        # Compose user prompt
        if exclude_quotes and isinstance(exclude_quotes, list) and len(exclude_quotes) > 0 and isinstance(exclude_quotes[0], dict):
            exclude_list = [f"{quote['quote'][:50]}..." for quote in exclude_quotes]
            user_prompt = f"Suggest 25 famous movie quotes related to: {prompt}. Please avoid these quotes: {', '.join(exclude_list)}"
        else:
            user_prompt = f"Suggest 25 famous movie quotes related to: {prompt}"

        # Get API key
        api_key = get_openai_api_key()
        if not api_key:
            st.error("OpenAI API key not found in Streamlit secrets!")
            return []

        # Create OpenAI client
        client = OpenAI(api_key=api_key)

        # Make API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )

        # Extract response content
        response_content = response.choices[0].message.content.strip()

        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            json_start = response_content.find('[')
            json_end = response_content.rfind(']') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_content[json_start:json_end]
                quotes_data = json.loads(json_str)
            else:
                st.error("No valid JSON found in ChatGPT response")
                return []
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON from ChatGPT response: {e}")
            return []

        return quotes_data[:25]  # Return max 25 quotes

    except Exception as e:
        st.error(f"Error getting quotes: {str(e)}")
        return []

# Get movie frames with ChatGPT
def get_movie_frames_with_chatgpt(prompt, exclude_movies=None):
    """Use ChatGPT to get movie suggestions for frame guessing"""
    try:
        # System prompt for movie frames
        system_prompt = """You are a helpful assistant that suggests famous movies based on user prompts.
        For each suggestion, provide:
        1. The movie title
        2. The year of the movie
        3. A brief description of a memorable scene or frame (with character names)
        4. The genre of the movie
        5. An anonymized version of the scene description (replace character names with "Person A", "Person B", etc.)

        Return the information in this exact JSON format:
        [
            {
                "title": "Movie Title",
                "year": "Year",
                "description": "Brief description of a memorable scene with character names",
                "anonymized_description": "Same scene but with Person A, Person B, etc. instead of names",
                "genre": "Genre"
            }
        ]
        
        Return exactly 25 movies. Make sure the JSON is valid and return only the json."""

        # Compose user prompt
        if exclude_movies and isinstance(exclude_movies, list) and len(exclude_movies) > 0 and isinstance(exclude_movies[0], dict):
            exclude_list = [f"{movie['title']} ({movie['year']})" for movie in exclude_movies]
            user_prompt = f"Suggest 25 famous movies related to: {prompt}. Please avoid these movies: {', '.join(exclude_list)}"
        else:
            user_prompt = f"Suggest 25 famous movies related to: {prompt}"

        # Get API key
        api_key = get_openai_api_key()
        if not api_key:
            st.error("OpenAI API key not found in Streamlit secrets!")
            return []

        # Create OpenAI client
        client = OpenAI(api_key=api_key)

        # Make API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )

        # Extract response content
        response_content = response.choices[0].message.content.strip()

        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            json_start = response_content.find('[')
            json_end = response_content.rfind(']') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_content[json_start:json_end]
                movies_data = json.loads(json_str)
            else:
                st.error("No valid JSON found in ChatGPT response")
                return []
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON from ChatGPT response: {e}")
            return []

        return movies_data[:25]  # Return max 25 movies

    except Exception as e:
        st.error(f"Error getting movies: {str(e)}")
        return []

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">🎮 Multi-Game Entertainment Hub</h1>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🎵 Song Guessing Game", "🎬 Movie Quotes Game", "🎭 Movie Frame Game"])
    
        # Song Guessing Game Tab
    with tab1:
        st.markdown('<h2 class="sub-header">🎵 Song Guessing Game</h2>', unsafe_allow_html=True)
        
        # Prompt input
        prompt = st.text_input(
            "Enter a theme or prompt:",
            placeholder="e.g., 'songs about love', 'Disney songs', '80s rock'",
            key="song_prompt"
        )
        
        # Generate button
        if st.button("Generate Videos", key="generate_songs"):
            if prompt:
                with st.spinner("Generating song suggestions..."):
                    videos = get_youtube_videos_with_chatgpt(prompt, None)
                    if videos:
                        st.session_state.videos = videos
                        st.session_state.current_video_index = 0
                        st.success(f"Generated {len(videos)} song videos!")
                    else:
                        st.error("No videos found. Try a different prompt.")
            else:
                st.warning("Please enter a prompt first.")
        
        # Navigation controls
        if st.session_state.videos:
            st.subheader("Navigation")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("⏮️ Previous", key="prev_song"):
                    if st.session_state.current_video_index > 0:
                        st.session_state.current_video_index -= 1
                        st.rerun()
            
            with col2:
                if st.button("⏭️ Next", key="next_song"):
                    if st.session_state.current_video_index < len(st.session_state.videos) - 1:
                        st.session_state.current_video_index += 1
                        st.rerun()
            
            with col3:
                if st.button("🎯 Reveal", key="reveal_song"):
                    st.rerun()
            
            # Progress indicator
            st.progress(st.session_state.current_video_index / (len(st.session_state.videos) - 1))
            st.caption(f"Video {st.session_state.current_video_index + 1} of {len(st.session_state.videos)}")
        
        # Instructions
        st.markdown("---")
        st.markdown("### How to Play:")
        st.markdown("1. Enter a theme or prompt")
        st.markdown("2. Click 'Generate Videos' to get 25 song links")
        st.markdown("3. Listen to the song and guess the title/artist")
        st.markdown("4. Click 'Reveal' to see the answer")
        st.markdown("5. Use Previous/Next to navigate")
            

        
        # Main content area for song game
        if st.session_state.videos:
            current_index = st.session_state.current_video_index
            current_video_id = st.session_state.videos[current_index]
            
            # Display video
            st.subheader("🎵 Listen and Guess!")
            
            # Warning about video availability
            st.warning("⚠️ Note: Some videos may be unavailable due to regional restrictions or copyright issues.")
            
            # Auto-play video with JavaScript
            st.markdown(f"""
            <div style="margin: 20px 0;">
                <iframe 
                    width="100%" 
                    height="400" 
                    src="https://www.youtube.com/embed/{current_video_id}?autoplay=1&mute=0" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
            """, unsafe_allow_html=True)
            
            # Reveal button functionality
            if st.button("🎯 Reveal Answer", key="reveal_answer_song"):
                st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                st.write("**Song Information:**")
                st.write(f"Title: {current_video_id}")  # You might want to store more info
                st.write("Artist: [To be implemented]")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("👆 Enter a prompt and click 'Generate Videos' to start playing!")
    
        # Movie Quotes Game Tab
    with tab2:
        st.markdown('<h2 class="sub-header">🎬 Movie Quotes Game</h2>', unsafe_allow_html=True)
        
        # Prompt input for quotes
        quote_prompt = st.text_input(
            "Enter a theme or prompt:",
            placeholder="e.g., 'action movies', 'Disney quotes', 'sci-fi films'",
            key="quote_prompt"
        )
        
        # Generate button for quotes
        if st.button("Generate Quotes", key="generate_quotes"):
            if quote_prompt:
                with st.spinner("Generating movie quotes..."):
                    quotes = get_movie_quotes_with_chatgpt(quote_prompt, None)
                    if quotes:
                        st.session_state.quotes = quotes
                        st.session_state.current_quote_index = 0
                        st.success(f"Generated {len(quotes)} movie quotes!")
                    else:
                        st.error("No quotes found. Try a different prompt.")
            else:
                st.warning("Please enter a prompt first.")
        
        # Navigation controls for quotes
        if st.session_state.quotes:
            st.subheader("Navigation")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("⏮️ Previous", key="prev_quote"):
                    if st.session_state.current_quote_index > 0:
                        st.session_state.current_quote_index -= 1
                        st.rerun()
            
            with col2:
                if st.button("⏭️ Next", key="next_quote"):
                    if st.session_state.current_quote_index < len(st.session_state.quotes) - 1:
                        st.session_state.current_quote_index += 1
                        st.rerun()
            
            with col3:
                if st.button("🎯 Reveal", key="reveal_quote"):
                    st.rerun()
            
            # Progress indicator
            st.progress(st.session_state.current_quote_index / (len(st.session_state.quotes) - 1))
            st.caption(f"Quote {st.session_state.current_quote_index + 1} of {len(st.session_state.quotes)}")
        
        # Main content area for movie quotes game
        if st.session_state.quotes:
            current_index = st.session_state.current_quote_index
            current_quote = st.session_state.quotes[current_index]
            
            # Display quote
            st.subheader("🎬 Read and Guess!")
            st.markdown('<div class="quote-box">', unsafe_allow_html=True)
            st.write(f'"{current_quote["quote"]}"')
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Reveal button functionality
            if st.button("🎯 Reveal Answer", key="reveal_answer_quote"):
                st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                st.write("**Movie Information:**")
                st.write(f"Movie: {current_quote.get('movie', 'Unknown')}")
                st.write(f"Character: {current_quote.get('character', 'Unknown')}")
                st.write(f"Year: {current_quote.get('year', 'Unknown')}")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("👆 Enter a prompt in the sidebar and click 'Generate Quotes' to start playing!")
        
        # Instructions for quotes
        st.markdown("---")
        st.markdown("### How to Play:")
        st.markdown("1. Enter a theme or prompt")
        st.markdown("2. Click 'Generate Quotes' to get 25 movie quotes")
        st.markdown("3. Read the quote and guess the movie/character")
        st.markdown("4. Click 'Reveal' to see the answer")
        st.markdown("5. Use Previous/Next to navigate")
    
    # Movie Frame Game Tab
    with tab3:
        st.markdown('<h2 class="sub-header">🎭 Movie Frame Game</h2>', unsafe_allow_html=True)
        
        # Prompt input for movie frames
        frame_prompt = st.text_input(
            "Enter a theme or prompt:",
            placeholder="e.g., 'action movies', 'Disney films', 'sci-fi classics'",
            key="frame_prompt"
        )
        
        # Generate button for movie frames
        if st.button("Generate Movies", key="generate_frames"):
            if frame_prompt:
                with st.spinner("Generating movie suggestions..."):
                    movies = get_movie_frames_with_chatgpt(frame_prompt, None)
                    if movies:
                        st.session_state.movies = movies
                        st.session_state.current_frame_index = 0
                        st.session_state.hint_level = 0  # Reset hint level
                        st.success(f"Generated {len(movies)} movie suggestions!")
                    else:
                        st.error("No movies found. Try a different prompt.")
            else:
                st.warning("Please enter a prompt first.")
        
        # Navigation controls for movie frames
        if st.session_state.movies:
            st.subheader("Navigation")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("⏮️ Previous", key="prev_frame"):
                    if st.session_state.current_frame_index > 0:
                        st.session_state.current_frame_index -= 1
                        st.session_state.hint_level = 0  # Reset hint level
                        st.rerun()
            
            with col2:
                if st.button("⏭️ Next", key="next_frame"):
                    if st.session_state.current_frame_index < len(st.session_state.movies) - 1:
                        st.session_state.current_frame_index += 1
                        st.session_state.hint_level = 0  # Reset hint level
                        st.rerun()
            
            with col3:
                if st.button("🎯 Reveal", key="reveal_frame"):
                    st.rerun()
            
            # Progress indicator
            st.progress(st.session_state.current_frame_index / (len(st.session_state.movies) - 1))
            st.caption(f"Movie {st.session_state.current_frame_index + 1} of {len(st.session_state.movies)}")
        
        # Main content area for movie frame game
        if st.session_state.movies:
            current_index = st.session_state.current_frame_index
            current_movie = st.session_state.movies[current_index]
            
            # Display movie frame placeholder
            st.subheader("🎭 Look and Guess!")
            
            # Show scene description based on hint level
            st.markdown('<div class="quote-box">', unsafe_allow_html=True)
            st.write(f"**Scene Description:**")
            
            if st.session_state.hint_level == 0:
                # Level 0: Anonymized description (Person A, Person B, etc.)
                description = current_movie.get('anonymized_description', current_movie.get('description', 'No description available'))
                st.write(f'"{description}"')
            else:
                # Level 1+: Full description with character names
                description = current_movie.get('description', 'No description available')
                st.write(f'"{description}"')
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Hint buttons with different levels
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💡 Hint 1: Show Names", key="hint1_frame"):
                    st.session_state.hint_level = 1
                    st.rerun()
            
            with col2:
                if st.button("💡 Hint 2: Year & Genre", key="hint2_frame"):
                    st.session_state.hint_level = 2
                    st.rerun()
            
            with col3:
                if st.button("🎯 Reveal Answer", key="reveal_answer_frame"):
                    st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                    st.write("**Movie Information:**")
                    st.write(f"Title: {current_movie.get('title', 'Unknown')}")
                    st.write(f"Year: {current_movie.get('year', 'Unknown')}")
                    st.write(f"Genre: {current_movie.get('genre', 'Unknown')}")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Show hints based on level
            if st.session_state.hint_level >= 1:
                st.info(f"💡 **Hint 1:** Character names are now shown in the description above!")
            
            if st.session_state.hint_level >= 2:
                st.info(f"💡 **Hint 2:** This is a {current_movie.get('genre', 'Unknown')} movie from {current_movie.get('year', 'Unknown')}")
        else:
            st.info("👆 Enter a prompt and click 'Generate Movies' to start playing!")
        
        # Instructions for movie frames
        st.markdown("---")
        st.markdown("### How to Play:")
        st.markdown("1. Enter a theme or prompt")
        st.markdown("2. Click 'Generate Movies' to get 25 movie suggestions")
        st.markdown("3. Read the scene description and guess the movie")
        st.markdown("4. Click 'Reveal' to see the answer")
        st.markdown("5. Use Previous/Next to navigate")

if __name__ == "__main__":
    main() 
