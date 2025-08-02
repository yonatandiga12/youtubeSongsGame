import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# App Configuration
APP_TITLE = "YouTube Video Game"
APP_ICON = "🎵"
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 500
TEMPERATURE = 0.7
MAX_VIDEOS = 10

# YouTube Configuration
YOUTUBE_SEARCH_LIMIT = 10

# UI Configuration
MAIN_COLOR = "#FF6B6B"
SECONDARY_COLOR = "#4ECDC4" 