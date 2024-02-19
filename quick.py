import fitz
from importlib import reload
from extraction import extractor as E
from openai import OpenAI
import json


def parse_response(response):
	print("\n")

	# print(response)

	if response.startswith('```'):
		response = response[7:-3]

	response_obj = json.loads(response)

	if 'tags' in response_obj:
		print(  "Tags:", ", ".join(response_obj['tags']))
		print()
	if 'domain' in response_obj:
		print("Domain:", ", ".join(response_obj['domain']))
		print()
	if 'questions' in response_obj:
		print("Questions:")
		for q in response_obj['questions']:
			print("- ", q)
		print()
	if 'summary' in response_obj:
		print("Summary:")
		print('   ', response_obj['summary'])
		print()

	print()
	print(response)


d = fitz.open("2023_ETDP_RoboTeam_Twente.pdf")

tdp = E.process_pdf(d)

client = OpenAI(
	api_key = "",
)

tags = ["#pathplanning", "#electronics", "#mechanics", "#software", "#ai", "#motor", "#pathplanning", "#solenoid", "#ballsensor", "#kicker", "#chipper"]
Query1 = f"Using the json key 'tags', given the tags [{' '.join(tags)}], reply with a list containing only the tags that are relevant to the text above. "
Query2 = f"Using the json key 'domain', give a list of words from the text that are domain specific."
Query3 = f"Using the json key 'questions', generate up to 5 questions that could be asked by a user searching for information, that this text could provide an answer to. The questions should not contain information specific to this text."
Query4 = f"Using the json key 'summary', summarize the text in 50 words, in which the text is explained to someone who just finished high school and has only little domain knowledge"
# for p in tdp.paragraphs:
# 	print(p.content_raw())
# 	print("\n\n")

# print(Query)

print("\n")
p = tdp.paragraphs[3]
print(p.content_raw())

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a computer terminal. Are your responses are json lists parseable by the python function 'json.loads'."},
    {"role": "user", "content": p.content_raw()},
    {"role": "user", "content": Query1},
    {"role": "user", "content": Query2},
    {"role": "user", "content": Query3},
    {"role": "user", "content": Query4},
  ]
)

response = completion.choices[0].message.content
parse_response(response)


for p in tdp.paragraphs:
	completion = client.chat.completions.create(
	  model="gpt-3.5-turbo",
	  messages=[
	    {"role": "system", "content": "You are a computer terminal. Are your responses are json lists parseable by the python function 'json.loads'."},
	    {"role": "user", "content": p.content_raw()},
	    {"role": "user", "content": Query4},
	  ]
	)

	response = completion.choices[0].message.content
	parse_response(response)


"""

TDP

[sentence]{
	raw text
	factory id
	page number
	paragraph id
}

[paragraph]{
	raw text (which is the title)
	factory id
	page number
	semver
}
[images]{
	
}
information {
	team name
	year
	league
}

debug {
	pagenumbers top
	pagenumbers bottom
	excluded ids?
	image descriptions

}


Do I need to know what (sub)paragraph a sentence belongs to?
- Suggesting entire paragraphs might be easier for RAG
- 

"""