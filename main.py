import glob
import os
import Pyro4

from bs4 import BeautifulSoup
from flask import Flask
from flask import render_template
from flask import request
from chord import *
from ckey import hash
from api import set_to_dht, get_to_dht, get_all

import forms

app = Flask(__name__)

cwd = os.getcwd()

@app.route("/")
def index():
    title = "Index"
    return render_template("index.html", title=title)


@app.route("/new_widget", methods=['GET', 'POST'])
def new_widget():

    os.chdir(cwd)
    os.chdir("widgets")
    widget = forms.Widget(request.form)
    if request.method == 'POST' and widget.validate():
        # Local Storage
        folder = open("{}.txt".format(widget.name.data), "w")
        folder.write("{}".format(widget.html.data))
        folder.close()

        # DHT Storge
        data = {
            "key": "{}".format(widget.name.data),
            "data": "{}".format(widget.html.data)
        }
        set_to_dht("PYRO:DHT_2@localhost:10000", data)

    title = "New Widget"
    return render_template("widget.html", title=title, form=widget)


@app.route("/new_page", methods=['GET', 'POST'])
def new_page():

    if request.method == 'POST':
        # os.chdir(cwd)
        # os.chdir("templates")
        # page = open("new_page.html", "w")
        # page.close()
        # data = {
        #
        # }
        # set_to_dht("PYRO:DHT_2@localhost:10000", data)
        pass

    os.chdir(cwd)
    title = "New Page"
    html_head = """
    <html>
    <head></head>
    <body class="container">
    """
    html_doc = """
    <div id="content-area">
    
    </div>
    """

    html_end = """
    </body>
    </html>
    """
    soup = BeautifulSoup(html_doc, 'html.parser').prettify()

    # Search for local widgets
    local_bs4_widgets = []
    os.chdir("widgets")
    for file in glob.glob("*.txt"):
        temp = open("{}".format(file), "r")
        local_bs4_widgets.append({
            "key": "{}".format(file.title().split(".")[0]),
            "data": "{}".format(BeautifulSoup(temp.read(), 'html.parser').prettify())
        })
        temp.close()

    # Search for all widgets
    dht_bs4_widgets = get_all("PYRO:DHT_2@localhost:10000")

    return render_template("page.html", title=title, widgets=dht_bs4_widgets, html_doc=soup,
                           html_head=html_head, html_end=html_end)


@app.route("/pages")
def pages():
    pass


@app.route("/widgets")
def widgets():
    pass


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
