"""Code that runs spacewiki.io"""
import dispatcher, app
import logging
from logging.handlers import SMTPHandler
import settings as SETTINGS

logging.basicConfig(level=logging.WARNING)
admin_emails = getattr(SETTINGS, "ADMIN_EMAILS", None)
if admin_emails is not None:
    mail_handler = SMTPHandler('127.0.0.1',
                               'server-error@spacewiki.io',
                               admin_emails, "SpaceWiki Crash!")
    mail_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(mail_handler)
else:
    logging.warn("No error reporting email is set!")

application = dispatcher.SubdomainDispatcher('spacewiki.io')
