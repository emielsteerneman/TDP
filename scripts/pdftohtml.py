import os
import shutil
import subprocess

def pdfs_to_html():
    """Convert all TDP pdf files to html files"""
     
    PDFTOHTML_FOLDER_NAME = "pdftohtml_folder"
        
    command = ["pdftohtml", "-c", "-s", "-dataurls"]
    for i_tdp_db, tdp_db in enumerate(tdps):
        try:
            # Create folder
            os.makedirs(PDFTOHTML_FOLDER_NAME, exist_ok=True)
            print(f"Converting {i_tdp_db}/{len(tdps)} {tdp_db.filename}...")
            filepath = f"TDPs/{tdp_db.year}/{tdp_db.filename}"
            shutil.copyfile(filepath, f"{PDFTOHTML_FOLDER_NAME}/{tdp_db.filename}")
            
            subprocess.call(command + [f"{PDFTOHTML_FOLDER_NAME}/{tdp_db.filename}"], stdout=subprocess.DEVNULL)
            
            # wer.pdf is converted to wer-html.html. Copy to static/tdps/id/tdp.html
            filename_html_in = f"{PDFTOHTML_FOLDER_NAME}/{tdp_db.filename.split('.')[0]}-html.html"
            filename_html_out = f"static/tdps/{tdp_db.id}/tdp.html"
            os.makedirs(os.path.dirname(filename_html_out), exist_ok=True)
            shutil.copyfile(filename_html_in, filename_html_out)
        except Exception as e:
            print(f"Error converting {tdp_db.filename}: {e}")
        finally:
            # Clean up folder
            shutil.rmtree(f"{PDFTOHTML_FOLDER_NAME}")
