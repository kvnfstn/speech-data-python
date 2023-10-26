from twilio.rest import Client
from vars_helper import getVar
from exponential_backoff import backOff

async def sendPrompt(context, recipient, content, isText):
    try:
        varsPath = Runtime.getFunctions()["vars_helper"].path
        varsHelper = require(varsPath)
        whatsappNumber = varsHelper.getVar("whatsapp-number")

        body = content if isText else ""
        media_url = content if not isText else None

        recipient = recipient if recipient.startswith("whatsapp") else f"whatsapp:{recipient if recipient.startswith('+') else '+' + recipient}"
        from_number = f"whatsapp:{whatsappNumber}"

        request = {
            "to": recipient,
            "from": from_number,
            "body": body,
            "media_url": media_url,
        }

        print(f"Sending WhatsApp request: {request}")
        await backOff(lambda: context.getTwilioClient().messages.create(**request))
        print(f"Done sending WhatsApp request: {request}")
    except Exception as e:
        print(e)
        raise e
