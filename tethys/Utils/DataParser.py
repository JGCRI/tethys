"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""
import csv
import numpy

# Numpy Parser
def GetArrayCSV(filename, headerNum):
    try:
        f = open(filename, "rU")
        a = numpy.__version__
        if int(a.split('.')[1])>= 10:
            data = numpy.genfromtxt(f, delimiter=",", skip_header=headerNum, filling_values="0")
        else:
            data = numpy.genfromtxt(f, delimiter=",", skiprows=headerNum, filling_values="0")
        return data
        f.close()
    except IOError:
        pass


def GetArrayTXT(filename, headerNum):
    try:
        f = open(filename, "rU")
        a = numpy.__version__
        if int(a.split('.')[1])>= 10:
            data = numpy.genfromtxt(f, delimiter=" ", skip_header=headerNum, filling_values="0")
        else:
            data = numpy.genfromtxt(f, delimiter=" ", skiprows=headerNum, filling_values="0")
        return data
        f.close()
    except IOError:
        pass


# CSV Parser
def getHeader(filename):
    try:
        #f = open(filename, "r")
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=",")
        try:
            header = next(reader)
            if len(header) < 2:
                header = None
            return header
        finally:
            f.close()
    except IOError:
        pass

def getContent(filename, headerNum):
    try:
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=",")
        data = []
        try:
            for i in range(0,headerNum):
                next(reader) # skip header

            # Skip the empty line
            for row in reader:
                if len(row) > 0:   
                    row = row
                    data.append(row)
            return data
        finally:
            f.close()
    except IOError:
        pass

def getContentArray(filename, headerNum):
    try:
        f = open(filename, "rU")
        data = numpy.genfromtxt(f, delimiter=",", skip_header = headerNum, filling_values="0")
        return data
        f.close()
    except IOError:
        pass
     
def getContentNum(filename, headerNum, row0, nrow):
    try:
        count = 0
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=",")
        data = []
        try:
            for i in range(0,headerNum + row0):
                next(reader) # skip header

            # Skip the empty line
            for row in reader:
                if len(row) > 0:
                    row = row
                    data.append(row)
                    count = count + 1
                    if count > nrow:
                        break                    
            return data
        finally:
            f.close()
    except IOError:
        pass
    
        
def getColumn(filename, headerNum, column):
    try:
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=",")
        data = []
        try:
            for i in range(0,headerNum):
                next(reader) # skip header

            # Skip the empty line
            for row in reader:
                if len(row) > 0:
                    row = row
                    data.append(row[column])
            return data
        finally:
            f.close()
    except IOError:
        print("Fail to open file: {}".format(filename))
        pass

def getColumnNum(filename, headerNum, column):
    data = getColumn(filename, headerNum, column)
    column = []
    for i in range(0,len(data)):
        column.append(float(data[i]))
    return column
    
def getNumeric(filename, headerNum, column):
    data = getColumn(filename, headerNum, column)
    return numpy.array(data,dtype='f')

def getNumericRow(filename, headerNum, row):
    content = getContent(filename, headerNum)
    data = content[row]
    return numpy.array(data[row:],dtype='f')


# TXT Parser
def getTXTContent(filename, headerNum):
    try:
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=" ")
        data = []
        try:
            for i in range(0,headerNum):
                next(reader) # skip header

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

def getTXTContentArray(filename, headerNum):
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

    
def getTXTContentlivestock(filename, headerNum): 
    ''' modified for livestock files, 7200 string columns to 720 float columns'''
    try:
        f = open(filename, "rU")
        reader = csv.reader(f, delimiter=" ")
        data = []
        try:
            for i in range(0,headerNum):
                next(reader) # skip header

            # Skip the empty line
            for row in reader:
                if len(row) > 0:
                    row = row
                    if not row[-1]:
                        del row[-1]
                    row = list(map(float, row))
                    temp = []
                    for i in range(0,len(row),10):
                        temp.append(sum(row[i:i+10]))    
                    data.append(temp)
            return data
        finally:
            f.close()
    except IOError:
        pass  
