"""
Exception classes for the Tethys model.
"""

################################################################
#### Tethys exceptions
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


class LoggerError(Error):
    """
    Exception indicating an error in the Logger subsystem.
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class DataError(Error):
    """
    Exception indicating that input data is malformed or inconsistent.
    """
    def __init__(self,msg):
        self.msg = msg

    def __str__(self):
        return self.msg
