import os, smtplib, ssl
from email.message import EmailMessage

def send(subject, body, attachments=()):
    user, pw = os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD")
    if not (user and pw):
        print("Gmail secrets not set, skipping email")
        return False
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = user, os.getenv("NOTIFY_TO") or user, subject
    msg.set_content(body)
    for path in list(attachments)[:8]:          # keep the email small
        if path.endswith(".pdf") and os.path.exists(path):
            with open(path, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                                   filename=os.path.basename(path))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
            s.login(user, pw.replace(" ", ""))
            s.send_message(msg)
        print("Digest email sent")
        return True
    except Exception as e:
        print("Email failed:", e)
        return False
