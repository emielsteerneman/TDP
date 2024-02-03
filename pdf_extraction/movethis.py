
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