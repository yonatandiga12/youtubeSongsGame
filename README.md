# 🎵 YouTube Video Game

A fun and interactive Streamlit app that uses ChatGPT to generate personalized YouTube video collections based on your prompts. Discover and play videos directly within the app!

## 🌐 **Live Demo**

🎮 **[Play the YouTube Video Game Now!](https://youtubesongsgame.streamlit.app/)**

---

## ✨ Features

- **AI-Powered Video Discovery**: Uses ChatGPT to find relevant YouTube videos based on your prompts
- **Direct Video Playback**: Watch videos directly within the app using embedded YouTube player
- **Beautiful UI**: Modern, responsive interface with custom styling
- **Fallback System**: If ChatGPT doesn't provide enough links, automatically falls back to YouTube search
- **Video Information**: Displays thumbnails, titles, channels, duration, and view counts
- **Session Management**: Remembers your video collection during the session

## 🚀 Quick Start

### Option 1: Deploy to Streamlit Cloud (Recommended)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit: YouTube Video Game"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository and set main file to `app.py`

3. **Add your API key**
   - In your app's Streamlit Cloud dashboard, go to Settings → Secrets
   - Add your OpenAI API key:
   ```toml
   OPENAI_API_KEY = "your_actual_openai_api_key_here"
   ```

4. **Your app is live!** 🎉

### Option 2: Run Locally

#### Prerequisites
- Python 3.7 or higher
- OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))

#### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd youtubeSongsGame
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**
   
   **Option A: Streamlit Secrets (Recommended)**
   Edit `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your_actual_openai_api_key_here"
   ```
   
   **Option B: Environment file**
   Create a `.env` file:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   **Option C: Manual input**
   Enter it directly in the app's sidebar when running.

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   
   The app will open at `http://localhost:8501`

## 🎮 How to Play

1. **Enter a Prompt**: Describe the type of videos you want (e.g., "songs from movies", "funny cat videos")
2. **Generate Videos**: Click the "Generate Videos" button to get 10 YouTube links
3. **Browse Collection**: View thumbnails and details of all found videos
4. **Play Videos**: Click "Play Video" on any video to watch it directly in the app
5. **Enjoy**: Discover new content based on your interests!

## 💡 Example Prompts

- "songs from movies"
- "funny cat videos"
- "cooking tutorials"
- "gaming highlights"
- "educational content"
- "music covers"
- "travel vlogs"
- "comedy sketches"
- "science experiments"
- "workout routines"

## 🛠️ Technical Details

### Dependencies

- **Streamlit**: Web app framework
- **OpenAI**: ChatGPT API integration
- **youtube-search-python**: YouTube video search and metadata
- **python-dotenv**: Environment variable management
- **requests**: HTTP requests

### Architecture

- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python with OpenAI API and YouTube search
- **Video Player**: Embedded YouTube iframe player
- **Data Flow**: Prompt → ChatGPT → YouTube URLs → Video Metadata → Display

### Key Functions

- `get_youtube_videos_with_chatgpt()`: Uses ChatGPT to find relevant videos
- `extract_youtube_links()`: Extracts video IDs from URLs using regex
- `get_video_info()`: Fetches video metadata from YouTube
- `main()`: Main Streamlit app interface

## 🔧 Configuration

You can customize the app by modifying `config.py`:

- Change the default ChatGPT model
- Adjust temperature and token limits
- Modify the number of videos returned
- Update UI colors and styling

## 🚨 Troubleshooting

### Common Issues

1. **"No videos found"**
   - Check your internet connection
   - Try a different prompt
   - Verify your OpenAI API key is valid

2. **"Error with ChatGPT API"**
   - Ensure your API key is correct
   - Check your OpenAI account has sufficient credits
   - The app will automatically fall back to YouTube search

3. **Videos not playing**
   - Some videos may be restricted or unavailable
   - Try refreshing the page
   - Check if the video is available in your region

### API Limits

- OpenAI API has rate limits and usage costs
- YouTube search has no API key requirement but may have rate limits
- The app includes fallback mechanisms for reliability

## 🤝 Contributing

Feel free to contribute to this project! Some ideas:

- Add more video sources
- Implement video categories/filtering
- Add user accounts and favorites
- Create video playlists
- Add social sharing features

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- OpenAI for providing the ChatGPT API
- Streamlit for the amazing web app framework
- YouTube for the video content
- The open-source community for the various Python packages used

---

**Enjoy discovering new videos with AI! 🎵🎬**