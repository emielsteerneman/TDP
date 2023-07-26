import fitz
import numpy as np
import re
import time
import os 

import Database
db_instance = Database.Database("database.db")
# from Database import instance as db_instance
from Embeddings import instance as embed_instance
import fill_database_tests
from Semver import Semver
import utilities as U
import PIL

import nltk
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
STOPWORDS_ENGLISH = stopwords.words('english')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

""" Both these classes are nothing other than dicts, but they are used to make the code more readable by enabling type hinting and type()"""
class Sentence(dict):
    def __init__(self, *args, **kwargs):
        super(Sentence, self).__init__(*args, **kwargs)
class Image(dict):
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)

"""
TODO:
    1. Filter out black images that sometimes seem to be underneath normal images (ACER 2015) (CMDragons 2014)
    2. Find image descirption not only on sentence breaks but also on font changes (ACES 2015)
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

def print_bbox(bbox:list[float]) -> None:
    return f"[x={bbox[0]:.0f}, y={bbox[1]:.0f} | x={bbox[2]:.0f}, y={bbox[3]:.0f}]"

def extract_images_and_sentences(doc:fitz.Document) -> tuple[list[Sentence], list[Image]]:
    factory_id = 0
    sentences, images = [], []
        
    for i_page, page in enumerate(doc):
        # Disabled flag 0b1 to get rid of the stupid ligature characters such as ﬀ (CMDragons 2014 page 15, "The oﬀense ratio")
        # Find all flags here https://pymupdf.readthedocs.io/en/latest/app1.html#text-extraction-flags
        blocks = page.get_text("dict", flags=6)["blocks"]

        for block in blocks: 
            block['page'] = i_page
            
            # Add image
            if "ext" in block: 
                # Skip images that are 'too' small
                if block["width"] < 100 or block["height"] < 100: continue
                block['id'] = factory_id
                images.append(Image(block))
                factory_id += 1
            else:
            # Add lines
                for lines in block["lines"]:  # iterate through the text lines
                    for span in lines["spans"]:  # iterate through the text spans
                        # Replace weird characters that python can't really deal with (OMID 2020 4.1 'score')
                        span['text'] = span['text'].encode("ascii", errors="ignore").decode()
                        # Replace all whitespace with a single space, and remove leading and trailing whitespace
                        span['text'] = re.sub(r"\s+", " ", span['text']).strip()
                        # Filter out sentences that are now empty (yes it happens) (ACES 2015)
                        if len(span['text']) == 0: continue
                        span['id'] = factory_id
                        span['bold'] = is_bold(span["flags"])
                        span['page'] = i_page
                        sentences.append(Sentence(span))
                        factory_id += 1
    
    return sentences, images

def store_image(image:Image, filepath:str) -> None:
    extension = image['ext']
    if 101 < len(filepath): filepath = filepath[:64] + "___" + filepath[-34:]
    if not filepath.endswith(extension): 
        filepath += "." + extension
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as file:
        file.write(image['image'])

    ## Create thumbnail
    image = PIL.Image.open(filepath)
    image.thumbnail((256, 256))
    filepath_thumb = os.path.join(THUMBNAILS_DIR, filepath)
    filepath_thumb = os.path.normpath(filepath_thumb)
    os.makedirs(os.path.dirname(filepath_thumb), exist_ok=True)
    image.save(filepath_thumb)
    
    return filepath
    
def match_image_with_sentences(image:list, sentences:list[Sentence], images:list[Image] = []) -> tuple[list[Sentence], int]:
    # print(f"[match_image_with_sentences] {image['id']}")
    # Find all sentenecs on the same page as the image
    page:int = image['page']
    sentences = [ _ for _ in sentences if _['page'] == page ]

    # Find all sentences that are below the image
    # 5 pixels padding because it can happen that the bottom of the image is part overlapping the text (ACER 2015)
    image_bottom_y:float = (image['bbox'][3]+image['bbox'][1])//2# - 10
    sentences = [ _ for _ in sentences if image_bottom_y < _['bbox'][1] ]
    
    x1, y1, x2, y2 = image['bbox']
    
    # Figure out if the image is overlapping with another image
    image_has_image_overlap = False
    for other in images:
        y1_o, y2_o = other['bbox'][1], other['bbox'][3]
        image_has_image_overlap = image_has_image_overlap or (y1_o < y1 < y2_o) or (y1_o < y2 < y2_o)
    
    # Figure out if the image is overlapping with a sentence
    image_has_sentence_overlap = False
    for other in sentences:
        y1_o, y2_o = other['bbox'][1], other['bbox'][3]
        image_has_sentence_overlap = image_has_sentence_overlap or (y1_o < y1 < y2_o) or (y1_o < y2 < y2_o)
    
    # Given that the document width is somewhere between 585 and 615
    image_centered = 280 < (x1 + x2) // 2 < 320
    
    # print("  Image    image overlap:", image_has_image_overlap)
    # print("  Image sentence overlap:", image_has_sentence_overlap)
    # print("  Image         centered:", image_centered)
    
    if not sentences: 
        return [], None
        
    # Sort sentences by y. This is needed because the order of the sentences is not guaranteed (ACES 2015)
    # Also have to look at the bottom of the sentence! In KN2C 2015, the dot in "Figure 4." is weird..
    #  'Figure 4' has font size 9, '.' has font size 12. This causes '.' to be ABOVE 'Figure 4' in the list of sentences. So weird..
    sentences.sort(key=lambda _: _['bbox'][3])

    # print("\n\n==", "Page", image['page'], image_bottom_y, image['id'])
    # for sentence in sentences:
    #     print(sentence['id'], print_bbox(sentence['bbox']), f"{sentence['size']:.2f}", f"'{sentence['text'].lower()}'")

    sentence_has_fig = [ "fig" in _['text'].lower() for _ in sentences ]
    
    if not any(sentence_has_fig):
        print("VERY WeirD!: ", sentences[0]['text'].lower())
        return [], None
        
    sentence_fig_index = sentence_has_fig.index(True)
    sentence = sentences[sentence_fig_index]
    
    figure_numbers = re.findall(r'(\d+)', sentence['text'])
    if not len(figure_numbers):
        print("WHUT: No figure number found in sentence:", sentence['text'])
        return [], None
    
    figure_number = int(figure_numbers[0])
    
    # print("Description sentence:", sentences[sentence_fig_index]['text'])
    # print("Figure number:", figure_number)

    # Cut off any sentences above the figure description sentence
    sentences = sentences[sentence_fig_index:]

    lineheight:float = sentences[0]['bbox'][3] - sentences[0]['bbox'][1]  # Get the height of the first line under the image
    sentence_bottoms_y:list[float] = [ _['bbox'][1] for _ in sentences ]  # Get all lines under the image (but still on the same page)
    differences = np.diff(sentence_bottoms_y) > 1.5 * lineheight          # Get the y differences between the lines, and where these exceed 2 * lineheight
    differences:list[bool] = list(differences) + [True]                   # Add a True at the end, so that there is always a sentence break
    sentence_break_at:int = differences.index(True)                       # Find the first sentence break
    
    # print("miwp", lineheight)
    # print("miwp", sentence_bottoms_y)
    # print("miwp", differences)
    # print(sentence_break_at)
    
    sentences = sentences[:sentence_break_at+1]
    
    description = " ".join([ _['text'] for _ in sentences ])
    # print("Description:", description, "\n")
    
    # filename = re.sub(r"[^a-zA-Z0-9]", "", description.lower())
    # filename = "extracted_images" + "/" + str(image['id']) + "_" + filename + "." + image['ext']
    # with open(filename, "wb") as file:
    #     file.write(image['image'])
    
    return sentences, figure_number

def find_paragraph_headers(sentences:list[Sentence]) -> tuple[list[list[Sentence]], int, int]:
    """
    Find all paragraph headers in the document. The assumption is that all paragraph headers are bold and 
    start with a Semver. This is not always the case, but it is the case for most TDPs.
    """
    p = lambda *args, **kwargs: print(* (['[fph]']+list(args)), **kwargs)

    abstract_id:int = -1
    references_id:int = 999999 # Assuming there will be no more than 999999 sentences in a TDP

    p()
    p("Finding paragraph headers")


    # Extract all groups that start with a Semver
    semver_groups:list[tuple[Semver, list[Sentence]]] = []

    selected_sentences = []
    
    STAGE = 0
    
    while True:
        if 3 <= STAGE: break

        # Find all bold sentences
        if STAGE == 0:
            selected_sentences = [ _ for _ in sentences if _['bold'] ]
            p("Found", len(selected_sentences), "bold sentences")

        # If there are no bold sentences with valid semvers, try search for sentences with font 'CMBX'
        if STAGE == 1:
            selected_sentences = [ _ for _ in sentences if _['font'].startswith('CMBX') ]
            p("Found", len(selected_sentences), "CMBX sentences")

        # If there are also no CMBX sentences with valid semvers, try all sentences, excluding
        #  the most common font (which is most likely normal text)
        if STAGE == 2:
            # Count font occurrences
            font_occurrences = {}
            for sentence in sentences:
                if sentence['font'] not in font_occurrences: font_occurrences[sentence['font']] = 0
                font_occurrences[sentence['font']] += 1
            # Sort by occurrences
            font_occurrences = sorted([ (k, v) for v, k in font_occurrences.items() ], reverse=True)
            most_common_font = font_occurrences[0][1]
            
            # Select all sentences that are not the most common font
            selected_sentences = [ _ for _ in sentences if _['font'] != most_common_font ]
            p("Found", len(selected_sentences), "non-common-font sentences")
        
        # Group by y
        selected_sentence_lines = groupby_y_fontsize_page(selected_sentences)
        
        # (Re)set abstract and references ids
        abstract_id:int = -1
        references_id:int = 999999 # Assuming there will be no more than 999999 sentences in a TDP

        for group in selected_sentence_lines:
            text = " ".join([ _['text'] for _ in group ])
            # Find abstract and references while we're at it            
            if abstract_id == -1 and "abstract" in text.lower(): abstract_id = group[0]['id']
            if references_id == 999999 and "reference" in text.lower(): references_id = group[0]['id']
            # Find groups that begin with a Semver
            possible_semver = text.split(" ")[0]
            if Semver.is_semver(possible_semver):
                semver_groups.append([Semver.parse(possible_semver), group])
    
        if len(semver_groups): break

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

    semvers = [ _[0] for _ in semver_groups ]
    semvers = U.resolve_semvers(semvers)
    
    paragraph_titles = [ semver_groups[semver.id][1] for semver in semvers ]

    for title in paragraph_titles:
        p("Paragraph title:", " ".join([ _['text'] for _ in title ]))

    return paragraph_titles, abstract_id, references_id

def find_pagenumbers(sentences):
    # First, group all sentences per line, and find page splits
    groups = groupby_y_fontsize_page(sentences)
    group_pages = [ _[0]['page'] for _ in groups ]
    difference = np.diff(group_pages)
    page_breaks = np.where(difference != 0)[0]
    
    groups_top_of_page = [ groups[page+1] for page in page_breaks ]
    groups_bottom_of_page = [ groups[page] for page in page_breaks ]
    
    has_pagenumbers_top = True
    try:
        for sentences in groups_top_of_page[::2]:
            text = " ".join([ _['text'] for _ in sentences ])
            page_number_text = int(text.split(" ")[0])
            page_number_data = sentences[0]['page'] + 1
            has_pagenumbers_top = has_pagenumbers_top and page_number_text == page_number_data
            # print("  page_number_text", page_number_text, "page_number_data", page_number_data)
    except:
        has_pagenumbers_top = False
    # print("has_pagenumbers_top", has_pagenumbers_top)
    
    has_pagenumbers_bottom = True    
    try:
        for sentences in groups_bottom_of_page[::2]:
            text = " ".join([ _['text'] for _ in sentences ])
            page_number_text = int(text.split(" ")[-1])
            page_number_data = sentences[0]['page'] + 1
            has_pagenumbers_top = has_pagenumbers_top and page_number_text == page_number_data
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
    pagenumber_sentences = [ _ for group in pagenumber_groups for _ in group ]
    return pagenumber_sentences
    
def groupby_y_fontsize_page(sentences:list[Sentence]) -> list[list[Sentence]]:
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
            groups.append([sentence])
            
    return groups

""" Regression tests to ensure that changes to the code do not break the output of the code """

def test_paragraph_titles(tdp, paragraph_titles):
    # Return True by default
    if tdp not in fill_database_tests.test_cases_paragraphs: return True
    
    titles = []
    for sentences in paragraph_titles:
        titles.append(" ".join([ _['text'] for _ in sentences ]))
    if fill_database_tests.test_cases_paragraphs[tdp] != titles:
        for a, b in zip(fill_database_tests.test_cases_paragraphs[tdp], titles):
            if a != b:
                print("Error!")
                print(f"|{a}|")
                print(f"|{b}|")
        raise Exception(f"Test case paragraphs failed for {tdp}!")

def test_image_description(tdp, images):
    # Return True by default
    if tdp not in fill_database_tests.test_cases_figure_descriptions: return True

    image_descriptions = [ _['description'] for _ in images ]
    if fill_database_tests.test_cases_figure_descriptions[tdp] != image_descriptions:
        for a, b in zip(fill_database_tests.test_cases_figure_descriptions[tdp], image_descriptions):
            if a != b:
                print("Error!")
                print(a)
                print(b)
        raise Exception(f"Test case figure descriptions failed for {tdp}!")       

def test_pagenumbers(tdp, pagenumber_sentences):
    if tdp not in fill_database_tests.test_cases_pagenumbers: return True
    text_pagenumbers = [ _['text'] for _ in pagenumber_sentences ]
    if fill_database_tests.test_cases_pagenumbers[tdp] != text_pagenumbers:
        raise Exception(f"Test case pagenumbers failed for {tdp}!")

""" // Regression tests """

