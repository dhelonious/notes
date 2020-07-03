from models import Category, NoteCategory

def categories(nid=None, cids=[]):
    categories = {}
    for category in Category.public():
        categories[category.id] = (
            category.name,
            NoteCategory.select().where(
                NoteCategory.note == nid,
                NoteCategory.category == category.id,
            ).exists() or category.id in cids,
        )
    return categories

def notesPerCategory(categories):
    return {
        category.name: len(NoteCategory.select()
                           .where(NoteCategory.category == category).execute())
        for category in categories
    }
