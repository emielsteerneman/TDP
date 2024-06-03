# System libraries
import re
from collections import Counter
# Third party libraries
import fitz
import numpy as np
# Local libraries
from MyLogger import logger
from .Semver import Semver
from .Span import Span
from .Image import Image
from data_structures.TDPStructure import TDPStructure
from data_structures.Paragraph import Paragraph
from data_structures.Sentence import Sentence
from text_processing import text_processing as TP
from . import utilities as U

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

"""
Blacklist and notes from old code

# Blacklist because these papers don't contain loadable text. The text seems to be images or something weird..
tdp_blacklist = ["./TDPs/2022/2022_TDP_Luhbots-Soccer.pdf", "./TDPs/2017/2017_TDP_ULtron.pdf"]
# Blacklist because it's almost a perfect duplicate of their 2016 paper
tdp_blacklist.append("./TDPs/2015/2015_ETDP_MRL.pdf") 
# Blacklist because they also have a 2014 ETDP which contains this TDP and more
tdp_blacklist.append("./TDPs/2014/2014_TDP_RoboDragons.pdf") 

tdp_blacklist.append("./TDPs/2011/2011_TDP_MRL.pdf") 
tdp_blacklist.append("./TDPs/2013/2013_TDP_MRL.pdf") 
tdp_blacklist.append("./TDPs/2014/2014_TDP_MRL.pdf") 

# TT27o00
# ./TDPs/2014/2014_ETDP_KIKS.pdf

# WTF is going on with this paper
# ./TDPs/2012/2012_TDP_RoboJackets.pdf
# ./TDPs/2011/2011_TDP_ODENS.pdf

# This paper should work fine with bold method
# ./TDPs/2014/2014_TDP_ACES.pdf <- uses light instead of bold
# ./TDPs/2014/2014_TDP_Owaribito-CU.pdf <- uses just font size

# No Semvers
# ./TDPs/2014/2014_TDP_RFC_Cambridge.pdf
# Unparseable Semvers
# ./TDPs/2009/2009_ETDP_Plasma-Z.pdf
"""

def bounding_boxes_overlap_y(span1: Span, span2: Span) -> float:
    """Check if two spans overlap in the y direction. This is useful to determine if two spans are part of the same
    paragraph.

    Args:
        span1 (Span): The first span
        span2 (Span): The second span

    Returns:
        float: the overlap as a fraction of the total combined height of the two spans
    """
    
    y1, y2 = span1["bbox_absolute"][1], span1["bbox_absolute"][3]
    y3, y4 = span2["bbox_absolute"][1], span2["bbox_absolute"][3]

    if y2 < y3 or y4 < y1:
        return 0.0
    
    overlap = min(y2, y4) - max(y1, y3)
    total_height = max(y2, y4) - min(y1, y3)
    
    return overlap / total_height



def printgroups(groups):
    for group in groups:
        print()
        print("GROUP")
        for span in group:
            print(f"{span['span']['bbox_absolute'][1]:.0f}", span['span']["text"])
            print("B" if span['is_bold'] else " ", "I" if span['is_italic'] else " ", "F" if span['is_weird_font'] else " ", "S" if span['is_larger_size'] else " ", "L" if span['is_left_aligned'] else " ", span["semver_level"] if 0 < span["semver_level"] else " ", "D" if span['has_spacing'] else " ", f"{span['span']['size']:.2f}", f"{span['distance_to_span_above']:.2f}")

