FROM ubuntu:latest

RUN apt update && apt upgrade && apt install -y python3.11 python3-pip unzip git

RUN pip install --upgrade pip

# Install Torch without GPU. Saves about 7GB on image size
# https://github.com/UKPLab/sentence-transformers/issues/1409
RUN pip3 install wget numpy PyMuPDF rank_bm25 flask transformers tqdm scikit-learn scipy nltk sentencepiece Pillow python-telegram-bot
RUN pip3 install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-deps sentence-transformers

# Download model weights
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2');"

RUN git clone https://github.com/emielsteerneman/TDP.git /app

WORKDIR /app

COPY TDPs/ TDPs/
COPY database.db database.db

# Force rebuilding from the 'git pull' layer if there have been new commits
# https://stackoverflow.com/questions/56945125/force-docker-to-rebuild-a-layer-based-on-latest-commit-of-a-git-repo
ADD https://api.github.com/repos/emielsteerneman/TDP/git/refs/heads/master version.json
RUN git pull

#RUN python3 download_tdps.py
#RUN python3 fill_database.py

ENTRYPOINT python3 app.py