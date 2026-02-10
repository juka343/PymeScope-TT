# import firebase_admin
# from firebase_admin import credentials
# from app.core.config import settings

# def initialize_firebase():
#     if not firebase_admin._apps:
#         cred = credentials.Certificate({
#             "type": "service_account",
#             "project_id": settings.FIREBASE_PROJECT_ID,
#             "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
#             "client_email": settings.FIREBASE_CLIENT_EMAIL,
#             "token_uri": "https://oauth2.googleapis.com/token",
#         })
#         firebase_admin.initialize_app(cred)
