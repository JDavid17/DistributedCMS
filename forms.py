from wtforms import Form, StringField, TextAreaField
from wtforms import validators


class Widget(Form):
    name = StringField('name', [
        validators.DataRequired(message="Uno nombre es requerido para el Plugin"),
        validators.length(min=5, max=15, message="Ingrese un nombre valido!!!")
    ])
    html = TextAreaField('html')
    created_by = StringField('created_by')
    save_address = StringField('save_address')
