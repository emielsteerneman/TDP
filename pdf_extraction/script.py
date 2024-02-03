
if __name__ == "__main__":

    tdps = U.find_all_tdps()

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

    # tdps = [tdp for tdp in tdps if "roboteam" in tdp.lower()]

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