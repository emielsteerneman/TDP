import fitz
import numpy as np
import re
import time
import os

from .Semver import Semver
import utilities as U
import PIL

import nltk

nltk.download("stopwords")
nltk.download("wordnet")
from nltk.corpus import stopwords

STOPWORDS_ENGLISH = stopwords.words("english")
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()

from .Span import Span
from .Image import Image

# PyMuPDF documentation: https://buildmedia.readthedocs.org/media/pdf/pymupdf/latest/pymupdf.pdf

"""
TODO:
    1. Filter out black images that sometimes seem to be underneath normal images (ACER 2015) (CMDragons 2014)
    2. Find image description not only on sentence breaks but also on font changes (ACES 2015)
    3. DONE Fix weird FF thing (CMDragons 2014 page 15, "The offense ratio")
    4. Some images are not detected by PyMuPDF (CMDragons 2014 page 14) (2015 RoboDragons figure 6 7 8)
    5. Change groupby_... to mergeby_... Would make the code simpler
    6. Extract references
    7. Fix finding image descriptions when multiple images are next to and underneath each other on the same page (Skuba 2012)
    8. Deal with figure description above figure instead of below (Thunderbots 2015)
    9. Deal with bold text that are clearly paragraph headers but do not have a Semver in front of them (Thunderbots 2015)
   10. Deal with weird unicode characters (OMID 2020, 4.1 Decisoin layer 'score') 
"""

"""
Things to know about Figure descriptions:
    1. They might have a different font size, they might not
    2. "Fig" might be bold, it might not
    3. Under the last line of a Figure description, there is always a whitespace of at least 1.5x (TODO: validate) the line height
    4. The Figure description is always contained on one page
"""

"""
Things to know about paragraph_headers:
    1. They are always bold
    2. They more often than not start with a Semver
    3. They more often than not fit on one line
"""


def extract_raw_images_and_spans(doc: fitz.Document) -> tuple[list[Span], list[Image]]:
    """Extract all images and spans from a Fitz document object. See the documentation of the Span and Image classes for
    more information about the structure of the returned objects.

    Args:
        doc (fitz.Document): A Fitz document object

    Returns:
        tuple[list[Span], list[Image]]: A tuple containing a list of spans and a list of images
    """

    factory_id = 0
    spans, images = [], []

    for i_page, page in enumerate(doc):
        # Disabled flag 0b1 to get rid of the stupid ligature characters such as ﬀ (CMDragons 2014 page 15, "The oﬀense ratio")
        # Find all flags here https://pymupdf.readthedocs.io/en/latest/app1.html#text-extraction-flags
        # See 19.21.1 Structure of Dictionary Outputs (https://buildmedia.readthedocs.org/media/pdf/pymupdf/latest/pymupdf.pdf)
        blocks = page.get_text("dict", flags=6)["blocks"]

        for block in blocks:
            block["page"] = i_page

            # Add image
            if "ext" in block:
                # Skip images that are 'too' small
                if block["width"] < 100 or block["height"] < 100:
                    continue
                block["id"] = factory_id
                images.append(Image(block))
                factory_id += 1

            # Add spans
            else:
                for lines in block["lines"]:  # iterate through the text lines
                    for span in lines["spans"]:  # iterate through the text spans
                        # Replace weird characters that python can't really deal with (OMID 2020 4.1 'score')
                        span["text"] = (
                            span["text"].encode("ascii", errors="ignore").decode()
                        )
                        # Replace all whitespace with a single space, and remove leading and trailing whitespace
                        span["text"] = re.sub(r"\s+", " ", span["text"]).strip()
                        # Filter out spans that are now empty (yes it happens) (ACES 2015)
                        if len(span["text"]) == 0:
                            continue
                        span["id"] = factory_id
                        span["bold"] = is_bold(span["flags"])
                        span["page"] = i_page
                        spans.append(Span(span))
                        factory_id += 1

    return spans, images


