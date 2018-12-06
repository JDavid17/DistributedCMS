import glob
import os
import Pyro4
import json
import urllib3

from bs4 import BeautifulSoup
from flask import Flask
from flask import render_template
from flask import request
# from DHT.chord import ChordNode
from ckey import *
from settings import IP, PORT
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

            <div id="content-area" contenteditable="true">
            """
html_end = """
            </div>
            </body>
            </html>
            """

http = urllib3.PoolManager()

key = ChordKey(IP, PORT)
dht_uri = "PYRO:DHT_{}@{}:{}".format(key.id, key.ip, key.port)


@app.route("/")
def index():
    title = "Index"
    return render_template("index.html", title=title)


@app.route("/new_widget", methods=['GET', 'POST'])
def new_widget():
    # os.chdir(cwd)
    # os.chdir("widgets")
    widget = forms.Widget(request.form)
    if request.method == 'POST' and widget.validate():
        # Local Storage
        # folder = open("{}.txt".format(widget.name.data), "w")
        # folder.write("{}".format(widget.html.data))
        # folder.close()

        # DHT Storge
        data = {
            "key": "{}".format(widget.name.data),
            "type": "widget",
            "data": "{}".format(widget.html.data)
        }
        set_to_dht(dht_uri, widget.name.data, data)

    title = "New Widget"
    return render_template("widget.html", title=title, form=widget)


@app.route("/new_page", methods=['GET', 'POST'])
def new_page():
    page = forms.Page(request.form)
    if request.method == 'POST':
        doc = html_head + page.code.data + html_end
        soup = BeautifulSoup(doc, 'html.parser').prettify()
        # os.chdir(cwd)
        # os.chdir("templates/pages")
        # folder = open("{}.html".format(page.title.data), "w")
        # folder.write("{}".format(soup))
        # folder.close()
        data = {
            "key": "{}".format(page.title.data),
            "type": "page",
            "data": "{}".format(soup)
        }
        set_to_dht(dht_uri, page.title.data, data)

    # os.chdir(cwd)
    title = "New Page"
    # soup = BeautifulSoup(html_doc, 'html.parser').prettify()

    # # Search for local widgets
    # local_bs4_widgets = []
    # os.chdir("widgets")
    # for file in glob.glob("*.txt"):
    #     temp = open("{}".format(file), "r")
    #     local_bs4_widgets.append({
    #         "key": "{}".format(file.title().split(".")[0]),
    #         "type": "widget",
    #         "data": "{}".format(BeautifulSoup(temp.read(), 'html.parser').prettify())
    #     })
    #     temp.close()

    # Search for all widgets
    dht_bs4_widgets = get_all(dht_uri, str_widget)
    return render_template("page.html", form=page, title=title, widgets=dht_bs4_widgets)


@app.route("/pages")
def pages():
    title = "Pages"
    r = http.request('GET', 'http://localhost:5000/pages.json')
    # print("status " + str(r.status))
    # print("data " + str(r.data))
    content = json.loads(r.data.decode('utf-8'))

    return render_template("pages.html", pages=content, title=title)


# @app.route("/widgets", methods=['GET', 'POST'])
# def widgets():
#     title = "Widgets"
#     r = http.request('GET', 'http://localhost:5000/widgets.json')
#     print("status " + str(r.status))
#     print("data " + str(r.data))
#     content = json.loads(r.data.decode('utf-8'))
#
#     return render_template("widget.html", title=title, widgets=content)


####################### API Stuff ####################################

@app.route("/pages.json", methods=['GET', 'POST'])
def pages_json():
    tipo = 'page'

    if request.method == 'POST':
        # print("checking json: " + str(request.is_json))
        resp = request.get_json()
        id = resp['id']
        key = resp['key']
        data = resp['data']
        type = resp['type']
        with Pyro4.Proxy(dht_uri) as obj:
            pretty_data = BeautifulSoup(data, "html.parser").prettify()
            data = {
                'key': key,
                'type': type,
                'data': pretty_data
            }
            set_to_dht(dht_uri, key, data)

        return json.dumps({'status': 'OK', 'key': key, 'type': type, 'data': data})
    else:
        try:
            with Pyro4.Proxy(dht_uri) as obj:
                pages = obj.get_all(tipo)
                response = app.response_class(
                    response=json.dumps(pages),
                    status=200,
                    mimetype='application/json'
                )
        except Pyro4.errors.CommunicationError:
            print("Unable to Connect to node in URI: {}".format(dht_uri))
    return response


@app.route("/widgets.json", methods=['GET', 'POST'])
def widgets_json():
    tipo = 'widget'
    try:
        with Pyro4.Proxy(dht_uri) as obj:
            widgets = obj.get_all(tipo)
            response = app.response_class(
                response=json.dumps(widgets),
                status=200,
                mimetype='application/json'
            )
    except Pyro4.errors.CommunicationError:
        print("Unable to Connect to node in URI: {}".format(dht_uri))

    return response


####################### API Stuff ####################################


if __name__ == '__main__':
    app.run(debug=True, host='10.6.98.209')
