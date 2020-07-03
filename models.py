import re

from flask import Markup
from markdown import Markdown
from peewee import Model, TextField, IntegerField
from playhouse.sqlite_ext import FTSModel, SearchField

from app import db

MD = Markdown(
    extensions=["mdx_math"],
    extension_configs={
        "mdx_math": {"enable_dollar_delimiter": True}
    },
)

class Category(Model):
    name = TextField()

    class Meta:
        database = db

    @classmethod
    def public(cls):
        return Category.select()

class Note(Model):
    title = TextField()
    content = TextField()

    class Meta:
        database = db

    def save(self, *args, **kwargs):
        print("SAVE", self)
        saved = super(Note, self).save(*args, **kwargs)
        FTSNote.store_note(self)
        return saved

    def delete_instance(self, *args, **kwargs):
        print("DELETE", self)
        deleted = super(Note, self).delete_instance(*args, **kwargs)
        FTSNote.get(FTSNote.docid == self.id).delete_instance()
        return deleted

    def html_title(self):
        html = MD.convert(self.title)
        return Markup(html)

    def html_content(self):
        html = MD.convert(self.content)
        return Markup(html)

    @classmethod
    def public(cls):
        return Note.select()

    @classmethod
    def search(cls, search_term):
        words = [word.strip() for word in search_term.split() if word]
        if not words:
            return Note.select().where(Note.id == 0)
        else:
            search = " ".join(words)

        rank = FTSNote.rank(2.0, 1.0)
        return (Note
                .select(Note, rank.alias("score"))
                .join(FTSNote, on=(Note.id == FTSNote.docid))
                .where(FTSNote.match(search))
                .order_by(rank))

class FTSNote(FTSModel):
    HTML_RE = re.compile("<.+?>")

    title = SearchField()
    content = SearchField()

    class Meta:
        database = db
        options = { "content": Note.content }

    @classmethod
    def public(cls):
        return FTSNote.select()

    @classmethod
    def store_note(cls, note):
        title = FTSNote.HTML_RE.sub("", note.html_title())
        try:
            FTSNote.get(FTSNote.docid == note.id)
        except FTSNote.DoesNotExist:
            FTSNote.create(docid=note.id, title=title)
        else:
            FTSNote.update(title=title).where(FTSNote.docid == note.id).execute()

class NoteCategory(Model):
    note = IntegerField()
    category = IntegerField()

    class Meta:
        database = db
