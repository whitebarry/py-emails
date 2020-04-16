import email.message
import mimetypes
import smtplib


class Email:

    def __init__(self, smtp_config, subject=None, body=None, body_type=None, attachments=None):
        self.smtp_config = smtp_config
        self._raise_if_undefined('sender')
        self._raise_if_undefined('host')
        self.subject = subject
        self.body = body
        self.body_type = body_type
        self.attachments = attachments or []


    def send(self, recipients):
        message = self._create_message(recipients)
        host = self.smtp_config['host']
        port = self.smtp_config.get('port', 25)
        password = self.smtp_config.get('password')
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            if password: smtp.login(self.smtp_config['sender'], password)
            smtp.send_message(message)


    def _raise_if_undefined(self, attribute):
        if not self.smtp_config.get(attribute):
            raise InvalidSmtpConfigError(attribute)


    def _create_message(self, recipients):
        message = email.message.EmailMessage()
        message['From'] = self.smtp_config['sender']
        if isinstance(recipients, str): message['To'] = recipients
        else: message['To'] = ', '.join(recipients)
        if self.subject: message['Subject'] = self.subject
        if self.body:
            if self.body_type: message.set_content(self.body, subtype=self.body_type)
            else: message.set_content(self.body)
        self._add_attachments(message)
        return message


    def _add_attachments(self, message):
        for attachment in self.attachments:
            mime_type = self._get_mime_type(attachment)
            maintype, subtype = mime_type.split('/')
            message.add_attachment(
                attachment['content'],
                maintype=maintype,
                subtype=subtype,
                filename=attachment['filename']
            )


    def _get_mime_type(self, attachment):
        mime_type = attachment.get('mime_type')
        if not mime_type:
            mime_type, encoding = mimetypes.guess_type(attachment['filename'])
        if not mime_type:
            raise MimeTypeNotSpecifiedError(attachment['filename'])
        return mime_type


def from_template(template: dict) -> Email:
    smtp_config = template.get('smtp_config')
    if not smtp_config: raise SmtpConfigNotProvidedError()
    subject = template.get('subject')
    body = template.get('body')
    body_type = template.get('body_type')
    attachments = template.get('attachments')
    return Email(smtp_config, subject, body, body_type, attachments)



class InvalidSmtpConfigError(AttributeError):

    def __init__(self, undefined_property):
        self.undefined_property = undefined_property


    def __str__(self):
        return f'Invalid SMTP configuration. Property {self.undefined_property} is required but was not defined'


class SmtpConfigNotProvidedError(AttributeError):

    def __str__(self):
        return 'Email cannot be sent without an SMTP configuration. Please specify it when instantiating a new Email'


class MimeTypeNotSpecifiedError(AttributeError):

    def __init__(self, filename):
        self.filename = filename


    def __str__(self):
        return f'MIME type could not be guessed for {self.filename}\nPlease specify it in the attachment dict'
