import asyncio
from collections import OrderedDict
import functools
import os
import time
import threading

from flask import Flask, render_template, request, send_from_directory
import Database
from Database import instance as db_instance
from Database_tdp_views import instance as db_instance_tdp_views
from Database_queries import instance as db_instance_queries
import utilities as U
from Embeddings import instance as embed_instance
import Search
from telegram import Bot

app = Flask(__name__, template_folder='templates', static_url_path='/static', static_folder='static')

embed_instance.set_sentences(db_instance.get_sentences())

search_instance_sentences = Search.Search(Search.Search.SOURCE_SENTENCES)
search_instance_paragraphs = Search.Search(Search.Search.SOURCE_PARAGRAPHS)
search_instance_images = Search.Search(Search.Search.SOURCE_IMAGES)

bot = None
if os.getenv('TELEGRAM_TOKEN') is not None and os.getenv('TELEGRAM_CHAT_ID') is not None:
    # Create telegram bot
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    bot = Bot(token=TELEGRAM_TOKEN)
    print("[app] Created telegram bot")

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

@app.route('/images/<year>/<filename>')
def tdp_image(year, filename):
    return send_from_directory(os.path.join("images", year), filename)

@app.route('/thumbnails/images/<year>/<filename>')
def tdp_thumbnail(year, filename):
    return send_from_directory(os.path.join("thumbnails", "images", year), filename)

def tdps(request, groupby=None):
    
    if groupby is None: groupby='year'

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

def send_to_telegram(text):
    if bot is None: return
    coroutine = bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    asyncio.get_event_loop().run_until_complete(coroutine)

@app.get("/")
def homepage():
    return send_from_directory('templates', 'index.html')

@app.get("/tdps/<id>")
def get_tdps_id(id):
    try:
        ref = request.args.get('ref')
        tdp_db = db_instance.get_tdp_by_id(id)
        filepath = f"/TDPs/{tdp_db.year}/{tdp_db.filename}"
        entry_string = db_instance_tdp_views.post_tdp(tdp_db, ref)

        thread = threading.Thread(target=send_to_telegram, args=[entry_string])
        thread.start()

        return render_template('tdp.html', tdp=tdp_db, filepath=filepath)
    except Exception as e:
        print(e)
        # Return generic 404 page
        return render_template('404.html'), 404

@app.get("/query")
def get_query():
    query = request.args.get('q')
    print(f"/query: '{query}'")
    if query is None: query = ''
    return render_template('query.html', initial_query=query)

@app.get("/api/tdps")
def get_api_tdps():
    return db_instance.get_tdps()


""" /api/tdps/<tdp_id>/paragraphs """

@app.get("/api/tdps/<tdp_id>/paragraphs")
def get_api_tdps_id_paragraphs(tdp_id):
    tdp = db_instance.get_tdp_by_id(tdp_id)
    print("[app] Retrieving paragraphs for TDP", tdp.filename)
    paragraphs = db_instance.get_paragraphs_by_tdp(Database.TDP_db(id=tdp_id))
    return [ paragraph.to_json_dict() for paragraph in paragraphs ]

""" /api/query """

@app.get("/api/query")
def get_api_query():
    query = request.args.get('q')
    return search(query)

@app.post("/api/query")
def post_api_query():
    body = request.get_json()
    query = body['query']
    return search(query)

