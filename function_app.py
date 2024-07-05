# System libraries
import os
import json
from dotenv import load_dotenv
# Third party libraries
from azure import functions as func
# Local libraries
import app
from data_access.metadata.metadata_client import MongoDBClient
from data_access.vector.pinecone_client import PineconeClient
from data_structures.TDPName import TDPName
from MyLogger import logger
import startup

print("Running...")

load_dotenv()

azure_app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

metadata_client, file_client = startup.get_clients()
vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))


# https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=linux%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python

@azure_app.route('metadata/find')
def metadata_find(req: func.HttpRequest):
    team = req.params.get('team')
    year = int(req.params.get('year')) if req.params.get('year') else None
    league = req.params.get('league')

    # if team is None: team = "RoboTeam_Twente"
    # if year is None: year = 2019
    # if league is None: league = "soccer_smallsize"

    metadata_client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
    tdps = metadata_client.find_tdps(team=team, year=year, league=league)

    logger.info(f"Found {len(tdps)} TDPs for team={team}, year={year}, league={league}")

    json_response = json.dumps([ tdp.to_dict() for tdp in tdps ])

    headers = { "Cache-Control": "max-age=604800, public" }
    
    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)

@azure_app.route('tdps')
def api_tdps(req: func.HttpRequest):
    json_response:str = app.api_tdps()
    headers = { "Access-Control-Allow-Origin": "*" }
    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)

@azure_app.route("tdp/{tdp_name}/pdf")
def api_tdp_pdf(req: func.HttpRequest) -> func.HttpResponse:
    
    env = startup.get_environment()

    tdp_name:str = req.route_params.get('tdp_name')
    tdp_name:TDPName = TDPName.from_string(tdp_name)

    if env == "LOCAL":
        with open(f"static/pdf/{tdp_name.to_filepath(TDPName.PDF_EXT)}", "rb") as f:
            pdf_bytes = f.read()
        return func.HttpResponse(pdf_bytes, mimetype="application/pdf")
        # return func.HttpResponse("<h1>Not implemented</h1>", mimetype="text/html")

    if env == "AZURE":
        redirect_url:str = f"https://tdps.blob.core.windows.net/tdps/pdf/{tdp_name.to_filepath(TDPName.PDF_EXT)}"
        return func.HttpResponse(status_code=302, headers={"Location": redirect_url})
    
@azure_app.route("tdp/{tdp_name}/html")
def api_tdp_html(req: func.HttpRequest) -> func.HttpResponse:
    
    env = startup.get_environment()

    tdp_name:str = req.route_params.get('tdp_name')
    tdp_name:TDPName = TDPName.from_string(tdp_name)

    if env == "LOCAL":
        with open(f"static/html/{tdp_name.to_filepath(TDPName.HTML_EXT)}", "r") as f:
            html = f.read()
        return func.HttpResponse(html, mimetype="text/html")
        # return func.HttpResponse("<h1>Not implemented</h1>", mimetype="text/html")

    if env == "AZURE":
        redirect_url:str = f"https://tdps.blob.core.windows.net/tdps/html/{tdp_name.to_filepath(TDPName.HTML_EXT)}"
        return func.HttpResponse(status_code=302, headers={"Location": redirect_url})
    
@azure_app.route("query")
def api_query(req: func.HttpRequest):
    from search import search
    query = req.params.get('query')

    """
    Flask equivalent

    paragraphs, keywords = search(vector_client, query, compress_text=True)
    paragraphs_json = []
    for paragraph in paragraphs:
        paragraphs_json.append({
            'tdp_name': paragraph.tdp_name.to_dict(),
            'title': paragraph.text_raw,
            'content': paragraph.content_raw(),
            'questions': paragraph.questions,
        })

    result = {
        'paragraphs': paragraphs_json,
        'keywords': keywords
    }    

    flask_response = Response(json.dumps(result))
    flask_response.headers['Content-Type'] = "application/json"
    # flask_response.headers['Cache-Control'] = "max-age=604800, public"
    return flask_response

    """

    paragraphs, keywords = search(vector_client, query, compress_text=True)
    paragraphs_json = []
    for paragraph in paragraphs:
        paragraphs_json.append({
            'tdp_name': paragraph.tdp_name.to_dict(),
            'title': paragraph.text_raw,
            'content': paragraph.content_raw(),
            'questions': paragraph.questions,
        })

    result = {
        'paragraphs': paragraphs_json,
        'keywords': keywords
    }

    json_response = json.dumps(result)
    headers = { "Access-Control-Allow-Origin": "*" }
    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)