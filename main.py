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

str_page = 'page'
str_widget = 'widget'
html_head = """
            <html>
            <head></head>
            <body class="container">

            <div id="content-area">
            """
html_end = """
            </div>
            </body>
            </html>
            """


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
            "type": "widget",
            "data": "{}".format(widget.html.data)
        }
        set_to_dht("PYRO:DHT_2@localhost:10000", widget.name.data, data)

    title = "New Widget"
    return render_template("widget.html", title=title, form=widget)


@app.route("/new_page", methods=['GET', 'POST'])
def new_page():
    page = forms.Page(request.form)
    if request.method == 'POST':
        doc = html_head + page.code.data + html_end
        soup = BeautifulSoup(doc, 'html.parser').prettify()
        os.chdir(cwd)
        os.chdir("templates/pages")
        folder = open("{}.html".format(page.title.data), "w")
        folder.write("{}".format(soup))
        folder.close()
        data = {
            "key": "{}".format(page.title.data),
            "type": "page",
            "data": "{}".format(soup)
        }
        set_to_dht("PYRO:DHT_2@localhost:10000", page.title.data, data)
        pass

    os.chdir(cwd)
    title = "New Page"
    # soup = BeautifulSoup(html_doc, 'html.parser').prettify()

    # Search for local widgets
    local_bs4_widgets = []
    os.chdir("widgets")
    for file in glob.glob("*.txt"):
        temp = open("{}".format(file), "r")
        local_bs4_widgets.append({
            "key": "{}".format(file.title().split(".")[0]),
            "type": "widget",
            "data": "{}".format(BeautifulSoup(temp.read(), 'html.parser').prettify())
        })
        temp.close()

    # Search for all widgets
    dht_bs4_widgets = get_all("PYRO:DHT_2@localhost:10000", str_widget)
    return render_template("page.html", form=page, title=title, widgets=dht_bs4_widgets)


@app.route("/pages")
def pages():
    # Local Pages
    title = "Pages"
    os.chdir(cwd)
    os.chdir("templates/pages")
    print(os.getcwd())
    local_bs4_pages = []
    for file in glob.glob("*.html"):
        temp = open("{}".format(file), "r+")
        local_bs4_pages.append({
            "key": "{}".format(file.title().split(".")[0]),
            "type": "page",
            "data": "{}".format(BeautifulSoup(temp.read(), "html.parser").prettify())
        })
        temp.close()

    # DHT Pages
    dht_pages = get_all("PYRO:DHT_2@localhost:10000", str_page)

    pages = []
    for item in local_bs4_pages:
        pages.append(item)

    for item in dht_pages:
        if not pages.__contains__(dht_pages[item]):
            pages.append(dht_pages[item])

    print(pages)
    return render_template("pages.html", title=title, pages=pages)

@app.route("/edit_page", methods=['GET', 'POST', 'PATCH', 'UPDATE'])
def edit_page():
    request_page = request.args.get('key', 'Error encontrando la pagina')
    title = "Edit Page"
    temp_page = forms.Page(request.form)
    if request_page != 'Error encontrando la pagina':
        if request.method == 'PATCH':
            os.chdir(cwd)
            os.chdir('templates')
            file = open("edit_page.html", "r+")
            pass

    return render_template("edit_page.html", title=title)

@app.route("/widgets")
def widgets():
    pass


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
