import weaviate
import weaviate.classes as wvc
import weaviate.classes.config as wvcc

from extraction import extractor as E
import Embeddings
import utilities as U
from MyLogger import logger

def create_weaviate_schema(client: weaviate.client.Client, overwrite: bool = False):
    if not overwrite and client.collections.exists("Sentence"):
        return client.collections.get("Sentence")
    
    answer = input("You are about to delete the current schema and create a new one. Are you sure? (y/n)")
    if answer.lower() != "y":
        return client.collections.get("Sentence")

    # Delete the schema if it exists
    client.collections.delete("Sentence")
    logger.info("Deleted the schema 'Sentence'")

    # Create the schema
    # https://weaviate.io/developers/weaviate/manage-data/collections
    collection = client.collections.create(
        name="Sentence",
        description="A sentence",
        vector_index_config=wvc.config.Configure.VectorIndex.flat(
            distance_metric=wvc.config.VectorDistances.COSINE,
        ),
        properties=[
            wvcc.Property(name="team", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=False),
            wvcc.Property(name="year", data_type=wvcc.DataType.INT, index_filterable=True, index_searchable=False),
            wvcc.Property(name="league", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=False),

            wvcc.Property(name="text", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=True),
        ]
    )
    logger.info("Created the schema 'Sentence'")

    return collection

client = weaviate.connect_to_custom(
    http_host="localhost",
    http_port=8081,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False,
)

print(f"Client is ready: {client.is_ready()}")

collection = create_weaviate_schema(client, overwrite=True)

tdps = U.find_all_tdps()
print(len(tdps))

tdps = tdps[-20:]

for tdp in tdps:

    tdp = E.process_pdf(tdp)
    print(tdp)

    embedder = Embeddings.instance

    sentences = [ sentence for paragraph in tdp.paragraphs for sentence in paragraph.sentences ]
    for sentence in sentences:
        vector = embedder.embed(sentence.text_raw)

        uuid = collection.data.insert(
            properties={
                "team": tdp.team,
                "year": tdp.year,
                "league": tdp.league,
                "text": sentence.text_raw
            },
            vector=vector.tolist()
        )
        # print(f"# {uuid} {sentence.text_raw}\n")

# Search
query = "What path planning techniques exist?"
vector = embedder.embed(query)
results = collection.query.near_vector(
    vector.tolist(), limit=5
    # filters=wvc.query.Filter.by_property("team").equal("SomeTeam")
)

print("\n\n")
# print(f"Results: {results}")

for r in results.objects:
    print("\n\n")
    print(r.properties["text"])


client.close()