#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed May 23 17:41:06 2018

@author: rstyczynski
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt

import getopt
import sys
import os
import re

output = sys.stdout

#
# HTML tags
#
htmlStart = """<html>
    <head>
    <title>%s</title>
    </head>
    <body>"""

htmlStop = """</body></html>"""

htmlImg = """<img src="%s" >"""

htmlVerbatim = """<verbatim>%s</verbatim>"""

htmlParagraphStart = """<p>"""
htmlParagraphStop = """</p>"""

htmlHeader = """<h%d id="%s">%s</h%d>"""

htmlToC = """ %s """
htmlLocalHref = """<a href="#%s">%s</a>"""
htmlBreak = """<br/>"""

htmlTableStart = """<table>"""
htmlTableStop = """</table>"""
htmlTableRowStart = """<tr>"""
htmlTableRowStop = """</tr>"""
htmlTableData = """<td>%s</td>"""


#
# 
#
testName = ''
fullName = '.'
dstDir =   '.'
datetime = False
allResults = False
allResultsFileExt = 'max'

rowsFrom = dt.MINYEAR
rowsTo = dt.MAXYEAR

#
# USAGE
#
def usage():
    
    output.write("""
Prepares summary report for jmeter execution log.""")

    output.write("""
usage: jMeterLogSummary.py """)
    
    output.write("""'--test= [srcDir=] [dstDir=]""")
    output.write("""
    
    Mandatory:
    --log..............filename with log file.
    --test.............test name.
    
    Optional:
    --dstDir...........directory to write html report. default: .
    --from.............select rows starting at from. Format: yyyy-mm-dd hh:mm:ss. default: 1
    --to...............select rows ending at to. Format: yyyy-mm-dd hh:mm:ss. default: 9999
    --datetime.........timestamp in datetime format. default: False /unix epoch/
    """)
    
    output.write("""
    ---
    version 0.1
    rstyczynski@gmail.com, https://github.com/rstyczynski/umc
    """)
   
    
#
# PARAMETER PARSING
#
try:
    opts, args = getopt.getopt( sys.argv[1:], 't', ['test=', 'log=', 'dstDir=', 'probeDir=', 'from=', 'to=', 'datetime', 'allResults'])
except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)
	
for opt, arg in opts:
    if opt in ('--help'):
        usage()
        sys.exit(2)
    elif opt in ('-t', '--test'):
        testName = arg
    elif opt in ('--from'):
        rowsFrom = dt.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S')
    elif opt in ('--to'):
        rowsTo = dt.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S')
    elif opt in ('--log'):
        fullName = arg
    elif opt in ('--dstDir'):
        dstDir = arg
    elif opt in ('--datetime'):
        datetime = True
    elif opt in ('--allResults'):
        allResults = True
        allResultsFileExt = 'all'
    else:
        usage()
        sys.exit(2) 

if testName == '':
    print 'Error: Missing mandatory argument.'
    usage()
    sys.exit(2)
    

#
# CODE
#

#
# prepare dst dir
#
imagesDir = dstDir + '/images'
if not os.path.exists(imagesDir):
    os.makedirs(imagesDir)

#
# read jMeter log
# 
alldf = pd.read_csv(fullName, error_bad_lines=True, skipfooter=0)

alldf.sort_values('timeStamp')

#filter rows by date rowsFrom, rowsTo. Final 3of3 step on row.
if ((rowsFrom > dt.MINYEAR) or (rowsTo < dt.MAXYEAR)):
    alldf = alldf.loc[ (str(rowsFrom) <= alldf['date_time']) & (alldf['date_time']<= str(rowsTo)) ]


#select only results with max threads
if allResults:
    majordf = alldf
else:
    maxThreads=max(alldf.allThreads)    
    majordf = alldf[alldf['allThreads']==75]    
    
#convert timestamp to date format
if not datetime:
    x = pd.to_datetime(majordf['timeStamp'],unit='ms')

#
# Open HTML file for writing
#
htmlStr = htmlStart % (testName)

