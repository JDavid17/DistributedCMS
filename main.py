from flask import Flask
from flask import render_template
from flask import request
from bs4 import BeautifulSoup
from flask_pymongo import PyMongo

import forms

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/CMS"
mongo = PyMongo(app)


@app.route("/")
def index():
    title = "Index"
    return render_template("index.html", title=title)


@app.route("/new_widget", methods=['GET', 'POST'])
def new_widget():
    widget = forms.Widget(request.form)

    if request.method == 'POST' and widget.validate():
        mongo.db.widget.insert({
            "name": "{}".format(widget.name.data),
            "html": "{}".format(widget.html.data)
        })

    title = "New Widget"
    return render_template("widget.html", title=title, form=widget)


@app.route("/new_page")
def new_page():
    title = "New Page"
    widgets = mongo.db.widget.find()
    bs4_widgets = []

    for widget in widgets:
        bs4_widgets.append({
            "name": "{}".format(widget['name']),
            "html": "{}".format(BeautifulSoup(widget['html'], 'html.parser').prettify())
        })

    return render_template("page.html", title=title, widgets=bs4_widgets)

