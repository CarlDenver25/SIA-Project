
from gmail_sender import send_email

recipient = input("Enter recipient email: ")
subject = input("Enter subject: ")
body = input("Enter message: ")

success, result = send_email(
    recipient,
    subject,
    body
)

if success:
    print("SUCCESS:", result)
else:
    print("FAILED:", result)