# System libraries
import os
import json
from custom_dotenv import load_dotenv
# Third party libraries
from azure import functions as func
# Local libraries
import app
from data_access.metadata.metadata_client import MongoDBClient
from MyLogger import logger


load_dotenv()

azure_app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=linux%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python

@azure_app.route('metadata/find')
def metadata_find(req: func.HttpRequest):
    team = req.params.get('team')
    year = int(req.params.get('year')) if req.params.get('year') else None
    league = req.params.get('league')

    if team is None: team = "RoboTeam_Twente"
    if year is None: year = 2019
    if league is None: league = "soccer_smallsize"

    metadata_client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
    tdps = metadata_client.find_tdps(team=team, year=year, league=league)

    logger.info(f"Found {len(tdps)} TDPs for team={team}, year={year}, league={league}")

    json_response = json.dumps([ tdp.to_dict() for tdp in tdps ])

    headers = {
        "Cache-Control": "max-age=604800, public",
    }
    
    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)

@azure_app.route('tdps')
def api_tdps(req: func.HttpRequest):
    json_response:str = app.api_tdps()

    headers = {
        "Access-Control-Allow-Origin": "*"
    }

    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)