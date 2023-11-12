#!/usr/bin/python3.6
import datetime
import json
import smtplib
from email.message import EmailMessage

with open("creds.json", "r") as f:
    creds = json.load(f)

user = creds["email_user"]
passw = creds["email_pass"]


def send_email(device: int, timestamp: str, to: str):
    # Create a text/plain message
    msg = EmailMessage()
    msg.set_content(
        f"""
Motion detected!

This is an automated message from your baby monitor.
Motion was detected from device {device} at {str(datetime.datetime.fromtimestamp(int(timestamp)))}.

You can view this event, as well as past events, at http://localhost:8501.
    """
)

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = f'Alert from Baby Monitor'
    msg['From'] = user
    msg['To'] = to

    # Send the message via gmail's SMTP server.
    server = smtplib.SMTP_SSL('smtp.gmail.com')
    server.ehlo()
    server.login(user, passw)
    server.send_message(msg)


def send_text_email(device: int, timestamp: str, to: str):
    # Create a text/plain message
    msg = EmailMessage()
    msg.set_content(
        f"""
Motion detected!

Motion was detected from device {device} at {str(datetime.datetime.fromtimestamp(int(timestamp)))}.
You can view this event at http://localhost:8501.
""")
    msg['Subject'] = ''
    msg['From'] = user
    msg['To'] = to

    # Send the message via gmail's SMTP server.
    server = smtplib.SMTP_SSL('smtp.gmail.com')
    server.ehlo()
    server.login(user, passw)
    server.send_message(msg)
