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
import startup
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import FileClient
from data_structures.TDPName import TDPName
from MyLogger import logger

app = Flask(__name__, template_folder='webapp/templates', static_url_path='/static', static_folder='webapp/static')


metadata_client, file_client = startup.get_clients()

@app.before_request
def before_request():
    g.file_client = file_client
    g.metadata_client = metadata_client

@app.after_request
def after_request(response):
    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/")
def index():
    return "Hello World!!!"

def reduce_tdps(tdps):
    league_map, league_map_inverse = {}, {}
    teamname_map, teamname_map_inverse = {}, {}

    league_map_idx = 0
    teamname_map_idx = 0

    tdps_new = []
    for tdp in tdps:
        tdp_new = {}
        tdp_new['y'] = tdp['tdp_name']['year']
        
        league_name = tdp['tdp_name']['league']['name']
        league_name_pretty = tdp['tdp_name']['league']['name_pretty']
        
        if league_name not in league_map_inverse:
            league_map[league_map_idx] = [league_name, league_name_pretty]
            league_map_inverse[league_name] = league_map_idx
            league_map_idx += 1

        tdp_new['l'] = league_map_inverse[league_name]

        team_name = tdp['tdp_name']['team_name']['name']
        team_name_pretty = tdp['tdp_name']['team_name']['name_pretty']

        if team_name not in teamname_map_inverse:
            teamname_map[teamname_map_idx] = [team_name, team_name_pretty]
            teamname_map_inverse[team_name] = teamname_map_idx
            teamname_map_idx += 1

        tdp_new['t'] = teamname_map_inverse[team_name]

        tdps_new.append(tdp_new)

    return tdps_new, league_map, teamname_map

@app.route("/api/tdps")
def api_tdps():
    tdps = g.metadata_client.find_tdps()

    tdps_new, league_map, teamname_map = reduce_tdps( [ tdp.to_dict() for tdp in tdps ] )

    response = { 'tdps': tdps_new, 'league_map': league_map, 'teamname_map': teamname_map }
    
    flask_response = Response(json.dumps(response))
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

@app.route("/api/tdp/<tdp_name>/pdf")
def api_tdp_pdf(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=True)

    # flask_response.headers['Content-Type'] = "application/json"
    # flask_response.headers['Cache-Control'] = "max-age=604800, public"
    # return flask_response

@app.route("/api/tdp/<tdp_name>/html")
def api_tdp_html(tdp_name:str):
    return api_tdp(tdp_name, is_pdf=False)

@app.route("/api/tdp/<tdp_name>/image/<image_idx>")
def api_tdp_image(tdp_name:str, image_idx:int):
    pass



# @app.route('/TDPs/<year>/<filename>')
# def download_file(year, filename):
#     return send_from_directory(f'TDPs/{year}', filename, as_attachment=True)

# @app.route('/templates/<filename>')
# def static_file(filename):
#     return send_from_directory(f'templates', filename)

# @app.route('/static/logos/<filename>')
# def static_logo(filename):
#     # Check if logo exists, else default logo
#     if os.path.exists('static/logos/' + filename):
#         return send_from_directory('static/logos', filename)
#     else:
#         return send_from_directory('static/logos', '10px.png')

# @app.get("/")
# def homepage():
#     print("Loading homepage")
#     return send_from_directory('webapp/templates', 'index.html')

# @app.get("/tdps/<id>")
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

# @app.get("/api/tdps/<tdp_id>/paragraphs")
# def get_api_tdps_id_paragraphs(tdp_id):
#     tdp = db_instance.get_tdp_by_id(tdp_id)
#     print("[app] Retrieving paragraphs for TDP", tdp.filename)
#     paragraphs = db_instance.get_paragraphs_by_tdp(Database.TDP_db(id=tdp_id))
#     return [ paragraph.to_json_dict() for paragraph in paragraphs ]


# @app.get("/tdps")
# def get_tdps():
#     groupby = request.args.get('groupby')
#     return tdps(request, groupby)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)