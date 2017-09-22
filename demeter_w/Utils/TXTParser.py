"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""

import csv
import numpy

def getContent(filename, headerNum):
    try:
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=" ")
        data = []
        try:
            for i in range(0,headerNum):
                reader.next() # skip header

            # Skip the empty line
            for row in reader:
                if len(row) > 0:
                    row = row
                    if not row[-1]:
                        del row[-1]
                    data.append(row)
            return data
        finally:
            f.close()
    except IOError:
        pass

def getContentArray(filename, headerNum):
    try:
        f = open(filename, "rU")
        a = numpy.__version__
        if int(a.split('.')[1])>= 10:
            data = numpy.genfromtxt(f, delimiter=" ", skip_header = headerNum, filling_values="0")
        else:
            data = numpy.genfromtxt(f, delimiter=" ", skiprows = headerNum, filling_values="0")   
        return data
        f.close()
    except IOError:
        pass 

    
def getContentlivestock(filename, headerNum): 
    ''' modified for livestock files, 7200 string columns to 720 float columns'''
    try:
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=" ")
        data = []
        try:
            for i in range(0,headerNum):
                reader.next() # skip header

            # Skip the empty line
            for row in reader:
                if len(row) > 0:
                    row = row
                    if not row[-1]:
                        del row[-1]
                    row = map(float, row)
                    temp = []
                    for i in range(0,len(row),10):
                        temp.append(sum(row[i:i+10]))    
                    data.append(temp)
            return data
        finally:
            f.close()
    except IOError:
        pass    