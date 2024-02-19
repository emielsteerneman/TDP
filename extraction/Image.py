class Image(dict):
    """ This class is nothing other than a dict wrapper. It's use is to make the code more readable by enabling type hinting / type checking. """

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)