def is_bold(flags): return flags & 2 ** 4

def flags_decomposer(flags):
    """Make font flags human readable."""
    l = []
    if flags & 2 ** 0: l.append("superscript")
    if flags & 2 ** 1: l.append("italic")
    if flags & 2 ** 2: l.append("serifed")
    else:
        l.append("sans")
    if flags & 2 ** 3:
        l.append("monospaced")
    else:
        l.append("proportional")
    if flags & 2 ** 4:
        l.append("bold")
    return ", ".join(l)

def split_text_into_sentences(text:str) -> list[str]:
    ### Split into sentences
    ## However, don't split on numbers, because those are often part of the sentence

    REGEX_OFFSET = 1 # Don't split at the end of the regex match, since that includes the first capital letter of the next sentence
    
    # Find all the indices of the split points
    # Note: Can't use re.split() because it drops the delimiters
    split_indices = np.array([ m.end() for m in re.finditer(f'[!?\.] [A-Z0-9]', text) ])
    # Append start and end of text
    split_indices = [REGEX_OFFSET] + list(split_indices) + [len(text)+REGEX_OFFSET]
    # Remove duplicates and resort (can happen when " + [len(text)+REGEX_OFFSET]" adds a duplicate )
    split_indices = sorted(list(set(split_indices)))
    
    """ Debugging
    indicator = " " * len(text)
    for i in split_indices: indicator = indicator[:i-REGEX_OFFSET] + "#" + indicator[i+1-REGEX_OFFSET:]
    # split text  up into blocks of length 80
    blocks1 = [ text     [i:i+80] for i in range(0, len(text),      80) ]
    blocks2 = [ indicator[i:i+80] for i in range(0, len(indicator), 80) ]
    # print
    for a, b in zip(blocks1, blocks2): print(f"{a}\n{b}")
    """
    
    sentences = []
    for a, b in zip(split_indices, split_indices[1:]):
        sentence = text[a-REGEX_OFFSET:b-REGEX_OFFSET].strip()
        sentences.append(sentence)
    
    return sentences

