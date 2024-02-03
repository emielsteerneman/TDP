class Span(dict):
    """This class is nothing other than a dict wrapper. It's use is to make the code more readable by enabling type
    hinting / type checking. A span return by the Fitz library has the following keys:
    - bbox: (float x4)            span rectangle
    - origin: (float x2)          the first character's origin
    - font: str                   font name
    - ascender: float             ascender of the font
    - descender: float            descender of the font
    - size: float                 font size
    - flags: int                  font characteristics (bold / italic / etc.)
    - color: int                  text color in sRGB format
    - text: str                   text in ASCII format with duplicate whitespace removed
    The following keys are added manually:
    - id: int                     Unique identifier for the Span within the PDF
    - bold: bool                  Whether the text is bold
    - page: int                   Page number of the PDF

    The following is an example of a span:

    {
             "size" : 9.962599754333496,
            "flags" : 4,
             "font" : "SFRM1000",
            "color" : 0,
         "ascender" : 0.9369999766349792,
        "descender" : -0.32100000977516174,
             "text" : "with the years and with the introduction of REM. The data throughput limit",
           "origin" : (134.7650146484375, 559.7119140625),
             "bbox" : (134.7650146484375, 550.376953125, 480.5667724609375, 562.909912109375),
               "id" : 223,
             "bold" : 0,
             "page" : 4
    }

    For more information, see page 371 https://buildmedia.readthedocs.org/media/pdf/pymupdf/latest/pymupdf.pdf
    """

    def __init__(self, *args, **kwargs):
        super(Span, self).__init__(*args, **kwargs)
