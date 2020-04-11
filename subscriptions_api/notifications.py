from django.core.mail import EmailMultiAlternatives


class EmailNotification:
    """A simple class to send email notification from subscription"""

    def __init__(self, subscription, notification, **kwargs):
        self.subscription = subscription
        self.kwargs = kwargs
        self.notification = notification
        self.msg = EmailMultiAlternatives(
            subject=self.get_subject(),
            body=self.get_body(),
            from_email=self.get_from_email(),
            to=self.get_to_email(),
        )

    def get_subject(self):
        """Override and return email subject"""
        return ""

    def get_body(self):
        """Override and return email body"""
        return ""

    def get_from_email(self):
        """Override and return from email default to email from settings"""
        return None

    def get_to_email(self):
        """Override and return to email returns email of user linked to subscription"""
        return [self.subscription.user.email]

    def get_attachment_file(self):
        """Return list of attachment file paths"""
        return None

    def get_attachment(self):
        """Return tuple containing filename, filecontent and mime type"""
        return None

    def get_html_content(self):
        """Return html content to send html version of email"""
        return None

    def attach_file(self):
        files = self.get_attachment_file()
        attachment = self.get_attachment()
        if files:
            if not isinstance(files, list):
                files = [files]
            for file in files:
                self.msg.attach_file(file)
        if isinstance(attachment, tuple):
            self.msg.attach(*attachment)

    def attach_html_content(self):
        html = self.get_html_content()
        if html:
            self.msg.attach_alternative(html, "text/html")

    def extra_process(self):

        self.attach_html_content()
        self.attach_file()

    def fail_silently(self):
        return True

    def send(self):
        self.extra_process()
        self.msg.send(fail_silently=self.fail_silently())
