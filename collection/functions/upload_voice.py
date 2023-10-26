import os
import tempfile
import shutil
import requests
import music_tag
from google.cloud import storage
from vars_helper import getVar
from messaging.send_prompt import sendPrompt
from google_firebase_helper import getStorageBucket, addParticipantResponse

# Create a local directory for staging audio files.
PUBLIC_DIR = os.path.join(tempfile.gettempdir(), "mms_images")
if not os.path.exists(PUBLIC_DIR):
    os.mkdir(PUBLIC_DIR)

def uploadVoice(context, promptId, mediaUrl, participantRef, participantData):
    with requests.get(mediaUrl, stream=True) as response:
        response.raise_for_status()
        file_path = os.path.join(PUBLIC_DIR, f"{participantRef.id}.ogg")

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        duration = extractDuration(file_path)
        minLength = int(getVar("min-audio-length-secs"))

        if duration < minLength:
            tooShortAudio = getVar("voice-note-too-short-audio")
            sendPrompt(context, participantData["phone"], tooShortAudio, False)
            return False
        else:
            print("Adding response: Uploading to storage")
            bucket = getStorageBucket()
            uploaded_file, dl_link = uploadToDirectory(promptId, participantRef.id, file_path, bucket)
            addParticipantResponse(participantRef, promptId, dl_link, duration)
            return participantData["status"] != "Completed"

def uploadToDirectory(promptId, participantId, file_path, bucket):
    print("Uploading response audio")
    destination_path = f"responses/{promptId}/{participantId}.ogg"
    metadata = {"cacheControl": "public, max-age=31536000"}
    
    try:
        blob = bucket.blob(destination_path)
        blob.metadata = metadata
        blob.upload_from_filename(file_path)
        dl_link = blob.generate_signed_url(expiration="2099-01-01", method="GET")
        return blob, dl_link
    except Exception as e:
        raise e

def extractDuration(file_path):
    duration = 0
    try:
        with music_tag.load_file(file_path) as audio:
            duration = audio.duration
    except Exception as e:
        print(e)
    return duration
