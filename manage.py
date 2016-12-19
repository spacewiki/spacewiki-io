#!/usr/bin/env python
from flask_script import Manager, Shell, Server
from spacewiki_io import app, model, dispatcher
import logging
import colorlog
import os
import spacewiki_io.settings as SETTINGS

APP = app.create_app()
MANAGER = Manager(APP)
MANAGER.add_command('shell', Shell())

@MANAGER.command
def runserver():
    from gevent.wsgi import WSGIServer
    app = dispatcher.SubdomainDispatcher(SETTINGS.IO_DOMAIN)
    serv = WSGIServer(('', int(os.environ.get('PORT', 5000))), app, log=logging.getLogger("http"))
    serv.serve_forever()

@MANAGER.command
def reset():
    model.get_db()
    model.Space.delete()
    syncdb()

@MANAGER.command
def syncdb():
    model.get_db()
    model.ADMIN_DATABASE.create_tables([model.Space], True)

if __name__ == "__main__":
    MANAGER.run()