def process_text_for_keyword_search(text:str) -> str:
    text = text.lower()
    words = re.findall(r'\w+', text)                                    # Extract words
    words = [ word for word in words if 1 < len(word)]                  # Remove single characters (slighly iffy, since it also removes useful things like 'x' and 'y')
    words = [ word for word in words if word not in STOPWORDS_ENGLISH ] # Filter out stopwords
    words = [ lemmatizer.lemmatize(word) for word in words ]            # Lemmatize
    
    sentence = " ".join(words)
    return sentence

tdps = U.find_all_TDPs()

# tdps = list(fill_database_tests.test_cases_paragraphs.keys())

# tdps = ["./TDPs/2014/2014_ETDP_CMDragons.pdf"]
# tdps = ["./TDPs/2012/2012_ETDP_Skuba.pdf"] # Very difficult to parse images and some paragraphs (stacked images,non-bold paragraphs, double paragraphs, uses "reference" instead of "references")
# tdps = ["./TDPs/2015/2015_TDP_ACES.pdf"] # First image overlaps with description.. very weird
# tdps = ["./TDPs/2015/2015_TDP_SSH.pdf"]

# tdps = ["./TDPs/2015/2015_ETDP_RoboDragons.pdf"]
# tdps = ["./TDPs/2020/2020_TDP_OMID.pdf"]