def find_paragraph_headers(spans: list[Span]) -> tuple[list[Span], int, int]:
    """ Assumptions. Most paragraph titles
    * are bold or (less common) italic
    * start on the left of the page / column
    * have a font size equal or larger than the normal text
    * Start with a number (Semver)

    Bonus assumption: Most if not all papers have a paragraph title "Introduction"
    """

    x_left_aligned = Counter([ span['bbox'][0] for span in spans ]).most_common(1)[0][0]
    most_common_fontsize = Counter([ span['size'] for span in spans ]).most_common(1)[0][0]
    most_common_font = Counter([ span['font'] for span in spans ]).most_common(1)[0][0]
    most_common_line_height = Counter([ span['bbox'][3] - span['bbox'][1] for span in spans ]).most_common(1)[0][0]

    # logger.info(f"Left aligned x coordinate is {x_left_aligned}")
    # logger.info(f"Most common font size is {most_common_fontsize}")
    # logger.info(f"Most common font is {most_common_font}")
    # logger.info(f"Most common line height is {most_common_line_height}")

    # print(Counter([ span['font'] for span in spans ]).most_common(999))
    # print(Counter([ span['bbox'][0] for span in spans ]).most_common(999))

    abstract_id: int = -1
    references_id: int = 999999  # Assuming there will be no more than 999999 spans in a TDP

    spans_selected = []

    for i_span in range(-1, len(spans)-1):
        i_span += 1
        span = spans[i_span]

        ### Get features
        is_bold = span["bold"]
        is_italic = span["italic"]
        is_weird_font = span['font'] != most_common_font
        is_larger_size = most_common_fontsize < span['size']
        is_left_aligned = abs(span['bbox'][0] - x_left_aligned) < 1
        possible_semver = span['text'].split(" ")[0]
        
        semver_level = 0
        if Semver.is_major_semver(possible_semver) and Semver.parse(possible_semver).A < 100: semver_level = 1
        if Semver.is_minor_semver(possible_semver) and Semver.parse(possible_semver).B < 100: semver_level = 2
        if Semver.is_patch_semver(possible_semver) and Semver.parse(possible_semver).C < 100: semver_level = 3

        # Find the distance to the span above. Need to search backwards because the spans are for whatever reason not always ordered by y-coordinate (page numbers industrial_logistics__2019__Solidus__0.pdf)
        distance_to_span_above, idx = 0, 0
        while distance_to_span_above <= 0 and 0 < i_span - idx:
            distance_to_span_above = span['bbox_absolute'][1] - spans[i_span-idx]['bbox_absolute'][3]
            idx += 1
        has_spacing = most_common_line_height < distance_to_span_above



        # print()
        # print(f"{span['bbox_absolute'][1]:.2f}", span["text"])
        # print("B" if is_bold else " ", "I" if is_italic else " ", "F" if is_weird_font else " ", "S" if is_larger_size else " ", "L" if is_left_aligned else " ", semver_level if 0 < semver_level else " ", "D" if has_spacing else " ", f"{span['size']:.2f}", f"{distance_to_span_above:.2f}")
    


        ### Skip spans that are presumably not paragraph titles
        total = is_bold + is_italic + is_weird_font + is_larger_size + is_left_aligned + (0<semver_level)
        if total == 0: continue
        if span['size'] < most_common_fontsize: continue
        if span['size'] <= most_common_fontsize and not is_bold and not is_italic and semver_level == 0: continue
        if len(span['text']) <= 1: continue
        if span["text"].lower().startswith("fig") or span["text"].lower().startswith("table"): continue

        # Find if there are any overlapping spans on the left of the current span
        has_overlap = False
        for span_other in spans:
            if span['page'] != span_other['page']: continue
            if span['id'] == span_other['id']: continue
            if bounding_boxes_overlap_y(span, span_other) < 0.5: continue
            if span['bbox_absolute'][0] < span_other['bbox_absolute'][0]: continue
            has_overlap = True
            break

        spans_selected.append(
            {
                "span": span,
                "is_bold": is_bold,
                "is_italic": is_italic,
                "is_weird_font": is_weird_font,
                "is_larger_size": is_larger_size,
                "is_left_aligned": is_left_aligned,
                "semver_level": semver_level,
                "has_spacing": has_spacing,
                "distance_to_span_above": distance_to_span_above,
                "has_overlap": has_overlap,
            }
        )

        # print()
        # print(f"{span['bbox_absolute'][1]:.2f}", span["text"])
        # print("B" if is_bold else " ", "I" if is_italic else " ", "F" if is_weird_font else " ", "S" if is_larger_size else " ", "L" if is_left_aligned else " ", semver_level if 0 < semver_level else " ", "D" if has_spacing else " ", f"{span['size']:.2f}", f"{distance_to_span_above:.2f}")
    
    span_abstract, span_reference = None, None
    for span in spans_selected:
        if span_abstract is None and "abstract" in span['span']['text'].lower():
            span_abstract = span['span']
            # logger.info(f"Found abstract at span y={span_abstract['bbox_absolute'][1]}")
        if span_reference is None and "reference" in span['span']['text'].lower():
            span_reference = span['span']
            # logger.info(f"Found references at span y={span_reference['bbox_absolute'][1]}")

    # Remove all selected spans above abstract or below reference
    if span_abstract is not None:
        spans_selected = [ _ for _ in spans_selected if span_abstract['bbox_absolute'][1] <= _['span']['bbox_absolute'][1] ]
    if span_reference is not None:
        spans_selected = [ _ for _ in spans_selected if _['span']['bbox_absolute'][1] <= span_reference['bbox_absolute'][1] ]


    ### Group spans based on features is_bold, is_italic, font, sinze, left_aligned, semver
    features = ['is_bold', 'is_italic', 'is_weird_font', 'is_larger_size', 'semver_level', 'has_overlap']
    groups = []
    for span in spans_selected:
        found = False
        for group in groups:
            if all([ span[feature] == group[0][feature] for feature in features ]):
                group.append(span)
                found = True
                break
        if not found:
            groups.append([ span ])
    
    # printgroups(groups)

    # Find group with semvers
    major_group = [ g for g in groups if g[0]['semver_level'] == 1 and Semver.parse(g[0]['span']['text'].split(" ")[0]).A <= 1 ]
    minor_group = [ g for g in groups if g[0]['semver_level'] == 2 and Semver.parse(g[0]['span']['text'].split(" ")[0]).B <= 1 ]
    patch_group = [ g for g in groups if g[0]['semver_level'] == 3 and Semver.parse(g[0]['span']['text'].split(" ")[0]).C <= 1 ]

    spans_final = []
    if len(major_group) == 1:
        spans_final += [ _['span'] for _ in major_group[0] ]
    if len(major_group) == 1 and len(minor_group) == 1:
        spans_final += [ _['span'] for _ in minor_group[0] ]
    if len(major_group) == 1 and len(minor_group) == 1 and len(patch_group) == 1:
        spans_final += [ _['span'] for _ in patch_group[0] ]

    possible_semver_groups = []
    for major in major_group:
        semver_group1 = [ _['span'] for _ in major ]
        possible_semver_groups.append(semver_group1)
        for minor in minor_group:
            semver_group2 = semver_group1[:] + [ _['span'] for _ in minor ]
            possible_semver_groups.append(semver_group2)
            for patch in patch_group:
                semver_group3 = semver_group2[:] + [ _['span'] for _ in patch ]
                possible_semver_groups.append(semver_group3)

    longest_chain = []

    for group in possible_semver_groups:
        # print("\n==GROUP")
        group = sorted(group, key = lambda s: s['bbox_absolute'][1])
        # for s in group: print(s['text'])
        semvers = [ Semver.parse(s['text'].split(" ")[0]) for s in group ]
        for semver, span in zip(semvers, group):
            semver.span = span

        # print(semvers)
        resolved_semvers = U.resolve_semvers(semvers)
        if len(longest_chain) < len(resolved_semvers):
            longest_chain = [ _.span for _ in resolved_semvers ]

    if len(longest_chain) == 0:
        logger.error(f"Found no semvers")
        raise Exception("No semvers found")

    ### Sort spans_final by y
    longest_chain.sort(key=lambda _: _['bbox_absolute'][1])

    abstract_id = span_abstract['id'] if span_abstract is not None else -1
    references_id = span_reference['id'] if span_reference is not None else 999999
    return longest_chain, abstract_id, references_id

