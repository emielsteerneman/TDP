# save this as app.py
from flask import Flask, render_template, request, send_from_directory
import Database
from Database import instance as db_instance
import utilities as U
from Embeddings import Embeddor as E
import os
import Search
from Search import instance as search_instance

app = Flask(__name__, template_folder='templates', static_folder='static')

E.set_sentences(db_instance.get_sentences())

@app.route('/TDPs/<year>/<filename>')
def download_file(year, filename):
    return send_from_directory(f'TDPs/{year}', filename, as_attachment=True)

@app.route('/templates/<filename>')
def static_file(filename):
    return send_from_directory(f'templates', filename)

@app.route('/static/logos/<filename>')
def static_logo(filename):
    # Check if logo exists, else default logo
    if os.path.exists('static/logos/' + filename):
        return send_from_directory('static/logos', filename)
    else:
        return send_from_directory('static/logos', '10px.png')

def tdps(request, groupby=None):
    tdps = db_instance.get_tdps()
    
    if groupby == 'team':
        teams = {}
        for tdp in tdps:
            if tdp.team not in teams: teams[tdp.team] = []
            teams[tdp.team].append(tdp)
        # Sort by year
        teams = { team: sorted(teams[team], key=lambda _: _.year, reverse=True) for team in teams }
        return render_template('tdps.html', data=teams, groupby=groupby)
    
    if groupby == 'year':
        years = {}
        for tdp in tdps:
            if tdp.year not in years: years[tdp.year] = []
            years[tdp.year].append(tdp)
        # Sort by team
        years = { year: sorted(years[year], key=lambda _: _.team) for year in years }
        return render_template('tdps.html', data=years, groupby=groupby)

    return render_template('tdps.html', data=tdps, groupby=groupby)

@app.get("/")
def hello():
    return tdps(request)

@app.get("/tdps/<id>")
def get_tdps_id(id):
    tdp_db = db_instance.get_tdp_by_id(id)
    filepath = f"/TDPs/{tdp_db.year}/{tdp_db.filename}"
    return render_template('tdp.html', tdp=tdp_db, filepath=filepath)

@app.get("/query")
def get_query():
    return send_from_directory('templates', 'query.html')

@app.get("/api/tdps")
def get_api_tdps():
    return db_instance.get_tdps()


""" /api/tdps/<tdp_id>/paragraphs """

@app.get("/api/tdps/<tdp_id>/paragraphs")
def get_api_tdps_id_paragraphs(tdp_id):
    tdp = db_instance.get_tdp_by_id(tdp_id)
    print("Retrieving paragraphs for TDP", tdp.filename)
    
    paragraphs = db_instance.get_paragraphs_by_tdp(Database.TDP_db(id=tdp_id))
    return [ paragraph.to_dict() for paragraph in paragraphs ]
@app.post("/api/tdps/<tdp_id>/paragraphs")
def post_api_tdps_id_paragraphs(tdp_id):
    body = request.get_json()
    db_instance.post_paragraph(Database.Paragraph_db.from_dict(body))

    # sentences, embeddings = U.paragraph_to_sentences_embeddings(text)
    # db_instance.post_sentences(paragraph_id, sentences, embeddings)

    paragraphs = db_instance.get_paragraphs(tdp_id)
    return [ paragraph.to_dict() for paragraph in paragraphs ]

@app.delete("/api/tdps/<tdp_id>/paragraphs/<paragraph_id>")
def delete_api_tdps_id_paragraphs(tdp_id, paragraph_id):
    paragraph_db = Database.Paragraph_db(id=paragraph_id)
    db_instance.delete_paragraph(paragraph_db)
    paragraphs = db_instance.get_paragraphs(tdp_id)
    return [ paragraph.to_dict() for paragraph in paragraphs ]

""" /api/query """

@app.post("/api/query")
def post_api_query():
    body = request.get_json()
    query = body['query']

    sentences, scores = search_instance.search(query, R=0.9, n=100)
    paragraph_ids = search_instance.sentences_to_paragraphs(sentences, scores)
    paragraphs = [ db_instance.get_paragraph_by_id(id) for id in paragraph_ids ]

    """ Sort TDPs by the importances of their sentences """
    
    tdp_ids_by_sentence_scores = []
    for sentence in sentences:
        paragraph_db = db_instance.get_paragraph_by_id(sentence.paragraph_id)
        if paragraph_db.tdp_id not in tdp_ids_by_sentence_scores:
            tdp_ids_by_sentence_scores.append(paragraph_db.tdp_id)

    # sentences, paragraphs, tdps, query, query_words = E.query(query)
    
    """ Convert Sentence_DB to Sentence dict which holds more information and can have the embedding removed """
    sentences = [ db_instance.get_sentence_exhaustive(s) for s in sentences ]
    for sentence in sentences: sentence.pop('embedding')
    
    """ Get all relevant TDPs """
    tdp_ids = list(set([ _['tdp_id'] for _ in sentences ]))
    tdps = [ db_instance.get_tdp_by_id(id) for id in tdp_ids ]
    
    # Group sentences by paragraph
    sentences_by_paragraph = {}
    for sentence in sentences:
        paragraph_id = sentence['paragraph_id']
        if paragraph_id not in sentences_by_paragraph: sentences_by_paragraph[paragraph_id] = []
        sentences_by_paragraph[paragraph_id].append(sentence)
           
    # Group paragraph groups by tdp
    paragraphs_by_tdp = {}
    for paragraph_id, sentences in sentences_by_paragraph.items():
        tdp_id = sentences[0]['tdp_id']
        if tdp_id not in paragraphs_by_tdp: paragraphs_by_tdp[tdp_id] = {}
        paragraphs_by_tdp[tdp_id][paragraph_id] = sentences
    
    # # Group sentences by tdp
    # sentences_by_tdp = {}
    # for sentence in sentences: 
    #     tdp_id = sentence['tdp_id']
    #     if tdp_id not in sentences_by_tdp: sentences_by_tdp[tdp_id] = []
    #     sentences_by_tdp[tdp_id].append(sentence)
    
    paragraphs = [ _.to_dict() for _ in paragraphs ]
    tdps = [ _.to_dict() for _ in tdps ]
    
    return {
        'sentences': sentences,
        'sentences_by_tdp': paragraphs_by_tdp,
        'paragraphs': paragraphs,
        'tdps': tdps,
        'tdp_order': tdp_ids_by_sentence_scores,
        'query': query,
        'query_words': Search.query_to_words(query)
    }




@app.post("/tdps/<id>")
def post_tdps_id(id):
    print(request.form)
    
    # Store text from field 'textfield' in database
    text = request.form.get('textfield')
    db_instance.post_text(id, text)
    
    return get_tdps_id(id)

@app.get("/tdps")
def get_tdps():
    groupby = request.args.get('groupby')
    return tdps(request, groupby)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)