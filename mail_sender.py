import env
import smtplib
import ssl

def send_mail(receivers: list[str], subject: str, text: str):
    port = 465 
    smtp_server = "smtp.gmail.com"
    sender_email = "hansaFlexMonitoring@gmail.com"
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, env.password)
        server.sendmail(sender_email, receivers, f"Subject: {subject}\n\n{text}")