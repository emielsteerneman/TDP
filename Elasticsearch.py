from elasticsearch import Elasticsearch
from Database import instance as db_instance

# es = Elasticsearch("http://localhost:9200", http_auth=('elastic', 't0tZDPk5pqBAWDQ0da4W'))
es = Elasticsearch("http://localhost:9200", api_key=('VEAI4IgBLWjbsXYT_5o2', 'FbjrrmgrTNKvRiFGHmM7OQ'), verify_certs=False)
print(es.info().body)

mappings = {
    "properties": {
        "title": {"type": "text", "analyzer": "standard"},
        "text": {"type": "text", "analyzer": "standard"},
        "team": {"type": "text", "analyzer": "standard"},
        "year": {"type": "integer"},
    }
}


# {"id":"VEAI4IgBLWjbsXYT_5o2","name":"master","api_key":"FbjrrmgrTNKvRiFGHmM7OQ","encoded":"VkVBSTRJZ0JMV2pic1hZVF81bzI6RmJqcnJtZ3JUTkt2UmlGR0htTTdPUQ=="}

try:
    es.indices.delete(index="paragraphs")
    es.indices.create(index="paragraphs", mappings=mappings)
except Exception as e:
    print(e)


# Get paragraphs from database
paragraphs = db_instance.get_paragraphs()
tdp_ids = list(set([p["tdp_id"] for p in paragraphs]))
# Get TDPs from database
tdps = [ db_instance.get_tdp(tdp_id) for tdp_id in tdp_ids ] 

print(f"[ES] {len(paragraphs)} paragraphs retrieved from database")
print(f"[ES] {len(tdps)} TDPs retrieved from database")

tdpid_tdps = { tdp["id"]: tdp for tdp in tdps }
paragraphs = [
    {
        "title": p["title"],
        "text": p["text"],
        "team": tdpid_tdps[p["tdp_id"]]["team"],
        "year": tdpid_tdps[p["tdp_id"]]["year"],
    } for p in paragraphs
]

for index, paragraph in enumerate(paragraphs):
    es.index(index="paragraphs", id=index, document=paragraph)
print(f"[ES] {len(paragraphs)} paragraphs indexed")

es.indices.refresh(index="paragraphs")
print(f"[ES] {es.cat.count(index='paragraphs').split(' ')[2][:-1]} paragraphs within Elasticsearch")


# Perform a BM25 search
query = 'I want to know more about the simulator of roboteam twente'
search_results = es.search(
    index='paragraphs',
    body={
        "query": {
            "match": {
                "text": query
            }
        }
    }
)

# Process search results
for hit in search_results['hits']['hits']:
    print(f"{hit['_score']:.2f}", hit['_source']['team'], hit['_source']['title'])