from wtforms import Form, StringField, TextAreaField


class Widget(Form):
    name = StringField('name')
    html = TextAreaField('html')
    created_by = StringField('created_by')
    save_address = StringField('save_address')
