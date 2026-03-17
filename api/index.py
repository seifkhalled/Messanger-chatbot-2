import sys
import os

# Add root directory to sys.path so we can import from main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Vercel entry point
# This ensures that the FastAPI 'app' is accessible as a serverless function.
