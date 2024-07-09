# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import shutil
import subprocess
import time
# Third party libraries
# Local libraries
import startup
metadata_client, file_client, _ = startup.get_clients()

pdfs, _ = file_client.list_pdfs()

command = ["pdftohtml", "-c", "-s", "-dataurls"]

FOLDER = "tmp/pdftohtml"
os.makedirs(FOLDER, exist_ok=True)

for i_pdf, pdf in enumerate(pdfs):

    print(f"Converting {i_pdf}/{len(pdfs)} {pdf.team_name.name_pretty}...")
    
    if file_client.html_exists(pdf): continue

    pdf_path_in = file_client.get_pdf(pdf, no_copy=True)
    pdf_path_out = f"{FOLDER}/to_convert.pdf"
    pdf_path_html = pdf_path_out[:-4] + "-html.html"

    try:

        shutil.copyfile(pdf_path_in, pdf_path_out)
        subprocess.call(command + [pdf_path_out], stdout=subprocess.DEVNULL)
        
        file_client.store_html(pdf_path_html, pdf)

        filesize_pdf_mb = os.path.getsize(pdf_path_out) / 1000 / 1000
        filesize_html_mb = os.path.getsize(pdf_path_html) / 1000 / 1000
        ratio = filesize_html_mb / filesize_pdf_mb
        print(f"Converted from {filesize_pdf_mb:.2f} MB to {filesize_html_mb:.2f} MB ({ratio:.2f}x)")

    except Exception as e:
        pass

    finally:
        # Remove files
        os.remove(pdf_path_out)
        os.remove(pdf_path_html)