import fitz
from MyLogger import logger
import numpy as np
import re

from .Semver import Semver
import utilities as U

from .Span import Span
from .Image import Image

from data_structures.TDP import TDP
from data_structures.Paragraph import Paragraph
from data_structures.Sentence import Sentence

from text_processing import text_processing as TP

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



def process_pdf(pdf: str | fitz.Document) -> TDP:
    if isinstance(pdf, str):
        pdf: fitz.Document = fitz.open(pdf)

    logger.info(f"Processing {pdf.name}")

    ### In the following steps, try to filter out as many sentence that are NOT normal paragraph sentences
    # For example, figure descriptions, page numbers, paragraph titles, etc.
    # Place the ids of all these sentences in a single mask
    
    # Extract images and sentences
    spans, images = extract_raw_images_and_spans(pdf)

    if not len(spans):
        logger.warning(f"No spans found in {pdf.name}") 
        return
    
    # Create mask that references all spans that are not normal text spans (figure descriptions, page numbers, paragraph titles, etc)
    spans_id_mask:list[int] = []

    
    ### Match images with spans that make up their description
    # Thus, sentences such as "Fig. 5. Render of the proposed redesign of the front assembly"
    logger.info("======== match_image_with_spans ========")
    for image in images:
        image_spans, figure_number = match_image_with_spans(image, spans)
        image['figure_number'] = figure_number
        image['description'] = " ".join([ _['text'] for _ in image_spans ])
        spans_id_mask += [ _['id'] for _ in image_spans ]


    ### Find all sentences that are pagenumbers
    # For example, "Description of the Warthog Robotics SSL 2015 Project    5" or "6    Warthog Robotics"
    logger.info("======== find_pagenumbers ========")
    pagenumber_spans = find_pagenumbers(spans)
    # Extend spans_id_mask with found pagenumbers
    spans_id_mask += [ _['id'] for _ in pagenumber_spans ]       


    ### Find all sentences that can make up a paragraph title
    logger.info("======== find_paragraph_headers ========")
    paragraph_titles, abstract_id, references_id = find_paragraph_headers(spans)

    # Extend spans_id_mask with found paragraph titles, and abstract id and references id
    for span_group in paragraph_titles:
        spans_id_mask += [ _['id'] for _ in span_group ]
    # Add to mask all spans before and after abstract and references. Anything before abstract is probably the title of the paper and
    # anything after references is probably the bibliography
    spans_id_mask += list(range(0, abstract_id+1))
    spans_id_mask += list(range(references_id, spans[-1]['id'] + 1))

    tdp = TDP()
    try:
        tdp = U.parse_tdp_name(pdf.name)
    except Exception as e:
        logger.warning(f"Could not parse TDP name from {pdf.name}. Error: {str(e)}")


    ### Split up remaining spans into paragraphs
    # Get ids of spans that are paragraph titles
    paragraph_title_ids = np.array([ _[0]['id'] for _ in paragraph_titles ])

    # Create empty bin for each paragraph
    paragraph_bins:list[list[Span]] = [ [] for _ in range(len(paragraph_titles)) ]
    # Move each unmasked sentence into the correct bin
    for span in spans:
        # Skip any masked sentence (paragraph titles / pagenumbers / figure descriptions / etc)
        if span['id'] in spans_id_mask: continue
        # Find index of bin that this sentence belongs to
        bin_mask = list(span['id'] < paragraph_title_ids) + [True]
        bin_idx = list(bin_mask).index(True)-1
        # Skip sentences that appear before the first paragraphs, such as the paper title or abstract
        if bin_idx < 0: continue
        # Place sentence into correct bin
        paragraph_bins[bin_idx].append(span)

    for paragraph_bin, paragraph_title in zip(paragraph_bins, paragraph_titles):
        title_raw, title_processed = TP.process_raw_spans([ _['text'] for _ in paragraph_title ])
        title_raw, title_processed = " ".join(title_raw), " ".join(title_processed)
        
        sentences_raw, sentences_processed = TP.process_raw_spans([ _['text'] for _ in paragraph_bin ])
        
        paragraph = Paragraph(
            text_raw=title_raw,
            text_processed=title_processed,
        )

        tdp.add_paragraph(paragraph)

        for sentence_raw, sentence_processed in zip(sentences_raw, sentences_processed):
            sentence = Sentence(
                text_raw=sentence_raw,
                text_processed=sentence_processed
            )
            paragraph.add_sentence(sentence)
    
    """"""""""""""" TDP IS NOW FILLED WITH PARAGRAPHS AND SENTENCES """""""""""""""
    
    ### Find image references
    for paragraph in tdp.paragraphs:
        # Search for "Figure 1" or "Fig. 1" or "Fig 1"
        # TODO also search for "Figure 1a" or "Figure 1.12" ?

        image_references = re.findall(r"(?:figure|fig\.?) (\d+)", paragraph.content_raw().lower())
        image_references = list(set([ int(_) for _ in image_references ]))
        
        referenced_images = [ image for image in images if image['figure_number'] in image_references ]
        paragraph.add_images(referenced_images)

    return tdp    
                

