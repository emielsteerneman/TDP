# save this as app.py
from flask import Flask, render_template, request, send_from_directory
import db
import utilities as U

app = Flask(__name__, template_folder='templates')

@app.route('/TDPs/<year>/<filename>')
def download_file(year, filename):
    return send_from_directory(f'TDPs/{year}', filename, as_attachment=True)

def tdps(request, groupby=None):
    tdps = db.get_tdps()
    tdps = [ dict(_) for _ in tdps ]
    
    if groupby == 'team':
        teams = {}
        for tdp in tdps:
            if tdp['team'] not in teams: teams[tdp['team']] = []
            teams[tdp['team']].append(tdp)
        # Sort each team's TDPs by year
        # for team in teams:
        #     teams[team] = sorted(teams[team], key=lambda x: x['year'])
            
        teams = { team: sorted(teams[team], key=lambda _: _['year'], reverse=True) for team in teams }
        return render_template('tdps.html', data=teams, groupby=groupby)
    
    return render_template('tdps.html', data=tdps, groupby=groupby)

@app.get("/")
def hello():
    return "Hello, World! <br>" + "<br>".join(U.find_all_TDPs())

@app.get("/tdps/<id>")
def get_tdps_id(id):
    tdp = dict(db.get_tdp(id))
    filepath = f"/TDPs/{tdp['year']}/{tdp['filename']}"
    return render_template('tdp.html', tdp=tdp, filepath=filepath)

@app.post("/tdps/<id>")
def post_tdps_id(id):
    print("\n\n")
    print("POST", id)
    print(request.form)
    
    return get_tdps_id(id)

@app.get("/tdps")
def get_tdps():
    groupby = request.args.get('groupby')
    return tdps(request, groupby)

# Add api route to add new tdp to database
@app.post("/tdps")
def tdps_post():
    # Get dataa from request
    filename = request.form.get('filename')
    team = request.form.get('team')
    year = request.form.get('year')
    is_etdp = request.form.get('is_etdp')    
    
    print(is_etdp)
    
    # db.add_tdp(filename, team, year, is_etdp)
    return tdps(request)

db = db.DB()
print(db)