# All TDPS that use F-font
# tdps = ["./TDPs/2020/2020_ETDP_TIGERs_Mannheim.pdf", "./TDPs/2016/2016_ETDP_TIGERs_Mannheim.pdf", "./TDPs/2020/2020_TDP_ITAndroids.pdf", "./TDPs/2013/2013_TDP_RoboJackets.pdf", "./TDPs/2013/2013_TDP_TIGERs_Mannheim.pdf", "./TDPs/2022/2022_TDP_ITAndroids.pdf"]
# TDP that uses TT** font
# tdps = ["./TDPs/2014/2014_ETDP_KIKS.pdf"]


""" Load all TDPs to be parsed """
# Blacklist because these papers don't contain loadable text. The text seems to be images or something weird..
tdp_blacklist = ["./TDPs/2022/2022_TDP_Luhbots-Soccer.pdf", "./TDPs/2017/2017_TDP_ULtron.pdf"]
# Blacklist because it's almost a perfect duplicate of their 2016 paper
tdp_blacklist.append("./TDPs/2015/2015_ETDP_MRL.pdf") 
# Blacklist because they also have a 2014 ETDP which contains this TDP and more
tdp_blacklist.append("./TDPs/2014/2014_TDP_RoboDragons.pdf") 

tdp_blacklist.append("./TDPs/2011/2011_TDP_MRL.pdf") 
tdp_blacklist.append("./TDPs/2013/2013_TDP_MRL.pdf") 
tdp_blacklist.append("./TDPs/2014/2014_TDP_MRL.pdf") 