def extract_raw_images_and_spans(doc: fitz.Document) -> tuple[list[Span], list[Image]]:
    """Extract all images and spans from a Fitz document object. See the documentation of the Span and Image classes for
    more information about the structure of the returned objects.

    Args:
        doc (fitz.Document): A Fitz document object

    Returns:
        tuple[list[Span], list[Image]]: A tuple containing a list of spans and a list of images
    """

    logger.info("Extracting images and spans")

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

    logger.info(f"Extracted {len(spans)} spans and {len(images)} images")
    return spans, images


def match_image_with_spans(
    image: Image, spans: list[Span], images: list[Image] = []
) -> tuple[list[Span], int]:
    """This function tries to find a description for an image by matching the image with spans. Additional images can be
    provided to help with the matching process. The function returns a list of spans that are a description for the image,
    and the figure number of the image.

    Args:
        image (Image): The image to find a description for
        spans (list[Span]): A list of spans
        images (list[Image], optional): A list of images for which the spans might be a description as well

    Returns:
        tuple[list[Span], int]: The list of spans that are a description for the image, and the figure number of the image
    """

    logger.info(f"Matching image with {len(spans)} spans")

    # Find all spans on the same page as the image
    page: int = image["page"]
    spans = [_ for _ in spans if _["page"] == page]

    # Find all spans that are below the image
    # n pixels padding because it can happen that the bottom of the image is part overlapping the text (ACER 2015)
    image_bottom_y: float = (image["bbox"][3] + image["bbox"][1]) // 2  # - 10
    spans = [_ for _ in spans if image_bottom_y <= _["bbox"][1]]

    if not spans:
        logger.info("No spans found that could be a description for image. Breaking")
        return [], None

    # x1, y1, x2, y2 = image["bbox"]

    # # Figure out if the image is overlapping with another image
    # image_has_image_overlap = False
    # for other in images:
    #     y1_o, y2_o = other["bbox"][1], other["bbox"][3]
    #     image_has_image_overlap = (
    #         image_has_image_overlap or (y1_o < y1 < y2_o) or (y1_o < y2 < y2_o)
    #     )

    # # Figure out if the image is overlapping with a span
    # image_has_span_overlap = False
    # for other in spans:
    #     y1_o, y2_o = other["bbox"][1], other["bbox"][3]
    #     image_has_span_overlap = (
    #         image_has_span_overlap or (y1_o < y1 < y2_o) or (y1_o < y2 < y2_o)
    #     )

    # Given that the document width is somewhere between 585 and 615
    # image_centered = 280 < (x1 + x2) // 2 < 320

    logger.debug(f"Found {len(spans)} spans that could be a description for image")

    # Sort spans by y. This is needed because the order of the spans is not guaranteed (ACES 2015)
    # Also have to look at the bottom coordinate of the span! In KN2C 2015, the dot in "Figure 4." is weird..
    #  'Figure 4' has font size 9, '.' has font size 12. This causes '.' to be ABOVE 'Figure 4' in the list of spans. So weird..
    # spans.sort(key=lambda _: _["bbox"][3])

    # Find a span that has both 'fig' and a number. Find all spans below that 
    # span until the next span that is at least 1.5 * lineheight below the previous span

    span_has_fig = ["fig" in _["text"].lower() for _ in spans]

    if not any(span_has_fig):
        logger.info("No spans found with the word 'fig' in it. Breaking")
        return [], None

    span_fig_index = span_has_fig.index(True)
    span_fig = spans[span_fig_index]

    figure_numbers = re.findall(r"(\d+)", span_fig["text"])
    if not len(figure_numbers):
        logger.info(f"No figure number found in span with text '{span_fig['text']}'. Breaking")
        return [], None

    figure_number = int(figure_numbers[0])

    logger.debug(f"Found first span below image with figure number {figure_number} and text '{span_fig['text']}'")

    # Cut off any spans above the figure description span
    # TODO this might cut off subfigure descriptions located between the image and the figure description. Should capture those as well

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
    # Capture all spans until the first span break. Drop the rest
    spans = spans[: span_break_at + 1]

    description = " ".join([_["text"] for _ in spans])
    logger.info(f"Found {len(spans)} spans for image with text '{description}'")

    return spans, figure_number


