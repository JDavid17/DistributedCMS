from flask import Flask
from flask import render_template

import forms

app = Flask(__name__)


@app.route("/")
def index():
    title = "Index"
    return render_template("index.html", title=title)


@app.route("/new_widget")
def new_widget():
    widget = forms.Widget()
    title = "New Widget"
    return render_template("widget.html", title=title, form=widget)


@app.route("/new_page")
def new_page():
    title = "New Page"
    return render_template("page.html", title=title)
