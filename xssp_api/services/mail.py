from smtplib import SMTP
from email.mime.text import MIMEText


class MailService:
    def __init__(self, smtp_hostname=None):
        self.smtp_hostname = smtp_hostname

    def send(self, subject, sender, recipients, body):

        if self.smtp_hostname is None:
            raise RuntimeError("smtp hostname is not set")

        message = MIMEText(body.encode('utf-8'), _charset='utf-8')
        message['From'] = sender
        message['To'] = ';'.join(recipients)
        message['Subject'] = subject

        with SMTP(self.smtp_hostname) as smtp:
            smtp.sendmail(sender, recipients, message.as_string())


mail = MailService()
