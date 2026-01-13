import os
import smtplib
from email.message import EmailMessage
from glob import glob

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

files = glob("*.csv")

msg = EmailMessage()
msg["Subject"] = "NSE Turnover Scanner"
msg["From"] = EMAIL
msg["To"] = EMAIL
msg.set_content("Attached is today's NSE Turnover Scanner CSV file.")

for file in files:
    with open(file, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="octet-stream",
            filename=file
        )

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)

print("Email sent successfully")