if allResults:
    htmlStr = htmlStr + ( htmlHeader % (1, 'info1', 'jMeter execution log analysis for ' + testName + ' (all threads)', 1))
else:
    htmlStr = htmlStr + ( htmlHeader % (1, 'info1', 'jMeter execution log analysis for ' + testName + ' (max threads)', 1))
    
#
# execution time
#
htmlStr = htmlStr + ( htmlHeader % (2, 'info1', 'latency distribution', 2))
desc = majordf['elapsed'].describe()
    
htmlStr = htmlStr + htmlTableStart
lines = str(desc).split('\n')
for line in lines:
    htmlStr = htmlStr + htmlTableRowStart
    data = re.sub(' +',' ', line).split(' ')
    htmlStr = htmlStr + (htmlTableData % (data[0]))
    htmlStr = htmlStr + (htmlTableData % (data[1]))
    htmlStr = htmlStr + htmlTableRowStop
htmlStr = htmlStr + htmlTableStop

#
# quantiles
#
htmlStr = htmlStr + ( htmlHeader % (2, 'info2', 'latency quantiles', 2))

quantiles = majordf['elapsed'].quantile([.1, .2, .3, .4, .5, .6, .7, .8, .9, 1])
    
htmlStr = htmlStr + htmlTableStart
lines = str(quantiles).split('\n')
for line in lines:
    htmlStr = htmlStr + htmlTableRowStart
    data = re.sub(' +',' ', line).split(' ')
    htmlStr = htmlStr + (htmlTableData % (data[0]))
    htmlStr = htmlStr + (htmlTableData % (data[1]))
    htmlStr = htmlStr + htmlTableRowStop
htmlStr = htmlStr + htmlTableStop

#
# responses
#
htmlStr = htmlStr + ( htmlHeader % (2, 'info2', 'HTTP response codes', 2))


counts = majordf['responseCode'].value_counts()

htmlStr = htmlStr + htmlTableStart
lines = str(counts).split('\n')
for line in lines:
    htmlStr = htmlStr + htmlTableRowStart
    data = re.sub(' +',' ', line).split(' ')
    htmlStr = htmlStr + (htmlTableData % (data[0]))
    htmlStr = htmlStr + (htmlTableData % (data[1]))
    htmlStr = htmlStr + htmlTableRowStop
htmlStr = htmlStr + htmlTableStop



#
# histogram
# 
htmlStr = htmlStr + ( htmlHeader % (2, 'histogram', 'Response time histogram', 2))
column='Latency'
fig, ax = plt.subplots()
majordf.hist(column, ax=ax, bins=20)
pngFileName = 'jmeter_histogram_' + allResultsFileExt + '_' + column + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)

htmlStr = htmlStr + (htmlImg % ('images/' +     pngFileName))
htmlStr = htmlStr + htmlBreak


#
# threads
#
htmlStr = htmlStr + ( htmlHeader % (2, 'threads', 'Thread count', 2))

fig, ax = plt.subplots(1, figsize=(10,4))
fig.autofmt_xdate()
ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')

column='allThreads'
ax.plot(x, majordf[column])

pngFileName = 'jmeter_series_' + allResultsFileExt + '_' + column + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)

htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak

#
# latency
#
htmlStr = htmlStr + ( htmlHeader % (2, 'response', 'Response time', 2))

fig, ax = plt.subplots(1, figsize=(10,4))
fig.autofmt_xdate()
ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
#ax.set_ylim([0,quantiles[0.9]*2])

column='Latency'
ax.plot(x, majordf[column])

pngFileName = 'jmeter_series_' + allResultsFileExt + '_' + column + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)

htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak


#
# stop html
#
htmlStr = htmlStr + (htmlStop)

#
# Write html file
#
htmlfile = 'jmeter_' + testName + '_' + allResultsFileExt + '.html'
htmlout = open(dstDir + '/' + htmlfile,'w')
htmlout.write(htmlStr)
htmlout.close()