tdps = [ _ for _ in tdps if _ not in tdp_blacklist ]


# tdps = ["./TDPs/2010/2010_TDP_Botnia_Dragon_Knights.pdf", "./TDPs/2011/2011_TDP_ODENS.pdf", "./TDPs/2011/2011_ETDP_RoboDragons.pdf", "./TDPs/2011/2011_TDP_RoboDragons.pdf"]


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


IMAGES_DIR = "./images"
THUMBNAILS_DIR = "./thumbnails"

total_tdps_added = 0
total_paragraphs_added = 0
total_sentences_added = 0
total_images_added = 0

t_start = time.time()
for i_tdp, tdp in enumerate(tdps):
    try:
        # print(tdp, end="                                    \r")
        # Open TDP pdf with PyMuPDF        
        doc = fitz.open(tdp)
        tdp_instance = U.parse_tdp_name(tdp)

        # Create directory for images if it doesn't exist
        images_dir = os.path.join(IMAGES_DIR, tdp_instance.year)
        os.makedirs( images_dir, exist_ok=True)
        
        ### In the following steps, try to filter out as many sentence that are NOT normal paragraph sentences
        # For example, figure descriptions, page numbers, paragraph titles, etc.
        # Place the ids of all these sentences in a single mask
        
        # Extract images and sentences
        sentences, images = extract_images_and_sentences(doc)

        print("\n\n\n")
        print(f"{tdp.ljust(50)} | TDP {i_tdp+1}/{len(tdps)} | {len(sentences)} sentences | {len(images)} images")
        
        if not len(sentences):
            print(f"\nWarning: No sentences found in {tdp}\n")
            continue
        
        # Create mask that references all sentences that are not normal paragraph sentences
        sentences_id_mask:list[int] = []
        
        ### Match images with sentences that make up their description
        # Thus, sentences such as "Fig. 5. Render of the proposed redesign of the front assembly"
        image_to_sentences:list[Image, list[Sentence]] = []
        for image in images:
            image_sentences, figure_number = match_image_with_sentences(image, sentences, images)
            image['figure_number'] = figure_number
            image['description'] = " ".join([ _['text'] for _ in image_sentences ])
            
            file_description = process_text_for_keyword_search(image['description']).replace(" ", "_")
            figure_number_str = str(figure_number) if figure_number is not None else "None"
            filename = f"{image['id']}_{tdp_instance.year}_{tdp_instance.team}_{figure_number_str}_{file_description}"
            filepath = os.path.join(images_dir, filename)
            filepath = store_image(image, filepath)
            image['filepath'] = filepath
            
            # image_to_sentences.append([image, image_sentences])
            # Extend sentences_id_mask with found image descriptions
            sentences_id_mask += [ _['id'] for _ in image_sentences ]
        
        
        
        ### Find all sentences that are pagenumbers
        # For example, "Description of the Warthog Robotics SSL 2015 Project    5" or "6    Warthog Robotics"
        pagenumber_sentences = find_pagenumbers(sentences)
        # Extend sentences_id_mask with found pagenumbers
        sentences_id_mask += [ _['id'] for _ in pagenumber_sentences ]       
        
        ### Find all sentences that can make up a paragraph title
        paragraph_titles, abstract_id, references_id = find_paragraph_headers(sentences)

        # Extend sentences_id_mask with found paragraph titles, and abstract id and references id
        for sentence_group in paragraph_titles:
            sentences_id_mask += [ _['id'] for _ in sentence_group ]
        # Add to mask all sentences before and after abstract and references
        sentences_id_mask += list(range(0, abstract_id+1))
        sentences_id_mask += list(range(references_id, sentences[-1]['id'] + 1))

        #### Run tests if possible
        test_paragraph_titles(tdp, paragraph_titles)
        test_image_description(tdp, images)
        test_pagenumbers(tdp, pagenumber_sentences)   
      
        ### Split up remaining sentences into paragraphs
        # Get ids of sentences that are paragraph titles
        paragraph_title_ids = np.array([ _[0]['id'] for _ in paragraph_titles ])
        # Create empty bin for each paragraph
        paragraph_bins:list[list[Sentence]] = [ [] for _ in range(len(paragraph_titles)) ]
        # Move each unmasked sentence into the correct bin
        for sentence in sentences:
            # Skip any masked sentence (paragraph titles / pagenumbers / figure descriptions / etc)
            if sentence['id'] in sentences_id_mask: continue
            # Find index of bin that this sentence belongs to
            bin_mask = list(sentence['id'] < paragraph_title_ids) + [True]
            bin_idx = list(bin_mask).index(True)-1
            # Skip sentences that appear before the first paragraphs, such as the paper title or abstract
            if bin_idx < 0: continue
            # Place sentence into correct bin
            paragraph_bins[bin_idx].append(sentence)

        paragraphs = []
        for paragraph_bin, paragraph_title in zip(paragraph_bins, paragraph_titles):
            title = " ".join([ _['text'] for _ in paragraph_title ])
            text_raw = "\n".join([ _['text'] for _ in paragraph_bin ])
            
            # Replace multiple whitespace with single whitespace
            text_raw = re.sub(r"\s+", " ", text_raw)
            # Get rid of newlines and reconstruct hyphenated words
            text_raw = text_raw.replace("-\n", "")
            text_raw = text_raw.replace("\n", " ")
            
            # references = re.findall(r"\[[0-9]+\]", text_raw) TODO
            sentences_raw = split_text_into_sentences(text_raw)
            sentences_processed = [ process_text_for_keyword_search(_) for _ in sentences_raw ]
            
            text_processed = " ".join(sentences_processed)
                        
            paragraphs.append({
                'title': title,
                'text_raw': text_raw,
                'text_processed': text_processed,
                'sentences_raw': sentences_raw,
                'sentences_processed': sentences_processed,
            })
        
        ### Find image references
        for i_paragraph, paragraph in enumerate(paragraphs):
            paragraph['images'] = []
            text = paragraph['text_raw']
            # Search for "Figure 1" or "Fig. 1" or "Fig 1"
            # TODO also search for "Figure 1a" or "Figure 1.12" ?
            
            image_references = re.findall(r"(?:figure|fig\.?) (\d+)", text.lower())
            image_references = list(set([ int(_) for _ in image_references ]))
            
            # if len(image_references):
            #     print()
            #     print(paragraph['title'])
            #     print(re.findall(r"(figure|fig\.?) (\d+)", text.lower()))
            
            for ref in image_references:
                for i_image, image in enumerate(images):
                    if image['figure_number'] == ref:
                        paragraph['images'].append(image)
            

        # for p in paragraphs:
        #     print(f"{p['title'].rjust(50)}: {len(p['images'])}")
        
        """ Store everything in the database """
        
        # First, store TDP
        # print(tdp)
        tdp_instance = U.parse_tdp_name(tdp)
        tdp_instance = db_instance.post_tdp(tdp_instance)
        total_tdps_added += 1

        # Then store each paragraph and its sentences and its images
        for i_paragraph, paragraph in enumerate(paragraphs):
            print(f"* {tdp.ljust(50)} | TDP {i_tdp+1}/{len(tdps)} - paragraph {i_paragraph+1}/{len(paragraphs)}", end="    \r")
            embedding = embed_instance.embed(paragraph['text_processed'])
            paragraph_db = Database.Paragraph_db( tdp_id=tdp_instance.id, title=paragraph['title'], text_raw=paragraph['text_raw'], text_processed=paragraph['text_processed'], embedding=embedding )
            
            paragraph_db = db_instance.post_paragraph(paragraph_db)
            total_paragraphs_added += 1
            
            # Store all sentences
            sentences_db = []
            for text_raw, text_processed in zip(paragraph['sentences_raw'], paragraph['sentences_processed']):
                embedding = embed_instance.embed(text_processed)
                sentence_db = Database.Sentence_db( paragraph_id=paragraph_db.id, text_raw=text_raw, text_processed=text_processed, embedding=embedding )
                sentences_db.append(sentence_db)
            # TODO why don't I have a function to store just one sentence?
            ids = [ _.paragraph_id for _ in sentences_db ]
            db_instance.post_sentences(sentences_db)
            total_sentences_added += len(sentences_db)
            
            # Store all images and mappings
            for image in paragraph['images']:
                text_raw = image['description']
                text_processed = process_text_for_keyword_search(text_raw)
                embedding = embed_instance.embed(text_processed)
                image_db = Database.Image_db(filename=image['filepath'], text_raw=text_raw, text_processed=text_processed, embedding=embedding)
                image_db = db_instance.post_image(image_db)
                total_images_added += 1

                # Store paragraph to image mapping
                mapping_db = Database.Paragraph_Image_Mapping_db(paragraph_id=paragraph_db.id, image_id=image_db.id)
                mapping_db = db_instance.post_paragraph_image_mapping(mapping_db)
            
                      
    except Exception as e:
        print(f"\nError with TDP {tdp}\n")
        print(e)
        # raise e

print(f"Finished in {int(time.time() - t_start)} seconds.")
print(f"Total TDPs added: {total_tdps_added}")
print(f"Total paragraphs added: {total_paragraphs_added}")
print(f"Total sentences added: {total_sentences_added}")
print(f"Total images added: {total_images_added}")