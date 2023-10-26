from firebase_helper import getTranscriptionsCollectionRef, getResponsesCollectionRef, getResponsesCollectionRef
from google.cloud.firestore_v1.field_path import FieldPath
from google.cloud.firestore_v1.transforms import Increment
from vars_helper import get_var
import random
import datetime


async def addTranscription(participantRef, participantData, responseId, text):
    try:
        transcriptionsCol = getTranscriptionsCollectionRef()
        responsesCol = getResponsesCollectionRef()
        language = get_var("transcription-language")

        # Add transcription row.
        print("Adding transcription document to database")
        (_, doc_ref) = await transcriptionsCol.add({
            "creation_date": datetime.datetime.now().isoformat(),
            "transcriber_path": participantRef.path,
            "target_language": language,
            "text": text,
            "status": "New",
            "response_path": responsesCol.document(responseId).path
        })
        print("Transcription document successfully added")

        participantData["transcribed_responses"].append(doc_ref.id)

        print("Updating transcription count in the response document")
        await responsesCol.document(responseId).update({
            f"transcription_counts.{language}": Increment(1),
        })
        print("Response document successfully updated")
    except Exception as e:
        print("An error occurred:", e)


async def getNextPrompt(transcribedResponses, language):
    try:
        # Identify and get unused prompts.
        respColRef = getResponsesCollectionRef()

        max_transcriptions = get_var("transcriptions-per-response")
        if (max_transcriptions is None):
            raise Exception("Variable error in assets/vars.json")

        if len(transcribedResponses) > 2:
            start_at = {FieldPath.document_id(
            ): random.choice(transcribedResponses)}
            # ? doc says it can't be "not-in" but looking into it there is no limitation to it and it seems it can effectively be used
            not_transcribed_resps_query_1 = respColRef.order_by(FieldPath.document_id(), direction='ASCENDING').start_at(start_at).where(
                FieldPath.document_id(), "not-in", transcribedResponses).where(f"transcription_counts.{language}", "<", int(max_transcriptions)).limit(1)
            not_transcribed_resps_query_2 = respColRef.order_by(FieldPath.document_id(), direction='DESCENDING').start_at(start_at).where(
                FieldPath.document_id(), "not-in", transcribedResponses).where(f"transcription_counts.{language}", "<", int(max_transcriptions)).limit(1)
        else:
            random_dummy_doc = respColRef.document()
            not_transcribed_resps_query_1 = respColRef.order_by(FieldPath.document_id(), direction='ASCENDING').where(FieldPath.document_id(), "<=", random_dummy_doc.id).where(
                FieldPath.document_id(), "not-in", transcribedResponses).where(f"transcription_counts.{language}", "<", int(max_transcriptions)).limit(1)
            not_transcribed_resps_query_2 = respColRef.order_by(FieldPath.document_id(), direction='DESCENDING').where(FieldPath.document_id(), "<=", random_dummy_doc.id).where(
                FieldPath.document_id(), "not-in", transcribedResponses).where(f"transcription_counts.{language}", "<", int(max_transcriptions)).limit(1)
            await random_dummy_doc.delete()

        suitable_transcriptions = [p async for p in not_transcribed_resps_query_1.stream()]

        if not suitable_transcriptions:
            suitable_transcriptions = [p async for p in not_transcribed_resps_query_2.stream()]

        if suitable_transcriptions:
            random_transcription = suitable_transcriptions[0]
            result = {
                "type": "audio",
                "content": random_transcription.get("storage_link"),
                "id": random_transcription.id,
                "position": len(transcribedResponses) + 1
            }
            return result
        else:
            print(
                "All available prompts have been seen by this user. Please add more to continue")
            raise Exception('NoMorePromptError')
    except Exception as e:
        raise e