def process_pdf(pdf: str | fitz.Document) -> TDPStructure:
    if isinstance(pdf, str):
        # logger.info(f"Loading PDF from {pdf}")
        pdf: fitz.Document = fitz.open(pdf)

    logger.info(f"Processing {pdf.name}")

    tdp_structure = TDPStructure()

    ### In the following steps, try to filter out as many sentence that are NOT normal paragraph sentences
    # For example, figure descriptions, page numbers, paragraph titles, etc.
    # Place the ids of all these sentences in a single mask
    
    # Extract images and sentences
    spans, images = extract_raw_images_and_spans(pdf)

    if not len(spans):
        logger.info(f"No spans found in {pdf.name}") 
        return tdp_structure
    
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
    paragraph_spans, abstract_id, references_id = find_paragraph_headers(spans)

    # Extend spans_id_mask with found paragraph titles, and abstract id and references id
    spans_id_mask += [ _['id'] for _ in paragraph_spans ]
    
    # Add to mask all spans before and after abstract and references. Anything before abstract is probably the title of the paper and
    # anything after references is probably the bibliography
    spans_id_mask += list(range(0, abstract_id+1))
    spans_id_mask += list(range(references_id, spans[-1]['id'] + 1))

    ### Split up remaining spans into paragraphs
    # Get ids of spans that are paragraph titles
    paragraph_title_ids = np.array([ _['id'] for _ in paragraph_spans ])

    # Create empty bin for each paragraph
    paragraph_bins:list[list[Span]] = [ [] for _ in range(len(paragraph_spans)) ]
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

    for paragraph_bin, paragraph_title in zip(paragraph_bins, paragraph_spans):
        title_raw, title_processed = TP.process_raw_spans([ paragraph_title['text'] ])
        title_raw, title_processed = " ".join(title_raw), " ".join(title_processed)
        
        sentences_raw, sentences_processed = TP.process_raw_spans([ _['text'] for _ in paragraph_bin ])
        
        paragraph = Paragraph(
            text_raw=title_raw,
            text_processed=title_processed,
        )

        tdp_structure.add_paragraph(paragraph)

        for sentence_raw, sentence_processed in zip(sentences_raw, sentences_processed):
            sentence = Sentence(
                text_raw=sentence_raw,
                text_processed=sentence_processed
            )
            paragraph.add_sentence(sentence)
    
    ### Drop Reference paragraph
    if tdp_structure.paragraphs[-1].text_raw.lower() == "references":
        tdp_structure.paragraphs = tdp_structure.paragraphs[:-1]

    """"""""""""""" TDP IS NOW FILLED WITH PARAGRAPHS AND SENTENCES """""""""""""""
    
    ### Find image references
    for paragraph in tdp_structure.paragraphs:
        # Search for "Figure 1" or "Fig. 1" or "Fig 1"
        # TODO also search for "Figure 1a" or "Figure 1.12" ?

        image_references = re.findall(r"(?:figure|fig\.?) (\d+)", paragraph.content_raw().lower())
        image_references = list(set([ int(_) for _ in image_references ]))
        
        referenced_images = [ image for image in images if image['figure_number'] in image_references ]
        paragraph.add_images(referenced_images)

    return tdp_structure
                

