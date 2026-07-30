import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["GOOGLE_API_KEY"] = "test-key-1,test-key-2"
os.environ["LLM_FALLBACK_CHAIN"] = "gemini-2.0-flash,gemini-1.5-pro"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_ALGORITHM"] = "HS256"
