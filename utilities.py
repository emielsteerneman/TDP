import os
import Database
from Database import instance as db_instance
# from embeddings import Embeddor as E

def find_all_TDPs():
    """Find all TDP pdf files in all subdirectories of current directory"""
    tdps = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pdf"):
                tdps.append(os.path.join(root, file))
    return tdps

# TDP file name format: <year>_<is_etdp>_<team>.pdf
def parse_tdp_name(filepath):
    """Parse TDP file name and return a dictionary with the fields"""
    filename = os.path.basename(filepath)
    fields = filename.split('.')[0].split('_')
    return Database.TDP_db (
        filename = filename,
        year = fields[0],
        is_etdp = fields[1].lower() == 'etdp',
        team = " ".join(fields[2:])
    )

def find_all_tdps_and_add_to_database(db):
    tdps = find_all_TDPs()
    parsed = [parse_tdp_name(tdp) for tdp in tdps]    
    for tdp in parsed:
        db.post_tdp(tdp)
    
def paragraph_to_sentences_embeddings(paragraph):
    sentences = paragraph.split('.')
    embeddings = E.embed(sentences)
    return sentences, embeddings

def resentence_paragraphs():
    print("[resentence_paragraphs] Resentencing paragraphs...")

    # Report total number of sentences
    sentences = db_instance.get_sentences()
    print(f"[resentence_paragraphs] {len(sentences)} sentences found")

    tdps = db_instance.get_tdps()
    print(f"[resentence_paragraphs] {len(tdps)} TDPs found")
    for tdp in tdps:
        print(f"[resentence_paragraphs] Resentencing TDP {tdp['id']} : {tdp['team']} {tdp['year']}")
        paragraphs = db_instance.get_paragraphs(tdp['id'])
        for paragraph in paragraphs:
            print(f"[resentence_paragraphs]     Resentencing paragraph {paragraph['id']} : {paragraph['title']}")
            sentences, embeddings = paragraph_to_sentences_embeddings(paragraph['text'])
            db_instance.post_sentences(paragraph['id'], sentences, embeddings)

    # Report total number of sentences
    sentences = db_instance.get_sentences()
    print(f"[resentence_paragraphs] {len(sentences)} sentences found")


def first_test():
    print("Importing packages...")
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import matplotlib.pyplot as plt

    print("Loading model...")
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    cosine_similarity = lambda a, b: np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    paragraph_embeddings = []

    # Get paragraphs from tdp id 63
    paragraphs = db_instance.get_paragraphs(63) + db_instance.get_paragraphs(213)
    for paragraph in paragraphs:
        print(paragraph['title'].rjust(40), "|", paragraph['text'][:100])
        sentences = paragraph['text'].split('.')
        embeddings = model.encode(sentences)
        paragraph_embeddings.append({
            'title': paragraph['title'],
            'embedding_average': np.average(embeddings, axis=0),
            'embeddings': embeddings,
            'sentences': sentences,
            'tdp_id': paragraph['tdp_id']
        })
        

    queries = [
        "I want to know more about ROS and how it works",
        "I want to know more about the wheels",
        "I want to know more about wireless communication between robots",
        "I want to know more about simulation",
        "How does grSim work?",
        "Who created grSim?",
    ]

    for query in queries:

        print()
        print(query)
        query_embedding = model.encode(query)
        
        # Distance between query and average of paragraph embeddings
        distances = [ [cosine_similarity(query_embedding, p['embedding_average']), p] for p in paragraph_embeddings ]
        distances = sorted(distances, reverse=True)
        for distance, p in distances[:5]:
            print(f"{p['tdp_id']}".rjust(5), p['title'].rjust(40), f"{distance:.3f}")

        # Find best matching sentences
        distances_sentences = []
        for p in paragraph_embeddings:
            for sentence, embedding in zip(p['sentences'], p['embeddings']):
                distances_sentences.append([cosine_similarity(query_embedding, embedding), sentence, p])
        distances_sentences = sorted(distances_sentences, key=lambda _: _[0], reverse=True)
        print()
        for distance, sentence, p in distances_sentences[:5]:
            print(f"{p['tdp_id']}".rjust(5), p['title'].rjust(40), f"{distance:.3f}", sentence[:150])

if __name__ == "__main__":
    
    # first_test()
    # db = db.DB()
    # find_all_tdps_and_add_to_database(db)

    resentence_paragraphs()
        
