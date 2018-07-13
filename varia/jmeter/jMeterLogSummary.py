#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed May 23 17:41:06 2018

@author: rstyczynski
"""

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt

import getopt
import sys
import os
import re
import fileinput
import subprocess

output = sys.stdout

mpl.rcParams['agg.path.chunksize'] = 10000

#
# HTML tags
#
htmlStart = """<html>
    <head>
    <title>%s</title>
    </head>
    <body>"""

htmlStop = """</body></html>"""

htmlImg = """<img src="%s" width="900">"""

htmlVerbatimStart = """<verbatim>"""
htmlVerbatimStop = """</verbatim>"""
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

rowsFrom = ''
rowsTo = ''

imgZoom = 1

renderPlantUML = True

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
    
    Optional:
    --test.............test name. default: log name
    --allResults.......compute all results. defualt: only max threads
    --dstDir...........directory to write html report. default: .
    --from.............select rows starting at from. Format: yyyy-mm-dd hh:mm:ss. default: 1
    --to...............select rows ending at to. Format: yyyy-mm-dd hh:mm:ss. default: 9999
    --datetime.........timestamp in datetime format. default: False /unix epoch/
    --imgZoom..........image zoom factor. default=1
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
    opts, args = getopt.getopt( sys.argv[1:], 't', ['test=', 'log=', 'dstDir=', 'probeDir=', 'from=', 'to=', 'imgZoom=','datetime', 'allResults'])
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
        if testName == '':
            testName = os.path.basename(fullName).split('.')[0]
    elif opt in ('--dstDir'):
        dstDir = arg
    elif opt in ('--datetime'):
        datetime = True
    elif opt in ('--allResults'):
        allResults = True
        allResultsFileExt = 'all'
    elif opt in ('--imgZoom'):
        imgZoom = int(arg)
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
reportDir = dstDir + '/' + testName
if not os.path.exists(reportDir):
    os.makedirs(reportDir)
    
imagesDir = reportDir + '/images'
if not os.path.exists(imagesDir):
    os.makedirs(imagesDir)


#
# read jMeter log
# 
alldf = pd.read_csv(fullName, error_bad_lines=True, skipfooter=0, low_memory=False)
#convert timestamp to date format
if not datetime:
    alldf['timeStamp'] = pd.to_datetime(alldf['timeStamp'], unit='ms')
#set index in time column
alldf.index = alldf['timeStamp']
#alldf = alldf.set_index(alldf['timeStamp'])

#as part of error code respones is str, pandas gets crazy. to simplify will make it string.
alldf['responseCode'] = alldf['responseCode'].astype(str)


#filter rows by date rowsFrom, rowsTo. Final 3of3 step on row.
if ((rowsFrom != '' ) or (rowsTo != '' )):
    begin = pd.Timestamp(rowsFrom)
    end = pd.Timestamp(rowsTo)
    #alldf = alldf.loc[ (rowsFrom <= alldf['timeStamp']) & (alldf['timeStamp']<= rowsTo) ]
    #alldf = alldf.loc[ rowsFrom : rowsTo ]
    alldf = alldf[(alldf.index.get_level_values(0) >= begin) & (alldf.index.get_level_values(0)  <= end)]
    #alldf.truncate(before=begin, after=end)

#select only results with max threads
if allResults:  
    majordf = alldf
else:
    maxThreads = alldf['allThreads'].max()   
    majordf = alldf[alldf['allThreads'] == maxThreads]    

# row count
dataCnt = majordf.count()
    

#
# Open HTML file for writing
#
htmlStr = htmlStart % (testName)

if allResults:
    htmlStr = htmlStr + ( htmlHeader % (1, 'info1', 'jMeter execution log analysis for ' + testName + ' (all requests)', 1))
else:
    htmlStr = htmlStr + ( htmlHeader % (1, 'info1', 'jMeter execution log analysis for ' + testName + ' (max threads)', 1))
 
    
#
# Convert README to html    
#
htmlStr = htmlStr + ( htmlHeader % (2, 'info', 'Test information', 2))

plantUMLsnippet=''
headerPfx = '##'
READMEfile = os.path.dirname(os.path.abspath(fullName)) + '/README'
#try:
tempFile = open( READMEfile, 'r+' )
verbatim=False
for line in fileinput.input( READMEfile ):                        
    if headerPfx in line :
        if (renderPlantUML & (plantUMLsnippet != '')):
            try:
                umcRoot = os.environ['umcRoot']
                #
                import jinja2
                #
                templateLoader = jinja2.FileSystemLoader(searchpath= umcRoot + '/varia/jmeter/lib')
                templateEnv = jinja2.Environment(loader=templateLoader)
                TEMPLATE_FILE = "plantuml.jinja"
                template = templateEnv.get_template(TEMPLATE_FILE)
                #
                plantUMLText = template.render(FLOW=plantUMLsnippet, TESTID=testName)  
                #
                plantUMLfile = 'testLayout.puml'
                plantUMLout = open(reportDir + '/' + plantUMLfile,'w')
                plantUMLout.write(plantUMLText)
                plantUMLout.close()
                #
                plantUMLjar = umcRoot + '/varia/jmeter/lib/plantuml.jar'
                #
                if subprocess.call(['java', '-jar', plantUMLjar, '-oimages', reportDir + '/' + plantUMLfile]):
                    raise
                # add image
                htmlStr = htmlStr + (htmlImg % ('images/' + 'testLayout.png'))
            except:
                print "Error running plantUML. Falling back to text."
                htmlStr = htmlStr + plantUMLsnippet.replace('\n', htmlBreak) 
            #    
            plantUMLsnippet = ''
        #
        if verbatim:
            htmlStr = htmlStr + htmlParagraphStop
        section=line.replace(headerPfx, '').replace('\n','').replace('\r','').strip()
        htmlStr = htmlStr + ( htmlHeader % (3, 'none', section, 3))
        htmlStr = htmlStr + htmlParagraphStart
        verbatim=True
    else:
        if (renderPlantUML & (section == 'Communication layout')):
            plantUMLsnippet = plantUMLsnippet + line 
        else:
            if line.replace('\n','').replace('\r','') == '.':
                line = '(none)'
            htmlStr = htmlStr + line + htmlBreak

if verbatim:
    htmlStr = htmlStr + htmlParagraphStop

tempFile.close() 
#except:
#    htmlStr = htmlStr + '(None. README file not found)' + htmlBreak
#    print 'Warning: README file not found. '
#    pass


#
# execution time
#
htmlStr = htmlStr + ( htmlHeader % (2, 'info1', 'Latency distribution', 2))
desc = majordf['Latency'].describe()
    
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
htmlStr = htmlStr + ( htmlHeader % (2, 'info2', 'Latency quantiles', 2))

quantiles = majordf['Latency'].quantile([.1, .2, .25, .3, .4, .5, .6, .7, .75, .8, .9, .95, 1])
    
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

fig, ax = plt.subplots(1, figsize=(10 * imgZoom, 4 * imgZoom))
ax.title.set_text('Thread count')

column='allThreads'
ax.plot(majordf[column], linewidth=1)
ax.legend(loc='upper left', fontsize=8) 

pngFileName = 'jmeter_series_' + allResultsFileExt + '_' + column + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)

htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak

#
# Latency
#
htmlStr = htmlStr + ( htmlHeader % (2, 'response', 'Response time', 2))

fig, ax = plt.subplots(1, figsize=(10 * imgZoom, 4 * imgZoom))
fig.autofmt_xdate()
ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
#ax.set_ylim([0,quantiles[0.9]*2])
ax.title.set_text('Latency')

column='Latency'

ax.plot(majordf[column], linewidth=0.1)

ax.legend(loc='upper left', fontsize=8) 

pngFileName = 'jmeter_series_' + allResultsFileExt + '_' + column + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)

htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak

#
# Latency 95 percentile
#
htmlStr = htmlStr + ( htmlHeader % (2, 'response', 'Response time 95\'th percentile', 2))

fig, ax = plt.subplots(1, figsize=(10 * imgZoom, 4 * imgZoom))
fig.autofmt_xdate()
ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
#ax.set_ylim([0,quantiles[0.9]*2])
ax.title.set_text('Latency 95\'th percentile')

column='Latency'

percentile95 = majordf[column].quantile(0.95)
subsetdf = majordf.copy()
subsetdf.loc[subsetdf[column] > percentile95, column] = 0

#print subsetdf.loc[subsetdf[column] > percentile95, column]

ax.plot(subsetdf[column], linewidth=0.1)

ax.legend(loc='upper left', fontsize=8) 

pngFileName = 'jmeter_series_95q_' + allResultsFileExt + '_' + column + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)

htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak



#
# Latency per response code
#
htmlStr = htmlStr + ( htmlHeader % (2, 'response', 'Response time per response code', 2))

codes = majordf['responseCode'].unique()

#
column='Latency'
fig, ax = plt.subplots(1, figsize=(10 * imgZoom, 4 * imgZoom))
ax.title.set_text('Latency time per response code')
for code in majordf['responseCode'].unique():
    #add column with code values
    #
    #very slow!
    #alldf['lat:'+ code] = alldf.apply(lambda r: r['Latency'] if r['responseCode'] == code else np.NaN, axis=1)
    majordf['lat:'+ code] = majordf['Latency'] * ( majordf['responseCode'] == code )
    ax.plot(majordf['lat:' + code], linewidth=0.1)
    #ax.set_ylim([0,quantiles[0.9]*2])

ax.legend(loc='upper left', fontsize=8) 

pngFileName = 'jmeter_series_code1' + allResultsFileExt + '_' + column +  '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)
htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak



#
# mean, min, max
#
fig, ax = plt.subplots(1, figsize=(10 * imgZoom, 4 * imgZoom))
ax.title.set_text('Latency mean & std deviation')
#ax.set_ylim([0,quantiles[0.9]*2])

column='elapsed'
dataCnt = majordf[column].count()
majordf[column+'_mean'] = majordf[column].rolling(dataCnt/20).mean()
majordf[column+'_std'] = majordf[column].rolling(dataCnt/20).std()
majordf[column+'_hi'] = majordf[column].rolling(dataCnt/20).mean() + majordf[column].rolling(dataCnt/20).std()
majordf[column+'_lo'] = majordf[column].rolling(dataCnt/20).mean() - majordf[column].rolling(dataCnt/20).std()
#lo = majordf[column + '_lo']
#majordf[ lo < 0 ] = 0


ax.plot(majordf[column+'_mean'], label = 'mean', linewidth=1)
ax.plot(majordf[column+'_std'], label = 'std', linewidth=1)
ax.plot(majordf[column+'_hi'], label = 'hi', linewidth=1)
#ax.plot(majordf[column+'_lo'], label = 'lo', linewidth=1)
#ax.plot(x, majordf[column+'_max'])
ax.legend(loc='upper left', fontsize=8) 

pngFileName = 'jmeter_series_mean' + allResultsFileExt + '_' + column + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)

htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak


#
# responses
#
htmlStr = htmlStr + ( htmlHeader % (2, 'info2', 'HTTP response codes', 2))

counts = majordf['responseCode'].value_counts()

htmlStr = htmlStr + htmlTableStart
for code in majordf['responseCode'].unique():
    htmlStr = htmlStr + htmlTableRowStart
    htmlStr = htmlStr + (htmlTableData % (code))
    htmlStr = htmlStr + (htmlTableData % (counts[code]))
    htmlStr = htmlStr + htmlTableRowStop
htmlStr = htmlStr + htmlTableStop


#
# elapsed per code
#

codes = majordf['responseCode'].unique()

#
column='elapsed'
fig, ax = plt.subplots(1, figsize=(10 * imgZoom, 4 * imgZoom))
ax.title.set_text('Elapsed time per response code')
for code in majordf['responseCode'].unique():
    #add column with code values
    #
    # very slow!
    #alldf['el:'+ code] = alldf.apply(lambda row: row['elapsed'] if r['responseCode'] == code else np.NaN, axis=1)
    majordf['el:'+ code] = majordf['elapsed'] * ( majordf['responseCode'] == code )
    ax.plot(majordf['el:' + code], linewidth=0.1)
    #ax.set_ylim([0,quantiles[0.9]*2])

ax.legend(loc='upper left', fontsize=8) 
    
pngFileName = 'jmeter_series_code2' + allResultsFileExt + '_' + column + '_' + str(code) + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)
htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak


#
# elapsed for 200 code
#

codes = majordf['responseCode'].unique()

#
column='elapsed'
fig, ax = plt.subplots(1, figsize=(10 * imgZoom, 4 * imgZoom))
ax.title.set_text('Elapsed time per response code: 200')

code = '200'
majordf['el:'+ code] = majordf['elapsed'] * ( majordf['responseCode'] == code )
ax.plot(majordf['el:' + code], linewidth=0.1)
ax.legend(loc='upper left', fontsize=8) 
    
pngFileName = 'jmeter_series_codeOK' + allResultsFileExt + '_' + column + '_' + str(code) + '.png'
fullFileName = imagesDir + '/' + pngFileName
fig.savefig(fullFileName)
htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
htmlStr = htmlStr + htmlBreak


#
# stack by code
#

#column='elapsed'
#fig, ax = plt.subplots(1, figsize=(10,4))
#ax.stackplot(x, y)
#ax.title.set_text('Stack by count of response code')
#for code in majordf['responseCode'].unique():
#    #add column with code values
#    #
#    # very slow!
#    #alldf['el:'+ code] = alldf.apply(lambda row: row['elapsed'] if r['responseCode'] == code else np.NaN, axis=1)
#    majordf['st:'+ code] = majordf['elapsed'] * ( majordf['responseCode'] == code )
#    ax.plot(majordf['st:' + code])
#
#ax.legend(loc='upper left', fontsize=8) 
#    
#pngFileName = 'jmeter_series_code2' + allResultsFileExt + '_' + column + '_' + str(code) + '.png'
#fullFileName = imagesDir + '/' + pngFileName
#fig.savefig(fullFileName)
#htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
#htmlStr = htmlStr + htmlBreak


#
# stop html
#
htmlStr = htmlStr + (htmlStop)

#
# Write html file
#
htmlfile = 'jmeter_' + testName + '_' + allResultsFileExt + '.html'
htmlout = open(reportDir + '/' + htmlfile,'w')
htmlout.write(htmlStr)
htmlout.close()


