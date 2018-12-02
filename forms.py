from wtforms import Form, StringField, TextAreaField
from wtforms import validators


class Widget(Form):
    name = StringField('name', [
        validators.DataRequired(message="Uno nombre es requerido para el Plugin"),
        validators.length(min=5, max=50, message="Debe tener widget includio en el nombre")
    ])
    html = TextAreaField('html')
    created_by = StringField('created_by')
    save_address = StringField('save_address')
    type = 'widget'

class Page(Form):
    title = StringField('title', [
        validators.DataRequired(message="Uno nombre es requerido para el Plugin"),
        validators.length(min=5, max=50, message="Debe tener Page incluida en el nombre")
    ])
    code = TextAreaField('code')
    type = 'page'
