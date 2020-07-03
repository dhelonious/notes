import os

from flask import Flask
from playhouse.sqlite_ext import SqliteExtDatabase

APP_ROOT = os.path.dirname(os.path.realpath(__file__))
DATABASE = os.path.join(APP_ROOT, "notes.db")
# Note: Use only for development
# DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
app.config["PER_PAGE"] = 10

db = SqliteExtDatabase(app.config["DATABASE"], pragmas=[("journal_mode", "wal")])
