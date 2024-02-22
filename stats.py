import utilities as U
from extraction import extractor as E
from data_structures import TDP
import matplotlib.pyplot as plt
import pickle
from MyLogger import logger
import numpy as np

# tdps = U.find_all_tdps()
# tdps = [E.process_pdf(tdp) for tdp in tdps]
# # Create pickle file
# with open('tdps.pkl', 'wb') as f:
#     pickle.dump(tdps, f)
# exit()

# Load pickle file
logger.info("Loading TDPs from pickle file..")
file = open("tdps.pkl", "rb")
tdps = pickle.load(file)
logger.info(f"Loaded {len(tdps)} TDPs from pickle file")

tdps = [tdp for tdp in tdps if tdp is not None]

records = []

for tdp in tdps:

    try:
        n_paragraphs = len(tdp.paragraphs)
        n_sentences_per_paragraph = [len(paragraph.sentences) for paragraph in tdp.paragraphs]
        n_characters_per_paragraph = [len(paragraph.content_raw()) for paragraph in tdp.paragraphs]
        n_sentences_total = sum(n_sentences_per_paragraph)
        n_chacacters_total = sum(n_characters_per_paragraph)

        record = {
            "team": tdp.team,
            "year": tdp.year,
            "league": tdp.league,
            "n_paragraphs": n_paragraphs,
            "n_sentences_per_paragraph": n_sentences_per_paragraph,
            "n_characters_per_paragraph": n_characters_per_paragraph,
            "n_sentences_total": n_sentences_total,
            "n_characters_total": n_chacacters_total,
        }
        records.append(record)
    except Exception as e:
        logger.error(f"Error with TDP : {tdp} : {e}")
        continue

# # Histogram of sentences per tdp
# n_sentences_total = [record["n_sentences_total"] for record in records]
# plt.hist(n_sentences_total, bins=30)
# plt.title("Sentences per TDP")
# plt.show()

# # Histogram of characters per tdp
# n_characters_total = [record["n_characters_total"] for record in records]
# plt.hist(n_characters_total, bins=30)
# plt.title("Characters per TDP")
# plt.show()

# # Histogram of sentences per paragraph
# n_sentences_per_paragraph = [record["n_sentences_per_paragraph"] for record in records]
# n_sentences_per_paragraph = [item for sublist in n_sentences_per_paragraph for item in sublist]
# plt.hist(n_sentences_per_paragraph, bins=50)
# plt.title("Sentences per Paragraph")
# plt.show()

# # Histogram of characters per paragraph
# n_characters_per_paragraph = [record["n_characters_per_paragraph"] for record in records]
# n_characters_per_paragraph = [item for sublist in n_characters_per_paragraph for item in sublist]
# plt.hist(n_characters_per_paragraph, bins=50)
# plt.title("Characters per Paragraph")
# plt.show()

# mean_sentences_per_paragraph = np.mean(n_sentences_per_paragraph)
# std_sentences_per_paragraph = np.std(n_sentences_per_paragraph)

# outlier_threshold = mean_sentences_per_paragraph + 6 * std_sentences_per_paragraph

# print(f"Mean sentences per paragraph: {mean_sentences_per_paragraph}")
# print(f" Std sentences per paragraph: {std_sentences_per_paragraph}")
# print(f"           Outlier threshold: {outlier_threshold}")
# print("\n\n")

# for tdp in tdps:
#     if tdp is None: continue
#     for paragraph in tdp.paragraphs:
#         if outlier_threshold < len(paragraph.sentences):
#             teamyear = f"{tdp.team} {tdp.year}".rjust(35)
#             print(f"{teamyear}    {len(paragraph.sentences)}    {paragraph.text_raw}")

paragraphs_tdps = [ [paragraph, tdp] for tdp in tdps for paragraph in tdp.paragraphs if len(paragraph.sentences) ]
paragraphs_tdps = sorted(paragraphs_tdps, key=lambda p: len(p[0].sentences), reverse=True)
for paragraph, tdp in paragraphs_tdps:
    teamyear = f"{tdp.team} {tdp.year}".rjust(35)
    print(f"{teamyear}    {len(paragraph.sentences)}    {paragraph.text_raw}")