def extract_raw_images_and_spans(doc: fitz.Document) -> tuple[list[Span], list[Image]]:
    """Extract all images and spans from a Fitz document object. See the documentation of the Span and Image classes for
    more information about the structure of the returned objects.

    Args:
        doc (fitz.Document): A Fitz document object

    Returns:
        tuple[list[Span], list[Image]]: A tuple containing a list of spans and a list of images
    """

    # logger.info("Extracting images and spans")

    factory_id = 0
    spans, images = [], []

    current_page_height:float = 0.0

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
                        # Needed because of soccer_smallsize__2009__Plasma-Z__0.pdf
                        span["text"] = span["text"].replace(u'\xa0', u' ')

                        # Replace weird characters that python can't really deal with (OMID 2020 4.1 'score')
                        span["text"] = (
                            span["text"].encode("ascii", errors="ignore").decode()
                        )
                        
                        # Replace all whitespace with a single space, and remove leading and trailing whitespace
                        span["text"] = re.sub(r"\s+", " ", span["text"]).strip()
                        # Filter out spans that are now empty (yes it happens) (ACES 2015)
                        if len(span["text"]) == 0: continue
                        
                        # Move y according to the page height
                        x1, y1, x2, y2 = span["bbox"]
                        span["bbox_absolute"] = [x1, y1 + current_page_height, x2, y2 + current_page_height]
                        
                        # Combine with previous span if they have the same y, font, flags, and fontsize
                        if len(spans):
                            previous_span = spans[-1]
                            if (
                                0.9 < bounding_boxes_overlap_y(previous_span, span)
                                and span["font"] == previous_span["font"]
                                and span["flags"] == previous_span["flags"]
                                and abs(span["size"] - previous_span["size"]) < 0.2
                            ):
                                previous_span["text"] += " " + span["text"]
                                previous_span["size"] = max(previous_span["size"], span["size"])
                                continue

                        span["id"] = factory_id
                        span["bold"] = is_bold(span["flags"])
                        span["italic"] = is_italic(span["flags"])
                        span["page"] = i_page
                        spans.append(Span(span))
                        factory_id += 1
        
        current_page_height += page.rect.height

    # logger.info(f"Extracted {len(spans)} spans and {len(images)} images")

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

    # logger.info(f"Matching image with {len(spans)} spans")

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

    # logger.debug(f"Found {len(spans)} spans that could be a description for image")

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
    # logger.info(f"Found {len(spans)} spans for image with text '{description}'")

    return spans, figure_number


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


def is_bold(flags) -> bool:
    return 0 < flags & 2**4

def is_italic(flags) -> bool:
    return 0 < flags & 2**1

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
