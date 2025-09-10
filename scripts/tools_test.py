import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import json
from data_access.vector.vector_filter import VectorFilter
from data_access.file.file_client import LocalFileClient
from dotenv import load_dotenv
load_dotenv()
import json
from MyLogger import logger
import startup
from embedding.Embeddings import instance as embeddor
from openai import OpenAI
from search import search, search_fixed
from disk_cache import disk_cache

class CostCounter:
    def __init__(self):
        self.total = 0.
    def add(self, usage):
        costs_in = 0.25 / 1e6
        costs_cached = 0.025 / 1e6
        costs_out = 2.00 / 1e6

        n_cached = usage.input_tokens_details.cached_tokens
        n_in = usage.input_tokens - n_cached
        n_out = usage.output_tokens
        n_reasoning = usage.output_tokens_details.reasoning_tokens

        costs = n_in * costs_in + n_cached * costs_cached + n_out * costs_out
        self.total += costs

        # print(f"n_in: {n_in}, n_cached: {n_cached}, n_out: {n_out}, n_reasoning: {n_reasoning}")
        # print(f"total costs in cents: {total_cost:.3f}")
        print(f"CostCounter -> {n_in}/{n_cached} | {n_out} -> : {costs:.2f} / {self.total:.2f}")

tools = [
    {"type": "web_search"}, 
    {
        "type": "function",
        "name": "get_list_of_team_names",
        "description": "Get a complete list of all the teams, including team name and league"
    },
    {
        "type": "function",
        "name": "search",
        "description": "Given a query, search through the database for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query with which to search through the database"
                },
                "team": {
                    "type": "string",
                    "description": "Limit the search for information to a specific team"
                }
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "find_team_name_using_hint",
        "description": "Given a team name hint, get a list of possible matching team names. For example, if the hint is 'tiger', it will find 'TIGERs Mannheim'",
        "parameters": {
            "type": "object",
            "properties": {
                "hint": {
                    "type": "string",
                    "description": "The hint with which to find possible matching team names"
                }
            },
            "required": ["hint"]
        }
    },
    # {
    #     "type": "function",
    #     "name": "get_robot_details_for_team",
    #     "description": "Get detailed information on the robots of a single team",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "name": {
    #                 "type": "string",
    #                 "description": "The name of the team for which to get detailed information"
    #             }
    #         },
    #         "required": ["name"]
    #     }
    # },
    # {
    #     "type": "function",
    #     "name": "get_papers_for_team",
    #     "description": "Get a list of papers written for a given team",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "team": {
    #                 "type": "string",
    #                 "description": "The name of the team for which to get a list of papers"
    #             }
    #         },
    #         "required": ["name"]
    #     }
    # }
    ]


print("Creating OpenAI client")
client = OpenAI()
vector_client = startup.get_vector_client()

file_client = startup.get_file_client()


def do_search(query:str, team:str=None) -> str:
    f = VectorFilter(league="soccer_smallsize", year_min=2020, team=team)
    paragraphs, keywords = search_fixed(vector_client, query)

    SOURCE_OFFSET = 1000
    llm_input = ""

    sources = {}

    llm_input += "\n"
    for i_paragraph, paragraph in enumerate(paragraphs):
        llm_input = f"SOURCE : [{i_paragraph+SOURCE_OFFSET}] = {paragraph.tdp_name.filename}\n"
        sources[i_paragraph] = paragraph.tdp_name
    llm_input += "\n"

    for i_paragraph, paragraph in enumerate(paragraphs):
        llm_input += "\n\n\n\n=============== NEW PARAGRAPH ================\n"
        llm_input += f"SOURCE : | id='[{i_paragraph+SOURCE_OFFSET}]', team='{paragraph.tdp_name.team_name.name_pretty}', year='{paragraph.tdp_name.year}', league='{paragraph.tdp_name.league.name_pretty}', paragraph='{paragraph.text_raw}' |\n"
        llm_input += f"TEXT : | {paragraph.content_raw()} |"
    
    print(llm_input)
    
    return llm_input