def search(query):

    time_search_start = time.time()
    time_passed = lambda: int(1000*(time.time() - time_search_start))
    time_passed_str = lambda: ("      " + str(time_passed()))[-4:] + " ms"
    log = lambda *args, **kwargs: print(f"[app.search][{time_passed_str()}]", *args, **kwargs)

    db_instance_queries.post_query(query)
    log("Query added to database")

    log("Sentence search")
    time_now = time.time()
    sentences, sentence_scores = search_instance_sentences.search(query, R=0.5, n=100)
    duration_sentence_search = time.time() - time_now
    sentence_ids = [ sentence.id for sentence in sentences ]
    log("Sentence search complete")

    log("Image search")
    time_now = time.time()
    images, image_scores = search_instance_images.search(query, R=0.5, n=15)
    duration_image_search = time.time() - time_now
    image_ids_image_search = [ image.id for image in images ]
    log("Image search complete")

    log("Paragraph search")
    time_now = time.time()
    paragraphs, paragraph_scores = search_instance_paragraphs.search(query, R=0.5, n=15)
    duration_paragraph_search = time.time() - time_now
    log("Paragraph search complete")



    time_now = time.time()
    ## Find the images that belong to the paragraphs
    paragraph_to_images = [ db_instance.get_paragraph_image_mapping_by_paragraph(p) for p in paragraphs ]
    paragraph_to_images = [ m for m in paragraph_to_images if m is not None ]
    image_ids_paragraph_search = [ m.image_id for m in paragraph_to_images ]
    
    ## Add the images from the image search to the images from the paragraph search
    image_ids = image_ids_image_search + image_ids_paragraph_search
    image_ids = functools.reduce(lambda lst, b: lst + [b] if b not in lst else lst, image_ids, []) # Why not simply list(set( .. )) ?
    images = [ db_instance.get_image_by_id(id) for id in image_ids ]
    ordering_images = [ image.id for image in images ]    
    duration_image_stuff = time.time() - time_now



    time_now = time.time()
    # image ids to tdp ids
    image_to_tdp = { image.id : db_instance.get_tdp_id_by_image(image)['id'] for image in images }
    tdp_ids_images = list( image_to_tdp.values() )
        
    # Get paragraphs that the sentences belong to
    paragraph_ids = [ s.paragraph_id for s in sentences ]
    paragraph_ids = functools.reduce(lambda lst, b: lst + [b] if b not in lst else lst, paragraph_ids, [])
    paragraphs = [ db_instance.get_paragraph_by_id(id) for id in paragraph_ids ]    
    # Get TDPs that the paragraphs belong to (and add image tdp ids)
    tdp_ids = [ p.tdp_id for p in paragraphs ] + tdp_ids_images
    tdp_ids = functools.reduce(lambda lst, b: lst + [b] if b not in lst else lst, tdp_ids, []) # Why not simply list(set( .. )) ?
    tdps = [ db_instance.get_tdp_by_id(id) for id in tdp_ids ]
    duration_tdp_stuff = time.time() - time_now


    ### Sentence ordering. Ensure that the most relevant sentences are shown first    
    time_now = time.time()
    ordering = {}
    for sentence in sentences:
        sid, pid = sentence.id, sentence.paragraph_id
        tid = [ p.tdp_id for p in paragraphs if p.id == pid ][0]
        if tid not in ordering: ordering[tid] = {}
        if pid not in ordering[tid]: ordering[tid][pid] = []
        ordering[tid][pid].append(sid)
    # Convert dict to list, since dict ordering is not preserved when jsonified
    # https://github.com/pallets/flask/issues/974
    ordering = [ [tid, [ [pid, s] for pid, s in p.items() ] ] for tid, p in ordering.items()]
    duration_ordering = time.time() - time_now


    query_words = Search.process_text_for_keyword_search(query).split()

    # Convert to dicts
    time_now = time.time()
    tdps = { tdp.id : tdp.to_dict() for tdp in tdps }
    paragraphs = { paragraph.id : paragraph.to_json_dict() for paragraph in paragraphs }
    sentences = { sentence.id : sentence.to_json_dict() for sentence in sentences }
    images = { image.id : image.to_json_dict() for image in images }
    duration_to_dict = time.time() - time_now

    shorten_text = lambda text: text[:100] + "..." if len(text) > 100 else text

    # Send results to telegram
    telegram_time = time.time()
    message = f"Query: \"{query}\"\n\n"
    message += "Top results:\n"
    for i in range(3):
        print("tdp:", ordering[i])
        tid, pids = ordering[i]
        message += f"\n:: {tdps[tid]['team']} {tdps[tid]['year']}\n"
        pid, sids  = pids[0]
        message += f":::: {paragraphs[pid]['title']}\n"
        for sid in sids[:3]:
            message += f"{sentences[sid]['text_raw']}. "
        message += "\n"

        if len(sentences) <= i: break

    message += "\n\n"
    message += f"sentences: {duration_sentence_search:.2f}s | "
    message += f"images: {duration_image_search:.2f}s | "
    message += f"paragraphs: {duration_paragraph_search:.2f}s | "
    message += f"image stuff: {duration_image_stuff:.2f}s\n"

    thread = threading.Thread(target=send_to_telegram, args=[message])
    thread.start()
    log(f"Sent message to telegram in {time.time() - telegram_time:.2f}s")

    return {
        "tdps": tdps,
        "paragraphs": paragraphs,
        "sentences": sentences,
        "images": images,
        "ordering": ordering,
        "ordering_images": ordering_images,
        "image_to_tdp": image_to_tdp,
        "query_words": query_words
    }    


@app.get("/tdps")
def get_tdps():
    groupby = request.args.get('groupby')
    return tdps(request, groupby)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    