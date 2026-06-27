import os
import json
import pickle
import base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None

    # Railway: load token from environment variable
    token_b64 = os.environ.get("YOUTUBE_TOKEN_B64")
    if token_b64:
        token_bytes = base64.b64decode(token_b64)
        creds = pickle.loads(token_bytes)
    elif os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
    else:
        raise Exception("No YouTube token found! Run auth locally first.")

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)

def upload_video(video_path, question_data, video_number=1):
    youtube = get_authenticated_service()

    topic = question_data.get("topic", "General Knowledge")
    question = question_data.get("question", "GK Question")

    title = f"GK Quiz #{video_number} | {topic} | {question[:50]}..."
    description = f"""🧠 Daily GK Quiz Question!

📚 Topic: {topic}
❓ Question: {question}

Options:
A. {question_data['options']['A']}
B. {question_data['options']['B']}
C. {question_data['options']['C']}
D. {question_data['options']['D']}

⏳ Think before the timer runs out!
✅ Answer revealed at the end of the video.

👍 Like & Subscribe for daily GK questions!
🔔 Hit the bell icon to never miss a question!

#GKQuiz #GeneralKnowledge #Quiz #MCQ #DailyQuiz #GK #{topic.replace(' ', '')}
"""

    tags = ["GK Quiz", "General Knowledge", "MCQ", "Quiz", "Daily Quiz",
            topic, "India GK", "World GK", "Quiz Questions"]

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")

    print(f"📤 Uploading: {title}")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"✅ Uploaded! https://youtu.be/{video_id}")
    return video_id


def generate_token_locally():
    """Run this ONCE on your local PC to generate token.pickle"""
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)
    with open("token.pickle", "wb") as f:
        pickle.dump(creds, f)

    with open("token.pickle", "rb") as f:
        token_b64 = base64.b64encode(f.read()).decode()
    print("\n✅ token.pickle created!")
    print("\n📋 Copy this for Railway environment variable YOUTUBE_TOKEN_B64:")
    print("-" * 60)
    print(token_b64)
    print("-" * 60)

if __name__ == "__main__":
    generate_token_locally()