"""Code that runs spacewiki.io"""
import dispatcher, app

application = dispatcher.SubdomainDispatcher('spacewiki.io')
