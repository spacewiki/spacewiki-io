"""Code that runs spacewiki.io"""
import dispatcher
import settings as SETTINGS

application = dispatcher.SubdomainDispatcher(SETTINGS.IO_DOMAIN)