def find_paragraph_headers(spans: list[Span]) -> tuple[list[list[Span]], int, int]:
    """Find all paragraph headers in the document. The assumption is that all paragraph headers are bold and
    start with a Semver. This is not always the case, but it is the case for most TDPs.

    Args:
        spans (list[Span]): A list of spans

    Returns:
        list[list[Span]]: A list of paragraph spans which are assumed to be paragraph headers
        int: The id of the span that indicates the start of the abstract paragraph
        int: The id of the span that indicates the start of the references paragraph
    """

    logger.info(f"Finding paragraph headers for {len(spans)} spans")

    abstract_id: int = -1
    references_id: int = 999999  # Assuming there will be no more than 999999 spans in a TDP
    
    """
    The following stages are used to find paragraph headers. If a stage does not find any paragraph headers, the next
    stage is tried. The stages are as follows:
    0. Find all bold spans
    1. If there are no bold spans with valid semvers, try search for spans with font 'CMBX'
    2. If there are also no CMBX spans with valid semvers, try all spans, excluding the most common font (which is most likely normal text)
    """

    # Extract all groups that start with a Semver
    semver_groups: list[tuple[Semver, list[Span]]] = []
    span_candidates: list[Span] = []
    STAGE = 0

    while True:
        # Find all bold spans
        if STAGE == 0:
            span_candidates = [_ for _ in spans if _["bold"]]
            logger.debug(f"Stage 0 : Found {len(span_candidates)} bold spans")

        # If there are no bold spans with valid semvers, try search for spans with font 'CMBX'
        if STAGE == 1:
            span_candidates = [_ for _ in spans if _["font"].startswith("CMBX")]
            logger.debug(f"Stage 1 : Found {len(span_candidates)} CMBX spans")

        # If there are also no CMBX spans with valid semvers, try all spans, excluding the most common font (which is most likely normal text)
        if STAGE == 2:
            # Count font occurrences
            font_occurrences = {}
            for span in spans:
                if span["font"] not in font_occurrences:
                    font_occurrences[span["font"]] = 0
                font_occurrences[span["font"]] += 1
            # Sort by occurrences
            font_occurrences = sorted(
                [(k, v) for v, k in font_occurrences.items()], reverse=True
            )
            most_common_font = font_occurrences[0][1]

            # Select all spans that are not the most common font
            span_candidates = [_ for _ in spans if _["font"] != most_common_font]
            logger.debug("Stage 2 : Found", len(span_candidates), "non-common-font spans")

        # Group spans by y, fontsize, and page
        span_groups: list[list[Span]] = groupby_y_fontsize_page(span_candidates)

        # (Re)set abstract and references ids
        abstract_id: int = -1
        references_id: int = 999999  # Assuming there will be no more than 999999 spans in a TDP

        for span_group in span_groups:
            text = " ".join([_["text"] for _ in span_group])
            # Find abstract and references while we're at it
            if abstract_id == -1 and "abstract" in text.lower():
                abstract_id = span_group[0]["id"]
            if references_id == 999999 and "reference" in text.lower():
                references_id = span_group[0]["id"]
            # Find groups that begin with a Semver
            possible_semver = text.split(" ")[0]
            if Semver.is_semver(possible_semver):
                semver_groups.append([Semver.parse(possible_semver), span_group])

        if len(semver_groups):
            logger.debug(f"Found {len(semver_groups)} semver groups in stage {STAGE}. Breaking gracefully")
            break

        if abstract_id != -1:
            logger.debug(f"Found abstract at span {abstract_id}")
        if references_id != 999999:
            logger.debug(f"Found references at span {references_id}")
        
        STAGE += 1

        if STAGE == 3: break

    ############ Let's hope we found some semvers using one of the stages ############

    if not len(semver_groups):
        logger.info("No semver groups found. Breaking")
        return [], abstract_id, references_id

    # Set semver id to group id, to keep track
    for i_group, span_group in enumerate(semver_groups):
        span_group[0].id = i_group

    logger.info(f"Found {len(semver_groups)} semver groups to work with after stages")

    semvers = [_[0] for _ in semver_groups]
    semvers = U.resolve_semvers(semvers)

    paragraph_titles = [semver_groups[semver.id][1] for semver in semvers]

    logger.debug(f"Found {len(paragraph_titles)} paragraph titles")
    for title in paragraph_titles:
        logger.debug(f"-- { ' '.join([_['text'] for _ in title]) }")

    return paragraph_titles, abstract_id, references_id


