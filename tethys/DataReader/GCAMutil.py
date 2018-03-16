#!/usr/bin/python
"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

Miscellaneous utilities for the GCAM driver

"""
#import os
import os.path
import re
import string
import subprocess
#import pandas as pd
#import tempfile
#import random

#import gcam_reader

from tethys.Utils.Logging import Logger

## utility functions used in other gcam python code

def gcam_query(batchqfiles, dbxmlfiles, inputdir, outfiles):
    """Run the indicated queries against a dbxml database

    arguments:
      batchqfiles  - List of xml files containing the batch queries to run.  If
                    there is only one, you can just pass the filename.
 
      dbxmlfiles  - List of dbxml file or files to query.  If there is
                    only one, you can just pass the filename.  If
                    there is a list of query files and only a single
                    dbxml, the queries will all be run against the
                    same dbxml.

      inputdir    - Directory where the gcam-driver input files are located.
                    This will typically be provided by the 'general' module.

      outfiles    - List of output files.  should be the same length as
                    the query list.

    """
    mainlog = Logger.getlogger()

    if hasattr(batchqfiles,'__iter__') and not isinstance(batchqfiles, str):
        qlist = batchqfiles
    else:
        qlist = [batchqfiles]

    if hasattr(dbxmlfiles, '__iter__') and not isinstance(batchqfiles, str):
        dbxmllist = dbxmlfiles
        if len(dbxmllist) == 1:
            dbxmllist = dbxmllist*len(qlist)
    else:
        dbxmllist = [dbxmlfiles]*len(qlist)

    if hasattr(outfiles, '__iter__') and not isinstance(batchqfiles, str):
        outlist = outfiles
    else:
        outlist = [outfiles]

    ## check for agreement in lengths of the above lists
    if len(dbxmllist) != len(qlist) or len(outlist) != len(qlist):
        raise RuntimeError("Mismatch in input lengths for gcam_query.") 
    
    
    ModelInterface = './DataReader/QueryGCAMDataBase/ModelInterface/ModelInterface.jar'

    for (query, dbxml, output) in zip(qlist,dbxmllist,outlist):
        mainlog.write('{}  {}\n'.format(query, output), Logger.DEBUG)
        ## make a temporary file
        #try:
        tempquery = rewrite_query(query, dbxml, inputdir, output)
            
        #execlist = ['/bin/env', 'DISPLAY=:%d.0'%disp, ldlibpath, 'java', '-jar', ModelInterface, '-b', tempquery]            
        execlist = ['java', '-jar', ModelInterface, '-b', tempquery]

        subprocess.call(execlist)
            
        #finally:
            #if tempquery:
                #os.unlink(tempquery)

    ## output from these queries goes into csv files.  The names of
    ## these files are in the query file, so it's up to the caller to
    ## know or figure out where its data will be.
    return outlist              # probably redundant, since the list of output files was an argument.


### Some regular expressions used in query_file_rewrite (private):
xmldbloc   = re.compile(r'<xmldbLocation>.*</xmldbLocation>')
outfileloc = re.compile(r'<outFile>.*</outFile>')
qfileloc   = re.compile(r'<queryFile>(.*)</queryFile>')

def rewrite_query(query, dbxml, inputdir, outfile):
    """Rewrite dbxml query file to include the names of the dbxml file and output file and location of query file.

    The names of the input dbxml and output csv files are encoded in
    the query file.  Since we want to be able to set them, we need to
    treat the query file as a template and create a temporary with the
    real file names.  This function creates the temporary and returns
    its name.

    Arguments:
      query  - The 'batch query file'.  This is, unfortunately, not the
               same file as the 'query file', which is mentioned inside
               the 'batch query file'.
      dbxml  - The gcam database output file to run the query against
      inputdir - The location (directory) of the 'query file'.  Generally
               this will be the 'input-data' directory under the gcam-driver
               top-level directory.
     outfile - Name of the output file to put the results in.

    """
    
    tempqueryname = os.path.dirname(outfile) + '/' + os.path.basename(query)

    ## copy the input query file line by line into the temp
    ## file; however, edit the xmldb and output locations to
    ## match the arguments.
    origquery = open(query,"r")
    tempquery = open(tempqueryname,"w")

    dbxmlstr = '<xmldbLocation>' + forward_to_back_slash(os.path.dirname(dbxml)) + '</xmldbLocation>'    
    outfilestr = '<outFile>' + forward_to_back_slash(outfile) + '</outFile>'

    for line in origquery:
        ## replace xml db file name
        line = xmldbloc.sub(dbxmlstr, line)
        ## replace output file name
        line = outfileloc.sub(outfilestr, line)
        ## replace query file name.  This one is a bit more
        ## complicated, as we have to get the base name of the file
        ## from the template
        qfile_match = qfileloc.search(line)
        if(qfile_match):
            ## get the filename
            qfile_template = qfile_match.group(1)
            ## strip off the (probably bogus) directory path and
            ## replace with inputdir
            qfile = os.path.basename(qfile_template)
            qfile = forward_to_back_slash(os.path.dirname(inputdir) + '/' + qfile)
            qfile = '<queryFile>' + qfile + '</queryFile>'
            line = qfileloc.sub(qfile, line)
        tempquery.write(line)
    
    origquery.close()
    tempquery.close()
    
    return tempqueryname


def  forward_to_back_slash(string):
    string = r'\\'.join(string.split('/'))
    return string


## regex for removing trailing commas
## TODO:  Do we need to remove multiple trailing commas?
_trlcomma = re.compile(r',\s*$')
def rm_trailing_comma(line):
    """Remove trailing comma, if any, from a string."""
    return _trlcomma.sub('',line)

## remove trailing whitespace
## TODO:  this could probably be merged with the function above
_trlspc = re.compile(r'\s*$')
def chomp(astring):
    """Remove trailing whitespace, if any, from a string."""
    return _trlspc.sub('',astring)


## Regular expression for detecting a scenario name (private, used in scenariofix)
scen_pattern = re.compile(r'^"[^"]*"') # Beginning of line, followed by a ", followed by any number of non-" chars, followed by a "
def scenariofix(line, newstr="scenario", pat=scen_pattern):
    """Remove commas and excess junk from scenario names.
    
    CSV files returned from the model interface frequently have a
    scenario name as the first field.  The scenario name invariably
    has a comma in it, which really messes up splitting on commas.  We
    almost never use the scenario name for anything, so this function
    transforms it to something benign.

    arguments:
        line   - Line of text read from a GCAM csv output file. 

      newstr   - (arbitrary) string to substitute in place of the
                 scenario field.

         pat   - Regular expression object for detecting a scenario
                 field.  The default value works for the outputs 
                 typically generated by GCAM, so there should be no
                 need to change it; however, if someone produces a 
                 scenario with a sufficiently weird name, a custom
                 pattern can be supplied through this argument.

    """
    return pat.sub(newstr, line)


def rd_rgn_table(filename,skip=1,fltconv=True):
    """Read a csv table of regions and properties.

    The region name should be in the first column.  If there are only
    two columns, then put the result into a dictionary of values by
    region.  If there are more than two columns, put the result into a
    dictionary of lists of values by region.

    Arguments:
      filename - name of the file to process
          skip - number of initial rows to skip (default = 1)
       fltconv - flag: True = convert results to float (DEFAULT); 
                       False = return string values

    Return value: a tuple of two elements.  The first is the table
                   described above.  The second is a list giving the
                   original order of the regions in the file, in case
                   it matters.

    """

    table = {}
    order = []
    with open(filename, "r") as infile:
        for sk in range(skip):
            infile.readline()

        for line in infile:
            line = rm_trailing_comma(line)
            toks = line.split(',')
            rgn  = string.lstrip(string.rstrip(toks[0]))
            data = toks[1:]
            if fltconv:
                data = map(float,data)
            else:
                # Remove leading and trailing whitespace
                data = map(string.lstrip, data)
                data = map(string.rstrip, data)
            if len(data) == 1:
                data = data[0]  # grab the lone value from the list.

            order.append(rgn)
            table[rgn] = data
    
    return (table, order)


# # Added new method of query GCAM database
# 
# def gcam_reader_query_database(settings, outfiles):
#     dbpath = settings.GCAM_DBpath
#     dbfile = settings.GCAM_DBfile
#     conn = gcam_reader.LocalDBConn(dbpath, dbfile)
# 
#     queries = gcam_reader.parse_batch_query(settings.GCAM_query)
#     n  = 0
#     for q in queries:
#         print q.title
#         qp = conn.runQuery(q)
#         create_csv(qp, outfiles[n],q.title)
#         n +=1
#         
# def create_csv(qd,outfile, title):
#     df = pd.DataFrame(qd)
#     df.to_csv(outfile, header=title)
