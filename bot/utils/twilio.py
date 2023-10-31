from django.conf import settings

from twilio.rest import Client


def send_whatsapp_message(send_from, send_to, body):
    # send_from and send_to are WhatsApp numbers, in the format 'whatsapp:+14155238886'
    # body is the message to be sent

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_TOKEN
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        from_=send_from,
        body=body,
        to=send_to
    )
    return message