def match_image_with_sentences(
    image: Image, spans: list[Span], images: list[Image] = []
) -> tuple[list[Span], int]:
    # Find all spans on the same page as the image
    page: int = image["page"]
    spans = [_ for _ in spans if _["page"] == page]

    # Find all spans that are below the image
    # 5 pixels padding because it can happen that the bottom of the image is part overlapping the text (ACER 2015)
    image_bottom_y: float = (image["bbox"][3] + image["bbox"][1]) // 2  # - 10
    spans = [_ for _ in spans if image_bottom_y < _["bbox"][1]]

    if not spans:
        return [], None

    x1, y1, x2, y2 = image["bbox"]

    # Figure out if the image is overlapping with another image
    image_has_image_overlap = False
    for other in images:
        y1_o, y2_o = other["bbox"][1], other["bbox"][3]
        image_has_image_overlap = (
            image_has_image_overlap or (y1_o < y1 < y2_o) or (y1_o < y2 < y2_o)
        )

    # Figure out if the image is overlapping with a span
    image_has_span_overlap = False
    for other in spans:
        y1_o, y2_o = other["bbox"][1], other["bbox"][3]
        image_has_span_overlap = (
            image_has_span_overlap or (y1_o < y1 < y2_o) or (y1_o < y2 < y2_o)
        )

    # Given that the document width is somewhere between 585 and 615
    # image_centered = 280 < (x1 + x2) // 2 < 320

    # Sort spans by y. This is needed because the order of the spans is not guaranteed (ACES 2015)
    # Also have to look at the bottom coordinate of the span! In KN2C 2015, the dot in "Figure 4." is weird..
    #  'Figure 4' has font size 9, '.' has font size 12. This causes '.' to be ABOVE 'Figure 4' in the list of spans. So weird..
    spans.sort(key=lambda _: _["bbox"][3])

    """ Find a span that has both 'fig' and a number. Find all spans below that 
    span until the next span that is at least 1.5 * lineheight below the previous span. """
    
    span_has_fig = ["fig" in _["text"].lower() for _ in spans]

    if not any(span_has_fig):
        print("VERY WeirD!: ", spans[0]["text"].lower())
        return [], None

    span_fig_index = span_has_fig.index(True)
    span = spans[span_fig_index]

    figure_numbers = re.findall(r"(\d+)", span["text"])
    if not len(figure_numbers):
        print("WHUT: No figure number found in span:", span["text"])
        return [], None

    figure_number = int(figure_numbers[0])

    # Cut off any spans above the figure description span
    spans = spans[span_fig_index:]

    lineheight: float = (
        spans[0]["bbox"][3] - spans[0]["bbox"][1]
    )  # Get the height of the first line under the image
    span_bottoms_y: list[float] = [
        _["bbox"][1] for _ in spans
    ]  # Get all lines under the image (but still on the same page)
    differences = (
        np.diff(span_bottoms_y) > 1.5 * lineheight
    )  # Get the y differences between the lines, and where these exceed 2 * lineheight
    differences: list[bool] = list(differences) + [
        True
    ]  # Add a True at the end, so that there is always a span break
    span_break_at: int = differences.index(True)  # Find the first span break

    # print("miwp", lineheight)
    # print("miwp", span_bottoms_y)
    # print("miwp", differences)
    # print(span_break_at)

    spans = spans[: span_break_at + 1]

    description = " ".join([_["text"] for _ in spans])
    # print("Description:", description, "\n")

    return spans, figure_number


def find_paragraph_headers(sentences: list[Span]) -> tuple[list[list[Span]], int, int]:
    """
    Find all paragraph headers in the document. The assumption is that all paragraph headers are bold and
    start with a Semver. This is not always the case, but it is the case for most TDPs.
    """
    p = lambda *args, **kwargs: print(*(["[fph]"] + list(args)), **kwargs)

    abstract_id: int = -1
    references_id: int = (
        999999  # Assuming there will be no more than 999999 sentences in a TDP
    )

    p()
    p("Finding paragraph headers")

    # Extract all groups that start with a Semver
    semver_groups: list[tuple[Semver, list[Span]]] = []

    selected_sentences = []

    STAGE = 0

    while True:
        if 3 <= STAGE:
            break

        # Find all bold sentences
        if STAGE == 0:
            selected_sentences = [_ for _ in sentences if _["bold"]]
            p("Found", len(selected_sentences), "bold sentences")

        # If there are no bold sentences with valid semvers, try search for sentences with font 'CMBX'
        if STAGE == 1:
            selected_sentences = [_ for _ in sentences if _["font"].startswith("CMBX")]
            p("Found", len(selected_sentences), "CMBX sentences")

        # If there are also no CMBX sentences with valid semvers, try all sentences, excluding
        #  the most common font (which is most likely normal text)
        if STAGE == 2:
            # Count font occurrences
            font_occurrences = {}
            for sentence in sentences:
                if sentence["font"] not in font_occurrences:
                    font_occurrences[sentence["font"]] = 0
                font_occurrences[sentence["font"]] += 1
            # Sort by occurrences
            font_occurrences = sorted(
                [(k, v) for v, k in font_occurrences.items()], reverse=True
            )
            most_common_font = font_occurrences[0][1]

            # Select all sentences that are not the most common font
            selected_sentences = [_ for _ in sentences if _["font"] != most_common_font]
            p("Found", len(selected_sentences), "non-common-font sentences")

        # Group by y
        selected_sentence_lines = groupby_y_fontsize_page(selected_sentences)

        # (Re)set abstract and references ids
        abstract_id: int = -1
        references_id: int = (
            999999  # Assuming there will be no more than 999999 sentences in a TDP
        )

        for group in selected_sentence_lines:
            text = " ".join([_["text"] for _ in group])
            # Find abstract and references while we're at it
            if abstract_id == -1 and "abstract" in text.lower():
                abstract_id = group[0]["id"]
            if references_id == 999999 and "reference" in text.lower():
                references_id = group[0]["id"]
            # Find groups that begin with a Semver
            possible_semver = text.split(" ")[0]
            if Semver.is_semver(possible_semver):
                semver_groups.append([Semver.parse(possible_semver), group])

        if len(semver_groups):
            break

        p("WARNING No semver groups found, trying next stage")
        STAGE += 1

    ############ Let's hope we found some semvers using one of the stages ############

    if not len(semver_groups):
        p("WARNING No semver groups found")
        return [], abstract_id, references_id

    # Set semver id to group id, to keep track
    for i_group, group in enumerate(semver_groups):
        group[0].id = i_group

    p("Found", len(semver_groups), "semver groups")

    if len(semver_groups) == 0:
        p("WARNING No semver groups found")

    semvers = [_[0] for _ in semver_groups]
    semvers = U.resolve_semvers(semvers)

    paragraph_titles = [semver_groups[semver.id][1] for semver in semvers]

    for title in paragraph_titles:
        p("Paragraph title:", " ".join([_["text"] for _ in title]))

    return paragraph_titles, abstract_id, references_id


