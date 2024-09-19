# System libraries
import asyncio
import json
import os
# Third party libraries
from telegram import Bot
from openai import RateLimitError
# Local libraries
from data_access.vector.vector_filter import VectorFilter
from MyLogger import logger
import startup
import threading
from search import search, llm

def send_to_telegram(text):
    bot, chat_id = startup.get_telegram_bot()
    if bot is None: return
    coroutine = bot.send_message(chat_id=chat_id, text=text)
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    asyncio.get_event_loop().run_until_complete(coroutine)

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

def api_tdps() -> str:

    metadata_client, _, _ = startup.get_clients()

    tdps = metadata_client.find_tdps()

    tdps_new, league_map, teamname_map = reduce_tdps( [ tdp.to_dict() for tdp in tdps ] )

    response = { 'tdps': tdps_new, 'league_map': league_map, 'teamname_map': teamname_map }
    
    return json.dumps(response)

def api_query(query:str, filter:VectorFilter) -> str:
    
    try:
        vector_client = startup.get_vector_client()
        cache_client = startup.get_cache_client()

        cache_key = query.lower() + "_" + str(filter)
        
        cache_hit, timestamp = cache_client.find_query(cache_key)

        if startup.get_telegram_bot()[0] is not None:
            cached = "(c)" if cache_hit is not None else ""
            message = f"Query {cached}: {query} | {str(filter)}"
            thread = threading.Thread(target=send_to_telegram, args=[message])
            thread.start()

        if cache_hit is not None:
            return cache_hit
        
        paragraphs, keywords = search(vector_client, query, filter=filter, compress_text=True)

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

        cache_client.insert_query(cache_key, json_response)

        return json_response
    
    except RateLimitError as e:
        raise Exception(json.dumps({
            'error': 'RateLimitError',
            'message': 'OpenAI wants more money!'
        }))
    
    except Exception as e:
        logger.error(str(e))
        raise Exception(json.dumps({
            'error': 'Exception',
            'message': str(e)
        }))


def api_query_llm(query:str, filter:VectorFilter) -> str:
    try:
        vector_client = startup.get_vector_client()
        cache_client = startup.get_cache_client()

        cache_key = query.lower() + "_" + str(filter)
        
        cache_hit, timestamp = cache_client.find_llm(cache_key)

        if startup.get_telegram_bot()[0] is not None:
            cached = "(c)" if cache_hit is not None else ""
            message = f"LLM {cached}: {query} | {str(filter)}"
            thread = threading.Thread(target=send_to_telegram, args=[message])
            thread.start()

        if cache_hit is not None:
            return cache_hit
        
        llm_input, llm_response = llm(vector_client, query, filter)

        result = {
            'llm_input': llm_input,
            'llm_response': llm_response
        }

        json_response = json.dumps(result)

        cache_client.insert_llm(cache_key, json_response)

        return json_response
    
    except RateLimitError as e:
        raise Exception(json.dumps({
            'error': 'RateLimitError',
            'message': 'OpenAI wants more money!'
        }))
    
    except Exception as e:
        logger.error(str(e))
        raise Exception(json.dumps({
            'error': 'Exception',
            'message': str(e)
        }))