@disk_cache()
def get_all_teams():
    print("beep boop")
    filenames, _ = file_client.list_pdfs()
    return list(set([ f.team_name.name_pretty for f in filenames ]))    

from find_name_with_hint import find_team_name_using_hint

def get_papers_for_team(team_name):
    files, _ = file_client.list_pdfs()
    files = [ _ for _ in files if _.team_name.name_pretty == team_name]
    files = sorted(files, key=lambda f: f.filename)
    files = [ _.filename for _ in files ]
    return files

input_list = []
cc = CostCounter()

weird_numbers = {}
number_factory = 0

def make_call(input_list):    
    return client.responses.create(
        model="gpt-5-nano",
        tools=tools,
        reasoning={"effort": "low"},
        input=input_list,
    )

def mock_function_call(fn):
    print(f"{fn.name}({fn.arguments})")
    args = json.loads(fn.arguments)
    print(args)

    output = None
    if fn.name == "get_list_of_team_names": 
        output = json.dumps({
                "names": ["RoboTeam Twente", "TIGERs Mannheim", "ER-Force"]
        })
    elif fn.name == "get_robot_details_for_team":
        output = json.dumps({
            "robot_names": ["Gandalf", "Wall-E", "Iron Giant"],
            "robot_heights_cm": [15, 16.7, 16.3],
            "max_velocity_kmh": 10,
        })
    elif fn.name == "find_team_name_using_hint":
        output = json.dumps(find_team_name_using_hint(args["hint"]))
        print(output)
    elif fn.name == "get_papers_for_team":
        output = json.dumps(get_papers_for_team(args["team"]))
        print(output)
    elif fn.name == "search":
        query = args["query"]
        team = None if "team" not in args else args["team"]
        output = json.dumps(do_search(query, team))
    else:
        print(f"Unknown function: {fn.name}")

    return {
        "type": "function_call_output",
        "call_id": fn.call_id,
        "output": output
    }

def loop():
    query = input("Yes?: ")
    input_list = [
        {"role": "user", "content": query}
    ]    
    
    while True:
        print()
        response = make_call(input_list)
        # print("Response received")
        cc.add(response.usage)
        
        # https://community.openai.com/t/openai-api-error-function-call-was-provided-without-its-required-reasoning-item-the-real-issue/1355347
        function_call_outputs = []

        for r in response.output:
            if r.type == "function_call":
                print(f"Function {r.name}({r.arguments}) -->", end=" ")
                # print("FUNCTION:", r)
                print("Response -->", end=" ")
                input_list.append(r)
                # print("FUNCTION RESPONSE:", r)
                function_call_outputs.append(mock_function_call(r))

            elif r.type == "reasoning":
                # print("REASONING:", r)
                print("Reasoning -->", end=" ")
                input_list.append(r)

            elif r.type == "message":
                # print("MESSAGE:", r)
                print("Message -->", end=" ")
                input_list.append(r)
                print()
                print(response.output_text)
                print()
                q = input("Yes?: ")
                input_list.append({
                    "role": "user", "content": q
                })

            elif r.type == "web_search_call":
                print("Web Search -->", end=" ")
                input_list.append(r)

            elif r.type == "search":
                exit()
            else:
                print("??", r.type, r)
                q = input("Yes?: ")
        
        input_list += function_call_outputs
        print()


from types import SimpleNamespace
wer = SimpleNamespace()
wer.name = "search"
wer.arguments = '{"query":"omniwheels RoboTeam Twente","team":"RoboTeam Twente"}'
mock_function_call(wer)
exit()
# mock_function_call({
#     "name": "search",
#     "arguments": '{"query":"omniwheels RoboTeam Twente","team":"RoboTeam Twente"}'
# })

loop()