def find_pagenumbers(sentences):
    # First, group all sentences per line, and find page splits
    groups = groupby_y_fontsize_page(sentences)
    group_pages = [_[0]["page"] for _ in groups]
    difference = np.diff(group_pages)
    page_breaks = np.where(difference != 0)[0]

    groups_top_of_page = [groups[page + 1] for page in page_breaks]
    groups_bottom_of_page = [groups[page] for page in page_breaks]

    has_pagenumbers_top = True
    try:
        for sentences in groups_top_of_page[::2]:
            text = " ".join([_["text"] for _ in sentences])
            page_number_text = int(text.split(" ")[0])
            page_number_data = sentences[0]["page"] + 1
            has_pagenumbers_top = (
                has_pagenumbers_top and page_number_text == page_number_data
            )
            # print("  page_number_text", page_number_text, "page_number_data", page_number_data)
    except:
        has_pagenumbers_top = False
    # print("has_pagenumbers_top", has_pagenumbers_top)

    has_pagenumbers_bottom = True
    try:
        for sentences in groups_bottom_of_page[::2]:
            text = " ".join([_["text"] for _ in sentences])
            page_number_text = int(text.split(" ")[-1])
            page_number_data = sentences[0]["page"] + 1
            has_pagenumbers_top = (
                has_pagenumbers_top and page_number_text == page_number_data
            )
            # print("  page_number_text", page_number_text, "page_number_data", page_number_data)
    except:
        has_pagenumbers_bottom = False
    # print("has_pagenumbers_bottom", has_pagenumbers_bottom)

    pagenumber_groups = []
    if has_pagenumbers_top and has_pagenumbers_bottom:
        pagenumber_groups = groups_top_of_page[::2] + groups_bottom_of_page[::2]
    elif has_pagenumbers_top:
        pagenumber_groups = groups_top_of_page
    elif has_pagenumbers_bottom:
        pagenumber_groups = groups_bottom_of_page

    # Flatten list of lists
    pagenumber_sentences = [_ for group in pagenumber_groups for _ in group]
    return pagenumber_sentences


def groupby_y_fontsize_page(sentences: list[Span]) -> list[list[Span]]:
    groups = []
    for sentence in sentences:
        group_exists = False
        for group in groups:
            same_y = group[0]["bbox"][1] == sentence["bbox"][1]
            same_fontsize = group[0]["size"] == sentence["size"]
            same_page = group[0]["page"] == sentence["page"]
            if same_y and same_fontsize and same_page:
                group.append(sentence)
                group_exists = True
                break
        if not group_exists:
            groups.append([Span])

    return groups


""" // Regression tests """


def is_bold(flags):
    return flags & 2**4


def flags_decomposer(flags):
    """Make font flags human readable.
    See page 372 https://buildmedia.readthedocs.org/media/pdf/pymupdf/latest/pymupdf.pdf
    """
    l = []
    if flags & 2**0:
        l.append("superscript")
    if flags & 2**1:
        l.append("italic")
    if flags & 2**2:
        l.append("serifed")
    else:
        l.append("sans")
    if flags & 2**3:
        l.append("monospaced")
    else:
        l.append("proportional")
    if flags & 2**4:
        l.append("bold")
    return ", ".join(l)


def print_bbox(bbox: list[float]) -> None:
    return f"[x={bbox[0]:.0f}, y={bbox[1]:.0f} | x={bbox[2]:.0f}, y={bbox[3]:.0f}]"
