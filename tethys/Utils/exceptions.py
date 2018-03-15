"""
Exception classes for the Tethys model.
"""

################################################################
#### Tethys exceptions:
####
#### Right now the only error we report seems to be file not found.  Add
#### additional exceptions as required.
################################################################

class Error(Exception):
    """
    Base class for tethys package exceptions.
    """
    pass 

class FileNotFoundError(Error):
    """
    Error thrown when Tethys cannot find one of its input files.
    """
    def __init__(self, filename):
        self.fn = filename

    def __str__(self):
        return "Unable to open file:  " + self.fn

class DirectoryNotFoundError(Error):
    """
    Error thrown when an input directory doesn't exist or is invalid.
    """
    def __init__(self, dirname):
        self.dn = dirname

    def __str__(self):
        return "Invalid directory or directory does not exist:  " + self.dn
