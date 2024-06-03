# System libraries
import json
import os
from importlib import reload

# Local libraries
from embedding.Embeddings import instance as embed_instance
from extraction import extractor as E

os.path.expanduser('.env')

def parse_response(response):
	print("\n")

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

tdp = E.process_pdf("2023_ETDP_RoboTeam_Twente.pdf")

sentences = [ s.text_raw for s in tdp.get_sentences()[:5] ]

embedding = embed_instance.embed_using_sentence_transformer(sentences)
print(embedding[:, :3])
print()
embedding = embed_instance.embed_dense_openai(sentences)
print(embedding[:, :3])


# for k, v in os.environ.items():
# 	print(k.rjust(40), v)


"""

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