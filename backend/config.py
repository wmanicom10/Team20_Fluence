import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    # Flask
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Frontend integration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")


    # Baseline AI pipeline
    AI_MODEL_VERSION = os.getenv("AI_MODEL_VERSION", "baseline-v1")
    AI_AUTO_TRAIN_ON_READ = os.getenv("AI_AUTO_TRAIN_ON_READ", "true").lower() == "true"
