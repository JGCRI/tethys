"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


This is the class to define logging process.

"""
import os, sys
import tethys.Utils.exceptions

_mainlog = None


def _setmainlog(logger):
    """
    Set the main logger for use throughout the rest of the model.
    
    :param logger: Logger object to use as the main log.
    
    If the main log already exists, a message will be printed to stderr.
    """

    global _mainlog
    if _mainlog is not None:
        sys.stderr.write('WARNING: Resetting main log.')
        _mainlog.close()
        
    _mainlog = logger


def _shutdown():
    """
    Shut down the main log.

    This should be the last thing you do before model exit.
    """

    global _mainlog
    if _mainlog is not None:
        _mainlog.close()
        _mainlog = None


def _str2lvl(string):
    """
    Helper function for converting strings to logging levels.

    This should only be needed in the logger constructor.
    """
    
    ## lookup table for converting strings to levels.
    ## We have to wrap this in a helper function because we can't evaluate
    ## these constants until the logger class is fully constructed.
    s2l = {'DEBUG':Logger.DEBUG, 'INFO':Logger.INFO,
           'WARNING':Logger.WARNING, 'ERROR':Logger.ERROR}
    return s2l[string]


        
class Logger(object):
    """
    Provide logging services.

    There is nothing stopping you from creating your own logs, but the intended
    use is for the model to create a single logger on startup, which other 
    classes and functions will access with `getlogger()`.

    The logger recognizes the following log levels:
    DEBUG
    INFO
    WARNING
    ERROR

    Logger configuration is specified in the [Logger] section of the configuration input file. The following keys are currently recognized:
    logdir(OPTIONAL) direcotry to put the log file in. (Default is './logs')
    filename (REQUIRED) name of the log file.
    MinLogLevel (OPTIONAL) minimum logging level to include in logs (Default is DEBUG)
    MinScreenLevel (OPTIONAL) minimum logging level to print to terminal (Default is INFO)
    
    """
    
    
    ## definition of logging levels
    (DEBUG, INFO, WARNING, ERROR) = (0, 1, 2, 3) 
    
    def __init__(self, config):
        """
        Logger class constructor.

        :param config: Dictionary of configuration options. Typically this will 
            be parsed from an ini-format input file.
        """

        self.terminal = sys.stdout
        self.logdir = config.get('logdir', 'logs')
        self.filename = os.path.join(self.logdir, config['filename'])
        self.minlvl = config.get('MinLogLevel', Logger.DEBUG)
        self.minterm = config.get('MinScreenLevel', Logger.INFO)

        ## The levels we got are probably strings.  Convert them to level values
        if type(self.minlvl) is str:
            self.minlvl = _str2lvl(self.minlvl)
        if type(self.minterm) is str:
            self.minterm = _str2lvl(self.minterm)
        
        self.clvl = self.minlvl


        ## Create the directory if necessary
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)
        
        self.log = open(self.filename, 'w')


    @staticmethod
    def getlogger():
        """
        Get the main logger object.
        """
        
        if _mainlog is None:
            from tethys.Utils.exceptions import LoggerError
            raise LoggerError('Trying to access main logger before it has been created.')
        return _mainlog

    
    def write(self, message, lvl = None):
        """
        Write a message to the log.

        Each message has a "log level" that indicates the urgency of the message.
        If the log level of the message is higher than the minimum specified in the
        configuration, then the message will be written to the log; otherwise it will
        be silently ignored.  If the log level is higher than the screen level 
        specified in the configuration, the message will be additionally be written 
        to the terminal.  Finally, warning and error messages will have "WARNING" and
        "ERROR", respectively, prefixed to them.

        By default, a message will have its log level set to the logger's current 
        log level (settable with the setlevel() method).  Specifying the level explicitly
        allows the level to be set on a one-off basis without resetting the default.
        """

        if lvl is None:
            lvl = self.clvl
        
        if lvl < self.minlvl:
            return

        if lvl == Logger.WARNING:
            _message = "WARNING:  " + message
        elif lvl == Logger.ERROR:
            _message = "ERROR:  " + message
        else:
            _message = message
                        
        self.log.write(_message)
        if lvl >= self.minterm:
            self.terminal.write(_message) 


    def setlevel(self, newlvl):
        """
        Set the default logging level.

        :param newlvl: The new default logging level.  This should be one of the log
            level constants defined in the Logger class.
        :return: The old default logging level.

        The logging level for write() calls with no logging level explicitly specified
        will be set to `newlvl`.  The old level is returned so that it can be reset
        to its original value if desired.  Note that explicitly specifying a logging 
        level in write() will override this setting.
        """

        oldlvl = self.clvl
        self.clvl = newlvl
        return oldlvl 

    
    def close(self):
        """
        Close the file associated with a logger.
        """

        self.log.close()


    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass
    
