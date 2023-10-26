import re
import firebase_helper 
import vars_helper
from messaging import send_prompt
import transcription 
import upload_voice 
import prompt_fetch
#todo check participantData modifications ; participantData shouldn't be reassigned in functions 

async def handlePromptResponse(context, body, mediaUrl, participantRef, participantData):
    lastPromptId = participantData["used_prompts"][-1]
    
    if participantData["type"] == "Transcriber":
        if not body:
            msg = vars_helper.get_var("transcription-instructions")
            print("User did not include transcription text")
            await send_prompt.sendPrompt(context, participantData["phone"], msg, True)
            return
        await transcription.addTranscription(participantRef, participantData, lastPromptId, body)
    else:
        if not mediaUrl:
            audio = vars_helper.get_var("voice-note-required-audio")
            print("User did not include voice note")
            await send_prompt.sendPrompt(context, participantData["phone"], audio, False)
            return
        upload_voice.uploadVoice(context, lastPromptId, mediaUrl, participantRef, participantData)
    
    participantData["answered"] += 1
    participantData["status"] = "Completed" if participantData["answered"] + 1 >= participantData["number_questions"] else "Ready"
    print(f"Next participant status is: {participantData['status']}")
    
    if participantData["status"] != "Completed":
        print("User not yet done. Sending next prompt")
        await handleSendPrompt(context, participantData)
    else:
        print("User has completed all prompts")

async def handleSendPrompt(context, participantData):
    isTranscription = (participantData["type"] == "Transcriber")
    
    try:
        if isTranscription:
            fetchedPrompt = await transcription.getNextPrompt(participantData["transcribed_responses"], participantData["language"])
        else:
            fetchedPrompt = await prompt_fetch.getNextPrompt(participantData["used_prompts"])
    except Exception as e:
        if str(e) == 'NoMorePromptError':
            return
        else:
            raise e
    
    positionString = f"{fetchedPrompt['position']}/{participantData['number_questions']}"
    
    print(f"Sending {fetchedPrompt['type']} prompt {fetchedPrompt['content']}")
    await send_prompt.sendPrompt(context, participantData['phone'], positionString, True)
    await send_prompt.sendPrompt(context, participantData['phone'], fetchedPrompt['content'], fetchedPrompt['type'] == 'Text')
    
    usedIDsArrayName = "transcribed_responses" if isTranscription else "used_prompts"
    participantData[usedIDsArrayName].append(fetchedPrompt['id'])
    participantData["status"] = "Prompted"
    print("Setting participant status to 'Prompted'")

async def handler(context, event):
    participantPhone = re.sub(r'\D+', '', event['From'])
    
    try:
        participantRef = await firebase_helper.getParticipantDocRef(participantPhone, True)
        participantSnapshot = await participantRef.get()
    
        if not participantSnapshot.exists:
            print("Participant not registered")
            audio = vars_helper.get_var("not-registered-audio")
            await send_prompt.sendPrompt(context, participantPhone, audio, False)
        else:
            participantData = participantSnapshot.to_dict()

            if participantData is None: #Redundant but whatever python won't let me do otherwise
                print("Participant not registered")
                audio = vars_helper.get_var("not-registered-audio")
                await send_prompt.sendPrompt(context, participantPhone, audio, False)
                return None

            print(f"Participant status is {participantData['status']}")
            
            if participantData["status"] == "Consented":
                print(f"Sending consent message for participantData type: {participantData['type']}")
                if participantData["type"] == "Transcriber":
                    text = vars_helper.get_var("transcription-instructions")
                    await send_prompt.sendPrompt(context, participantPhone, text, True)
                else:
                    audio = vars_helper.get_var("consent-audio")
                    await send_prompt.sendPrompt(context, participantPhone, audio, False)
            
            if participantData["status"] == "Prompted":
                print("Processing prompt response")
                await handlePromptResponse(context, event['Body'], event['MediaUrl0'], participantRef, participantData)
            elif participantData["status"] in ["Ready", "Consented"]:
                print("Sending the next prompt")
                await handleSendPrompt(context, participantData)
            
            if participantData["status"] == "Completed":
                print("Sending the closing message")
                surveyCompletedAudio = vars_helper.get_var("survey-completed-audio")
                await send_prompt.sendPrompt(context, participantPhone, surveyCompletedAudio, False)
            
            print("Saving changes to the participant document in the firestore.")
            await participantRef.update(participantData)
            print("Successfully updated participant data in firestore")
    except Exception as e:
        print(e)
        audio = vars_helper.get_var("error-message-audio")
        await send_prompt.sendPrompt(context, participantPhone, audio, False)
    
    print("the end")
    return None
