import firebase_admin
from firebase_admin import credentials, firestore_async, storage
from google.cloud.firestore_v1.async_document import AsyncDocumentReference
import os
import datetime
from vars_helper import get_var

# Load the Firebase service account private key from a JSON file
service_account_path = os.environ['SERVICE_ACCOUNT_PATH'] # Ensure you set this environment variable

# Initialize the Firebase app
cred = credentials.Certificate(service_account_path)
app = firebase_admin.initialize_app(cred)

# Initialize Firestore and Storage
db = firestore_async.client(app)
bucket = storage.bucket()

def getParticipantsCollectionRef():
    return db.collection('participants')

def getResponsesCollectionRef():
    return db.collection('responses')

def getTranscriptionsCollectionRef():
    return db.collection('transcriptions')

def getPromptsCollectionRef():
    return db.collection('prompts')

async def getParticipantDocRef(participantId, isParticipantPhone):
    try:
        partColRef = getParticipantsCollectionRef()
        if not isParticipantPhone:
            return partColRef.document(participantId)
        else:
            doc_iter = partColRef.where('phone', '==', participantId).stream()
            doc_count = 0
            doc_ref = AsyncDocumentReference()

            async for doc_snapshot in doc_iter:
                doc_count += 1
                doc_ref = doc_snapshot.reference()

            if doc_count == 1:
                return doc_ref
            elif doc_count == 0:
                raise Exception('Document not found with the specified phone number')
            else:
                raise Exception('Multiple documents found with the same phone number')
    except Exception as e:
        raise e
def getResponseDocRef(responseId):
    try:
        return getResponsesCollectionRef().document(responseId)
    except Exception as e:
        raise e

def getStorageBucket():
    try:
        return bucket
    except Exception as e:
        raise e

async def updateParticipantAfterResponse(participantRef, participantData):
    print('Applying change to participant data')
    await participantRef.update(participantData)

async def addParticipantResponse(participantRef, promptId, dlLink, duration):
    print('Adding response to sheet')
    responses_col = getResponsesCollectionRef()
    prompt_col = getPromptsCollectionRef()
    language = get_var('speech-language')

    response_data = {
        'storage_link': dlLink,
        'duration': duration,
        'language': language,
        'participant_path': participantRef.path,
        'prompt_path': prompt_col.document(promptId).path,
        'response_date': datetime.datetime.now().isoformat(),
        'transcription_counts': {
            language: 1
        },
        'status': 'New'
    }

    await responses_col.add(response_data)
