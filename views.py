import re
import flask

import utils

from app import app
from models import Note, FTSNote, Category, NoteCategory, MD

@app.route("/", methods=["GET", "POST"])
@app.route("/page/<int:page>", methods=["GET", "POST"])
def index(page=1):
    per_page = flask.current_app.config["PER_PAGE"]
    number_of_notes = len(list(Note))
    pages = number_of_notes // per_page + (number_of_notes % per_page > 0)

    # TODO: Select category

    form = dict(flask.request.form)
    cids = []
    if "apply_filter" in list(form):
        form.pop("apply_filter")
        cids = [
            int(re.match("category:([0-9]*)", category).group(1))
            for category in list(form)
        ]

    categories = utils.categories(cids=cids)
    keywords = flask.request.form.get("search", "", type=str)
    notes = Note.search(keywords)

    if not notes:
        notes = Note.public()

    nids = []
    for note in notes:
        # TODO: Better solution for deleting all empty notes
        if not note.title and not note.content:
            note.delete_instance()

        # TODO: Improve filtering of notes
        if all([
            NoteCategory.select().where(
                NoteCategory.note == note.id,
                NoteCategory.category == cid,
            ).exists() for cid in cids
        ]):
            nids.append(note.id)

    # Filter notes
    notes = notes.where(Note.id.in_(nids))

    return flask.render_template(
        "index.html",
        notes=notes.paginate(page, per_page),
        page=page,
        pages=pages,
        categories=categories,
        keywords=keywords,
    )

@app.route("/save/<int:nid>", methods=["POST"])
def save_note(nid):

    form = dict(flask.request.form)
    title = form.pop("note-title", [""])
    content = form.pop("note-content", [""])
    form.pop("categories-input")
    categories = form

    Note.update(
        title=title[0],
        content=content[0],
    ).where(Note.id == nid).execute()
    FTSNote.store_note(Note.get(Note.id == nid))

    NoteCategory.delete().where(NoteCategory.note == nid).execute()
    for category in list(categories):
        cid = int(re.match("category:([0-9]*)", category).group(1))
        NoteCategory.create(note=nid, category=cid)

    return flask.redirect(flask.url_for("index"))

@app.route("/delete/<int:nid>", methods=["GET"])
def delete_note(nid):
    try:
        note = Note.get(Note.id == nid)
    except Note.DoesNotExist:
        flask.abort(404)

    note.delete_instance()
    if FTSNote.select().where(FTSNote.docid == note.id).exists():
        FTSNote.get(FTSNote.docid == note.id).delete_instance()

    return flask.redirect(flask.url_for("index"))

@app.route("/new", methods=["GET"])
def new_note():
    note = Note.create(
        title="",
        content="",
    )

    categories = utils.categories()
    return flask.render_template(
        "edit.html",
        note=note,
        categories=categories,
        new=True
    )

@app.route("/edit/<int:nid>", methods=["GET"])
def edit_note(nid):
    try:
        note = Note.get(Note.id == nid)
    except Note.DoesNotExist:
        flask.abort(404)

    categories = utils.categories(nid=nid)
    return flask.render_template("edit.html", note=note, categories=categories)

@app.route("/add_categories", methods=["POST"])
def add_categories():
    new_categories = {}
    categories_input = flask.request.form.get("categories-input", "", type=str)

    for name in categories_input.split(";"):
        name = name.strip()
        if not name:
            break
        if not Category.select().where(Category.name == name).exists():
            category = Category.create(name=name)
            new_categories[str(category.id)] = category.name

    return flask.jsonify(**new_categories)

@app.route("/get_note", methods=["POST"])
def get_note():

    title = MD.convert(flask.request.form.get("note-title", "", type=str))
    content = MD.convert(flask.request.form.get("note-content", "", type=str))

    return flask.jsonify({
        "title": flask.Markup(title),
        "content": flask.Markup(content),
    })

@app.route("/categories")
def edit_categories():

    categories = Category.public()
    notes = utils.notesPerCategory(categories)

    return flask.render_template(
        "categories.html",
        categories=categories,
        notes=notes,
    )

@app.route("/delete_categories", methods=["POST"])
def delete_categories():

    for category in list(flask.request.form):
        cid = int(re.match("category:([0-9]*)", category).group(1))
        Category.get(Category.id == cid).delete_instance()
        if NoteCategory.select().where(NoteCategory.category == cid).exists():
            NoteCategory.get(NoteCategory.category == cid).delete_instance()

    return flask.jsonify({"status": "success"})
