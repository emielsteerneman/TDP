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
from data_access.vector.vector_filter import VectorFilter
from data_structures.TDPName import TDPName
from MyLogger import logger
import startup
import time

load_dotenv()

azure_app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

metadata_client, file_client, vector_client = startup.get_clients()

# https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=linux%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python

@azure_app.route('metadata/find')
def metadata_find(req: func.HttpRequest):
    global metadata_client
    
    team = req.params.get('team')
    year = int(req.params.get('year')) if req.params.get('year') else None
    league = req.params.get('league')

    tdps = metadata_client.find_tdps(team=team, year=year, league=league)

    logger.info(f"Found {len(tdps)} TDPs for team={team}, year={year}, league={league}")

    json_response = json.dumps([ tdp.to_dict() for tdp in tdps ])

    headers = { 
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=604800, public"
    }
    
    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)

@azure_app.route('tdps')
def api_tdps(req: func.HttpRequest):
    json_response:str = app.api_tdps()
    headers = { 
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=604800, public"     
    }
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
    
    t_start = time.time()

    query = req.params.get('query')
    filter = VectorFilter.from_dict(dict(req.params))
    
    try:
        json_response:str = app.api_query(query, filter)
    except Exception as e:
        json_response = str(e)
        headers = { "Access-Control-Allow-Origin": "*" }
        return func.HttpResponse(json_response, status_code=500, mimetype="application/json", headers=headers)
    finally:
        duration_ms = (time.time() - t_start) * 1000
        logger.info(f"duration={duration_ms} query={query}")

    headers = { 
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=604800, public"
    }
    
    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)

@azure_app.route("query/llm")
def api_query_llm(req: func.HttpRequest):
    t_start = time.time()

    query = req.params.get('query')
    filter = VectorFilter.from_dict(dict(req.params))

    try:
        json_response:str = app.api_query_llm(query, filter)
    except Exception as e:
        json_response = str(e)
        headers = { "Access-Control-Allow-Origin": "*" }
        return func.HttpResponse(json_response, status_code=500, mimetype="application/json", headers=headers)
    finally:
        duration_ms = (time.time() - t_start) * 1000
        logger.info(f"duration={duration_ms} query={query}")

    headers = { 
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=604800, public"
    }
    
    return func.HttpResponse(json_response, mimetype="application/json", headers=headers)