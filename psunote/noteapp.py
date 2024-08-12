import flask
from flask import render_template, flash, redirect, request
import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


@app.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
def edit_note(note_id):
    note = models.Note.query.get_or_404(note_id)
    tags_string = ''.join([tag.name for tag in note.tags])
    tags_string = [tag.strip() for tag in tags_string.split(',')]

    form = forms.NoteForm(obj=note)  
    form.tags.data = tags_string

    if request.method == 'GET':
        tags_string = ''.join([tag.name for tag in note.tags])
        tags_string = [tag.strip() for tag in tags_string.split(',')]
        form.tags.data = tags_string

    if form.validate_on_submit():
        # Update the note with form data
        note.title = form.title.data
        note.description = form.description.data

        note.tags.clear()
        db = models.db
        for name in form.tags.data:
            if name:
                # Get or create the tag
                tag = models.Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = models.Tag(name=name)
                    db.session.add(tag)
                note.tags.append(tag)
        

        db.session.commit()  # Save changes to the database
        flash('Note updated successfully!', 'success')
        return flask.redirect(flask.url_for('index', note_id=note.id))  # Redirect to a relevant page

    return render_template('edit-note.html', form=form)

@app.route('/note/<int:note_id>/delete', methods=['GET','POST'])
def delete_note(note_id):
    db = models.db
    note = db.get_or_404(models.Note, note_id)
    db.session.delete(note)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route('/tag/<tag_name>/edit', methods=["GET", "POST"])
def tags_edit(tag_name):
    db = models.db
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
        ).scalar_one_or_none()

    
    form = forms.TagForm(obj=tag)
    
    if form.validate_on_submit():
        if form.name.data and form.name.data != tag.Tag.name:
            tag.Tag.name = form.name.data
            db.session.commit()
            return flask.redirect(flask.url_for("tags_view", tag_name=tag.Tag.name))

    return flask.render_template("tags-edit.html", form=form, tag=tag)

@app.route("/tags/<tag_name>/delete", methods=["POST"])
def tags_delete(tag_name):
    db = models.db
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
        ).scalar_one_or_none()

    if tag:
        db.session.delete(tag)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
