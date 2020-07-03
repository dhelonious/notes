import sys
sys.path.insert(0, ".")

from models import db, FTSNote, Note

with db.atomic():
    FTSNote.create_table()
    for note in Note.select():
        FTSNote.store_note(note)