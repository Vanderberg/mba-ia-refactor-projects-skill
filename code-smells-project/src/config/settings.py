import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
DB_PATH = os.environ.get("DB_PATH", "loja.db")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
