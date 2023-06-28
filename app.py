# save this as app.py
from flask import Flask, render_template, request, send_from_directory
import Database
from Database import instance as db_instance
import utilities as U
from embeddings import Embeddor as E

app = Flask(__name__, template_folder='templates')

E.set_sentences(db_instance.get_sentences())

@app.route('/TDPs/<year>/<filename>')
def download_file(year, filename):
    return send_from_directory(f'TDPs/{year}', filename, as_attachment=True)

@app.route('/templates/<filename>')
def static_file(filename):
    return send_from_directory(f'templates', filename)


def tdps(request, groupby=None):
    tdps = db_instance.get_tdps()
    tdps = [ dict(_) for _ in tdps ]
    
    if groupby == 'team':
        teams = {}
        for tdp in tdps:
            if tdp['team'] not in teams: teams[tdp['team']] = []
            teams[tdp['team']].append(tdp)
        # Sort by year
        teams = { team: sorted(teams[team], key=lambda _: _['year'], reverse=True) for team in teams }
        return render_template('tdps.html', data=teams, groupby=groupby)
    
    if groupby == 'year':
        years = {}
        for tdp in tdps:
            if tdp['year'] not in years: years[tdp['year']] = []
            years[tdp['year']].append(tdp)
        # Sort by team
        years = { year: sorted(years[year], key=lambda _: _['team']) for year in years }
        return render_template('tdps.html', data=years, groupby=groupby)

    return render_template('tdps.html', data=tdps, groupby=groupby)

@app.get("/")
def hello():
    return tdps(request)

@app.get("/tdps/<id>")
def get_tdps_id(id):
    tdp_db = Database.TDP_db(id=id)
    tdp = db_instance.get_tdp_by_id(tdp_db)
    filepath = f"/TDPs/{tdp['year']}/{tdp['filename']}"
    return render_template('tdp.html', tdp=tdp, filepath=filepath)

# @app.get("/api/tdps/<id>")
# def get_api_tdps_id(id):
#     return { "hello": "world" }

@app.get("/api/tdps")
def get_api_tdps():
    return db_instance.get_tdps()


""" /api/tdps/<tdp_id>/paragraphs """

@app.get("/api/tdps/<tdp_id>/paragraphs")
def get_api_tdps_id_paragraphs(tdp_id):
    paragraphs = db_instance.get_paragraphs(Database.TDP_db(id=tdp_id))
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
    sentences, paragraphs, tdps = E.query(query)
    return {
        'sentences': sentences,
        'paragraphs': paragraphs,
        'tdps': tdps
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

