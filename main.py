from app import app

import views
import models

if __name__ == "__main__":
    models.Note.create_table(True)
    models.FTSNote.create_table(True)
    models.FTSNote.optimize()
    models.Category.create_table(True)
    models.NoteCategory.create_table(True)
    app.run(port=5013)
