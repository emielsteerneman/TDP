# System libraries
import json
# Third party libraries
# Local libraries
import startup
from search import search

from data_access.vector.vector_filter import VectorFilter

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
    _, _, vector_client = startup.get_clients()

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

    return json_response