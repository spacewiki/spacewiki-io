#!/usr/bin/env python
from flask.ext.script import Manager, Shell, Server
from spacewiki_io import app, model
import logging
import colorlog

APP = app.create_app()
MANAGER = Manager(APP)
MANAGER.add_command('shell', Shell())
MANAGER.add_command('runserver', Server())

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
