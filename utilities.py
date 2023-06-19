import os
import utilities as U
import db

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
    return {
        'filename': filename,
        'year': fields[0],
        'is_etdp': fields[1].lower() == 'etdp',
        'team': " ".join(fields[2:])
    }

def find_all_tdps_and_add_to_database(db):
    tdps = find_all_TDPs()
    parsed = [parse_tdp_name(tdp) for tdp in tdps]    
    for tdp in parsed:
        db.add_tdp(tdp['filename'], tdp['team'], tdp['year'], tdp['is_etdp'])
    
if __name__ == "__main__":
    
    db = db.DB()
    
    find_all_tdps_and_add_to_database(db)
        
    rows = [ dict(_) for _ in db.get_tdps() ]
    teams = list(set( [ _['team'] for _ in rows ] ))
    print(sorted(teams))