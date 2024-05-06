# System libraries
import asyncio
from collections import OrderedDict
import functools
import json
import os
import time
import threading
# Third party libraries
from flask import Flask, g, render_template, request, send_from_directory, Response
from telegram import Bot
# Local libraries
import app
import startup
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import FileClient
from data_structures.TDPName import TDPName
from MyLogger import logger

flask_app = Flask(__name__, template_folder='webapp/templates', static_url_path='/static', static_folder='webapp/static')

metadata_client, file_client = startup.get_clients()

@flask_app.before_request
def before_request():
    g.file_client = file_client
    g.metadata_client = metadata_client

@flask_app.after_request
def after_request(response):
    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@flask_app.route("/")
def index():
    return "Hello World!!!"

@flask_app.route("/api/tdps")
def api_tdps():
    json_response:str = app.api_tdps()
    flask_response = Response(json_response)
    flask_response.headers['Content-Type'] = "application/json"
    flask_response.headers['Cache-Control'] = "max-age=604800, public"
    return flask_response

def api_tdp(tdp_name:str, is_pdf:bool=False):

    logger.info(f"API TDP {tdp_name} is_pdf={is_pdf}")

    try:
        tdp_name:TDPName = TDPName.from_string(tdp_name)
    except ValueError as e:
        logger.error(f"Invalid TDP Name {tdp_name}")
        raise ValueError(f"Invalid TDP Name {tdp_name}")

    if is_pdf:
        tdp_exists = g.file_client.pdf_exists(tdp_name)
    else:
        tdp_exists = g.file_client.html_exists(tdp_name)
    
    if not tdp_exists:
        logger.error(f"TDP {tdp_name} does not exist")
        raise Exception("TDP does not exist")

    if is_pdf:
        return send_from_directory("static/pdf", tdp_name.to_filepath())
    else:
        return send_from_directory("static/html", tdp_name.to_filepath(ext="html"))

@flask_app.route("/api/tdp/<tdp_name>/pdf")
def api_tdp_pdf(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=True)

    # flask_response.headers['Content-Type'] = "application/json"
    # flask_response.headers['Cache-Control'] = "max-age=604800, public"
    # return flask_response

@flask_app.route("/api/tdp/<tdp_name>/html")
def api_tdp_html(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=False)

@flask_app.route("/api/tdp/<tdp_name>/image/<image_idx>")
def api_tdp_image(tdp_name:str, image_idx:int):
    pass



# @flask_app.route('/TDPs/<year>/<filename>')
# def download_file(year, filename):
#     return send_from_directory(f'TDPs/{year}', filename, as_attachment=True)

# @flask_app.route('/templates/<filename>')
# def static_file(filename):
#     return send_from_directory(f'templates', filename)

# @flask_app.route('/static/logos/<filename>')
# def static_logo(filename):
#     # Check if logo exists, else default logo
#     if os.path.exists('static/logos/' + filename):
#         return send_from_directory('static/logos', filename)
#     else:
#         return send_from_directory('static/logos', '10px.png')

# @flask_app.get("/")
# def homepage():
#     print("Loading homepage")
#     return send_from_directory('webapp/templates', 'index.html')

# @flask_app.get("/tdps/<id>")
# def get_tdps_id(id):
#     try:
#         ref = request.args.get('ref')
#         tdp_db = db_instance.get_tdp_by_id(id)
#         filepath = f"/TDPs/{tdp_db.year}/{tdp_db.filename}"
#         entry_string = db_instance_tdp_views.post_tdp(tdp_db, ref)

#         thread = threading.Thread(target=send_to_telegram, args=[entry_string])
#         thread.start()

#         return render_template('tdp.html', tdp=tdp_db, filepath=filepath)
#     except Exception as e:
#         print(e)
#         # Return generic 404 page
#         return render_template('404.html'), 404


# """ /api/tdps/<tdp_id>/paragraphs """

# @flask_app.get("/api/tdps/<tdp_id>/paragraphs")
# def get_api_tdps_id_paragraphs(tdp_id):
#     tdp = db_instance.get_tdp_by_id(tdp_id)
#     print("[app] Retrieving paragraphs for TDP", tdp.filename)
#     paragraphs = db_instance.get_paragraphs_by_tdp(Database.TDP_db(id=tdp_id))
#     return [ paragraph.to_json_dict() for paragraph in paragraphs ]


# @flask_app.get("/tdps")
# def get_tdps():
#     groupby = request.args.get('groupby')
#     return tdps(request, groupby)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)