def find_pagenumbers(spans: list[Span]):
    # First, group all spans and find page splits
    groups: list[list[Span]] = groupby_y_fontsize_page(spans)
    group_pages: list[int] = [_[0]["page"] for _ in groups]
    # Find indices where the page changes
    page_breaks: list[bool] = np.where(np.diff(group_pages) != 0)[0]

    # Get all the span groups that are at the top or bottom of a page
    groups_top_of_page = [groups[page + 1] for page in page_breaks]
    groups_bottom_of_page = [groups[page] for page in page_breaks]

    has_pagenumbers_top = True
    try:
        for spans in groups_top_of_page[::2]:
            text = " ".join([_["text"] for _ in spans])
            page_number_text = int(text.split(" ")[0])
            page_number_data = spans[0]["page"] + 1
            has_pagenumbers_top = (
                has_pagenumbers_top and page_number_text == page_number_data
            )
    except:
        has_pagenumbers_top = False

    has_pagenumbers_bottom = True
    try:
        for spans in groups_bottom_of_page[::2]:
            text = " ".join([_["text"] for _ in spans])
            page_number_text = int(text.split(" ")[-1])
            page_number_data = spans[0]["page"] + 1
            has_pagenumbers_top = (
                has_pagenumbers_top and page_number_text == page_number_data
            )
    except:
        has_pagenumbers_bottom = False

    logger.info(f"Pagenumbers at top: {has_pagenumbers_top}, bottom: {has_pagenumbers_bottom}")

    pagenumber_groups = []
    if has_pagenumbers_top and has_pagenumbers_bottom:
        pagenumber_groups = groups_top_of_page[::2] + groups_bottom_of_page[::2]
    elif has_pagenumbers_top:
        pagenumber_groups = groups_top_of_page
    elif has_pagenumbers_bottom:
        pagenumber_groups = groups_bottom_of_page

    # Flatten list of lists
    pagenumber_spans = [_ for group in pagenumber_groups for _ in group]
    return pagenumber_spans

def groupby_y_fontsize_page(spans: list[Span]) -> list[list[Span]]:
    groups = []
    for span in spans:
        group_exists = False
        for group in groups:
            same_y = group[0]["bbox"][1] == span["bbox"][1]
            same_fontsize = group[0]["size"] == span["size"]
            same_page = group[0]["page"] == span["page"]
            if same_y and same_fontsize and same_page:
                group.append(span)
                group_exists = True
                break
        if not group_exists:
            groups.append([span])

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