# System libraries
import os
import json
from dotenv import load_dotenv
# Third party libraries
from azure import functions as func
# Local libraries
# from data_access.metadata.metadata_client import MongoDBClient

load_dotenv()

app = func.FunctionApp()

# https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=linux%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python

@app.route('metadata/find')
def metadata_find(req: func.HttpRequest):
    team = req.params.get('team')
    year = int(req.params.get('year')) if req.params.get('year') else None
    league = req.params.get('league')

    d = {
        "team": team,
        "year": year,
        "league": league
    }

    return "Hello world!"

    # return func.HttpResponse(json.dumps(d), mimetype="application/json")

    # metadata_client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
    # tdps = metadata_client.find_tdps(team=team, year=year, league=league)

    # json_response = json.dumps([ tdp.to_dict() for tdp in tdps ])

    # return func.HttpResponse(json_response, mimetype="application/json")