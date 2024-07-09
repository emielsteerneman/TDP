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
from data_access.vector.pinecone_client import PineconeClient
from data_access.vector.vector_filter import VectorFilter
from data_structures.TDPName import TDPName
from MyLogger import logger

flask_app = Flask(__name__, template_folder='webapp/templates', static_url_path='/static', static_folder='webapp/static')

metadata_client, file_client, vector_client = startup.get_clients()

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
        return send_from_directory("static/pdf", tdp_name.to_filepath(TDPName.PDF_EXT), max_age=604800)
    else:
        return send_from_directory("static/html", tdp_name.to_filepath(TDPName.HTML_EXT), max_age=604800)

@flask_app.route("/api/tdp/<tdp_name>/pdf")
def api_tdp_pdf(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=True)

@flask_app.route("/api/tdp/<tdp_name>/html")
def api_tdp_html(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=False)

@flask_app.route("/api/tdp/<tdp_name>/image/<image_idx>")
def api_tdp_image(tdp_name:str, image_idx:int):
    pass

@flask_app.route("/api/query")
def api_query():
    query = request.args.get('query')
    filter = VectorFilter.from_dict(dict(request.args))

    json_response:str = app.api_query(query, filter)
    
    flask_response = Response(json_response)
    flask_response.headers['Content-Type'] = "application/json"
    flask_response.headers['Cache-Control'] = "max-age=604800, public"
    
    return flask_response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)