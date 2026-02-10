import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    AZURE_DOC_INTEL_ENDPOINT = os.getenv("AZURE_DOC_INTEL_ENDPOINT")
    AZURE_DOC_INTEL_KEY = os.getenv("AZURE_DOC_INTEL_KEY")

    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY")
    FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")

settings = Settings()
