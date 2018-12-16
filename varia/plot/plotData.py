#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 16:11:25 2018

@author: rstyczynski
"""

from matplotlib.ticker import FuncFormatter
from pandas import Series
from matplotlib import dates

import matplotlib.pyplot as plt
import pandas
import numpy
import datetime as dt
import os
import fnmatch
import matplotlib.dates as mdates
import yaml
import getopt
import sys

output = sys.stdout

#
# 
#
computerName='ppseelm-lx41082'
probeName = 'iostat'
identifierColumns = 'Device'

computerName='ppseelm-lx41082'
probeName = 'ifconfig'
identifierColumns = 'device'

computerName='ppseelm-lx41082'
probeName = 'wls_jmsserver'
identifierColumns = 'jmsServerName'

computerName='ppseelm-lx41082'
probeName = 'soabindings'
identifierColumns = 'ServerName,soainfra_composite,soainfra_composite_assembly_member,soainfra_composite_assembly_member_type,soainfra_composite_revision,soainfra_domain'

computerName='ppseelm-lx41082'
probeName = 'wls_channel'
identifierColumns = 'domain,serverName,subsystem,channelName'

computerName='ppseelm-lx41082'
probeName = 'wls_jmsruntime'
identifierColumns = 'domain,serverName,subsystem,runtimeName'

computerName='ppseelm-lx41082'
probeName = 'wls_datasource'
identifierColumns = 'domain,serverName,subsystem,dsName'

computerName='ppseelm-lx41089'
probeName = 'businessservice_SERVICE'
identifierColumns = 'path,name'

computerName='ppseelm-lx41089'
probeName = 'businessservice_OPERATION'
identifierColumns = 'path,name'

computerName='ppseelm-lx41089'
probeName = 'businessservice_URI'
identifierColumns = 'path,name'

###
computerName='ppseelm-lx41082'
probeName = 'iostat'
identifierColumns = 'Device'

probeDir='/Users/rstyczynski/Documents/IKEA/11.Test/TESTS/10.04.2018/umc_archive/rodmon_data/info/'
srcDir = '/Users/rstyczynski/Documents/IKEA/11.Test/TESTS/10.04.2018/umc_archive/rodmon_data/data'
dstDir = '/tmp'

#
# HTML tags
#
htmlStart = """<html>
    <head>
    <title>%s</title>
    </head>
    <body>"""

htmlStop = """</body></html>"""

htmlImg = """<img src="%s" width=500 height=400>"""

htmlVerbatim = """<verbatim>%s</verbatim>"""

htmlParagraphStart = """<p>"""
htmlParagraphStop = """</p>"""

htmlHeader = """<h%d id="%s">%s</h%d>"""

htmlToC = """ %s """
htmlLocalHref = """<a href="#%s">%s</a>"""
htmlBreak = """<br/>"""

#
# DEFAULT PARAMETERS
#
computerName=''
probeName = ''
identifierColumns = ''

rowsFrom = dt.MINYEAR
rowsTo = dt.MAXYEAR

srcDir = '.'
probeDir='.'
dstDir = '.'

plotOnlyChanges = False

#
# USAGE
#
def usage():
    
    output.write("""
Plots UMC data collected in CSV file.""")

    output.write("""
usage: umcPlot.sh """)
    
    output.write("""'--server= --probe= [--pkColumns=] [srcDir=] [dstDir=] [--probeDir=]""")
    output.write("""
    
    Mandatory:
    --server...........plot data for given server. Filters log filenames.
    --probe............plot data for given probe. Filters log filenames.

    Optional:
    --pkColumns........specify columns to be used to identify unique data streams. default: none
    --from.............select rows starting at from. Format: yyyy-mm-dd hh:mm:ss. default: 1
    --to...............select rows ending at to. Format: yyyy-mm-dd hh:mm:ss. default: 9999
    --srcDir...........directory to get log files from. default: .
    --dstDir...........directory to write png files. default: .
    --plotOnlyChanges..plots only dataseries with changes. default: false
    
    Special:
    --probeDir.......points to directory with probe.info file. Required to determine columns names to be plotted. default: srcDir
    """)
    
    output.write("""
    ---
    version 0.1
    rstyczynski@gmail.com, https://github.com/rstyczynski/umc""")
   
#
# HELPER FUNCTIONS
#
def changesPerSecond(dataset, column):
    if not 'timestamp_dt' in dataset:
        dataset['timestamp_dt'] = dataset['timestamp'].diff()

    columnDelta=column + '_dv'
    dataset[columnDelta] = dataset[column].diff()
    
    columnDelta=column + '_dvdt'
    dataset[columnDelta] = dataset[column + '_dv'] /   dataset['timestamp_dt']

#retuens size of data row
def getDataSize(csvFile):
    colCount=0;
    with open(csvFile) as csv_file:
        for i, line in enumerate(csv_file):
            if i == 0:
                headerCount = line.count(",") + 1
                colCount = headerCount
            elif i == 1:
                dataCount = line.count(",") + 1
            elif i > 1:
                break
    if (headerCount < dataCount):
        print("Warning: Header and data size mismatch. Columns beyond header size will be removed.")
        colCount=headerCount

    return(colCount)


# PARAMETER PARSING
#
try:
    opts, args = getopt.getopt( sys.argv[1:], 's:p', ['server=','probe=', 'pkColumns=', 'srcDir=', 'dstDir=', 'probeDir=', 'from=', 'to=', 'plotOnlyChanges'])
except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)
	
for opt, arg in opts:
    if opt in ('--help'):
        usage()
        sys.exit(2)
    elif opt in ('-s', '--server'):
        computerName = arg
    elif opt in ('-p', '--probe'):
        probeName = arg
    elif opt in ('--from'):
        rowsFrom = dt.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S')
    elif opt in ('--to'):
        rowsTo = dt.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S')
    elif opt in ('--pkColumns'):
        identifierColumns = arg
    elif opt in ('--probeDir'):
        probeDir = arg
    elif opt in ('--srcDir'):
        srcDir = arg
        probeDir = arg
    elif opt in ('--dstDir'):
        dstDir = arg
    elif opt in ('--plotOnlyChanges'):
        plotOnlyChanges = True
    else:
        usage()
        sys.exit(2) 

if computerName == '':
    print 'Error: Missing mandatory argument.'
    usage()
    sys.exit(2)
    
if probeName == '':
    print 'Error: Missing mandatory argument.'
    usage()
    sys.exit(2)


#
# CODE
#

#
#browse files, and add data to dataframe
#
firstFile = True
firstFileColumns = ''
for dirRoot,dirList,fileList in os.walk(srcDir):
    print 'Scan path:', dirRoot
    dirName = os.path.basename(dirRoot)
    print 'Scan directory:', dirName
    
    #filter rows by date rowsFrom, rowsTo. Step 1of3 on directory level.
    try:
        #print rowsFrom.date(), dt.datetime.strptime(dirName,'%Y-%m-%d').date(), rowsTo.date()
        if not(rowsFrom.date() <= dt.datetime.strptime(dirName,'%Y-%m-%d').date() <= rowsTo.date()) :
            print 'Ignoring data set out of required date range.'
            continue
    except:
        pass
        print sys.exc_info()[0]
        print 'Ignoring directory w/o date.'
        print rowsFrom.date()
        print rowsTo.date()
        print dirName
        continue
    
    #print 'Dir list:', dirList
    print 'File list:', fileList
    if fileList:
        for file in fileList:
            #fileMatch = '*' + computerName + '_' + probeName + '.log'
            fileMatch = '*' + '_' + probeName + '*.log'
            print fileMatch
            if fnmatch.fnmatch(file, fileMatch):
                fullName = os.path.join(dirRoot,file)
                print fullName, os.path.getsize(fullName)
                
                fileDate = file.split('_')[0]
                print fileDate, rowsFrom, rowsTo
                
                #filter rows by date rowsFrom, rowsTo. Step 2of3 on file level.
                try:
                    #print rowsFrom, dt.datetime.strptime(fileDate,'%Y-%m-%d-%H%M%S'), rowsTo
                    if not(rowsFrom <= dt.datetime.strptime(fileDate,'%Y-%m-%d-%H%M%S') <= rowsTo):
                        print 'Ignoring file out of required date range.'
                        continue
                except:
                    pass
                    print 'Ignoring file w/o date.'
                    continue
                
                if os.path.getsize(fullName) > 0:
                    if firstFile:
                        df = pandas.read_csv(fullName, error_bad_lines=True, skipfooter=0, usecols=range(getDataSize(fullName)))
                        print ">>>READ CSV:" + fullName
                        #print df
                        
                        firstFileColumns = str(df.columns)
                        #try:
                        #df['date_time']  = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in df['datetime']]
                        for dataLine in df['datetime']:
                            try:
                                df['date_time']  = dt.datetime.strptime(dataLine,'%Y-%m-%d %H:%M:%S')
                            except:
                                print 'Warning: malformed data line:'
                                print dataLine
                                pass
                        #except:
                        #    pass
                        firstFile = False
                        #print df.head
                    else:
                        #skipfooter is to remove lat line as potnetially bad
                        df2 = pandas.read_csv(fullName, error_bad_lines=True, skipfooter=0, usecols=range(getDataSize(fullName)))
                        if str(df2.columns) != firstFileColumns:
                            errorMsg = 'different columns! Ignoring file:' + fullName
                            #raise Exception(errorMsg)
                            print 'Warrning: ' + errorMsg
                            print "First file:" + firstFileColumns
                            print "This file :" + str(df2.columns)
                        else:
                            #print df2.head
                            #try:
                            #df2['date_time']  = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in df2['datetime']]
                            #
                            for dataLine in df2['datetime']:
                                try:
                                    df2['date_time']  = dt.datetime.strptime(dataLine,'%Y-%m-%d %H:%M:%S')
                                except:
                                    print 'Warning: malformed data line:'
                                    print dataLine
                                    pass
                            #except:
                            #    pass
                            df = df.append(df2)
                            
if firstFile:
    print "Nothing to do. Exiting."
    exit(0)
   
#
# Open HTML file for writing
#
htmlStr = htmlStart % (computerName + '_' + probeName)

#remove leading spaces from column names
cols = df.columns
cols = cols.map(lambda x: x.strip())
df.columns = cols

#filter rows by date rowsFrom, rowsTo. Final 3of3 step on row.
df = df.loc[ (str(rowsFrom) <= df['date_time']) & (df['date_time']<= str(rowsTo)) ]

#
# Prepare stream identification column
#
#print identifierColumns.split(',')
if identifierColumns != '':
    #print identifierColumns.split(',')
    for idCol in identifierColumns.split(','):
        #print idCol
        #print df[idCol]
        if 'identifier' in df.columns:
            df['identifier'] = df['identifier'] + '.' + df[idCol]
        else:
            df['identifier'] = df[idCol]
    #remove forbideen "file related" characters from identifier        
    #df['identifier'] = df['identifier'].str.replace('/','.')

#print df['identifier']    

# set index
#df.set_index('identifier')
#print df['identifier'].unique()

#convert datetime from string
#df['datetime'] = pandas.to_datetime(df['datetime'])
#df = df.sort_values(by='datetime')

df = df.sort_values(by='timestamp')
#df.to_csv('out.csv')

#
#probe=df.iloc[0]['source']
#system=df.iloc[0]['system']
system=computerName
probe=probeName

#https://pandas.pydata.org/pandas-docs/stable/10min.html
#print df.head
#print df.index
#print df.columns


# formatter 
def millions(x, pos):
    'The two args are the value and tick position'
    return '%1.1fM' % (x*1e-6)
formatter = FuncFormatter(millions)

# x axis
days = dates.DayLocator()
hours = dates.HourLocator()
dfmt = dates.DateFormatter('%b %d')


#
plt.close('all')


#
# Single chart
#
getData= probeName + '.metrics'
probeDef= os.path.join(probeDir, 'info', probeName + '.info')
print ">>>Probe definition:" + probeDef

htmlStr = htmlStr + ( htmlHeader % (1, probeName + "_" + computerName, probeName + "@" + computerName, 1))
htmlStr = htmlStr + htmlToC #placeholder

with open(probeDef, 'r') as yamlDoc:
    doc = yaml.load(yamlDoc)
    
finalDoc=doc
for cfgElement in getData.split('.'):
    finalDoc = finalDoc[cfgElement]

    
ToC = ''
for subsystem in finalDoc:
    print 
    print '---'
    print subsystem
    
    htmlStr = htmlStr + ( htmlHeader % (2, subsystem, subsystem, 2))
    
    if ToC == '':
        ToC = htmlHeader % (2, 'Contents', 'Contents', 2)
        ToC = ToC + htmlLocalHref % (subsystem, subsystem) + ' | '
    else:
        if 'identifier' in df.columns:
            ToC = ToC + htmlBreak + htmlLocalHref % (subsystem, subsystem) + ' | '
        else:
            ToC = ToC + htmlLocalHref % (subsystem, subsystem) + ' | '
    
    #discover metric groups
    getData= probeName + '.metrics.' + subsystem
    columns=doc
    for cfgElement in getData.split('.'):
        columns = columns[cfgElement]
    print columns
    if 'identifier' in df.columns:
        print  df['identifier'].unique()
        #get uniqie identifiers. https://chrisalbon.com/python/data_wrangling/pandas_list_unique_values_in_column/
        for seriesPK in df['identifier'].unique():
            if isinstance(seriesPK, basestring):
                #select rows for given identifier
                #print seriesPK
                htmlStr = htmlStr + ( htmlHeader % (3, subsystem + '_' + seriesPK, seriesPK, 3))
                ToC = ToC + htmlLocalHref % (subsystem + '_' + seriesPK, seriesPK) + ' | '
                    
                plotdf = df.loc[df['identifier'] == seriesPK]
                #print plotdf.columns
                
                #df.to_csv('/tmp/1a.csv')
                #plotdf.to_csv('/tmp/1b.csv')
                #print plotdf.head
                
                x = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in plotdf.datetime]
                #x = plotdf['date_time']
# use it to debug data frame             
#                x = ''
#                timeStr = ''
#                try: 
#                    del x[:]
#                except:
#                    pass
#                for index, row in plotdf.iterrows():
#                    try:
#                        timeStr = row.datetime
#                        timeMark = dt.datetime.strptime(timeStr,'%Y-%m-%d %H:%M:%S')
#                        x.append(timeMark)
#                    except:
#                        print row
#                        print row.datetime
#                        print 'Error:' + row.datetime

                        
                #x = plotdf['timestamp']
                
                #print plotdf.head
                #do plot
                fig, ax = plt.subplots(1)
                fig.autofmt_xdate()
                ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
                title = seriesPK + "@" + computerName + ':' + probe + ':' + subsystem
                ax.set_title(title)

                #direvartive
                figD, axD = plt.subplots(1)
                figD.autofmt_xdate()
                axD.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
                print probe, subsystem, seriesPK
                title = seriesPK + "@" + computerName + ':' + probe + ':' + subsystem + ' [/s]'
                axD.set_title(title)
                
                #            
                emptyPlot=True
                for column in columns:
                    print column 
                    #print plotdf[column]
                    
                    dataChanges= False
                    try:
                        if df[column].std() > 0:
                            dataChanges= True
                    except:
                        pass    
                    
                    if dataChanges: #is data changing obver time?
                        emptyPlot=False
                        try:
                            ax.plot(x, plotdf[column], label=column)
                            ax.legend()
                            #add test name
                            #ax.text(right, top, 'right bottom' ,horizontalalignment='right', verticalalignment='bottom', transform=ax.transAxes)

                            changesPerSecond(plotdf, column)
                            axD.plot(x, plotdf[column + '_dvdt'], label=column + '/s')
                            axD.legend()
                        except:
                            print plotdf[column]
                            plotdf.to_csv('/tmp/1c.csv')
                            pass
                if (not emptyPlot) or (not plotOnlyChanges):
                    #
                    ax.legend()   
                    #
                    print system, probe, subsystem, seriesPK
                    pngFileName = '' + system + '_' + probe + '_' + subsystem + '_' + seriesPK + '.png'
                    pngFileName = pngFileName.replace('/','')
                    fig.set_tight_layout(True)
                    try:
                        fig.savefig(dstDir + '/images/' + pngFileName)   # save the figure to file
                    except:
                        #TODO
                        pass

                    plt.close(fig)
                    #
                    htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
                    # direvative
                    axD.legend()   
                    #
                    pngFileName = '' + system + '_' + probe + '_' + subsystem + '_' + seriesPK + '_changes.png'
                    pngFileName = pngFileName.replace('/','')
                    figD.set_tight_layout(True)
                    try:
                        figD.savefig(dstDir + '/images/' + pngFileName)   # save the figure to file
                    except:
                        #TODO
                        pass
                    plt.close(figD)
                    #
                    htmlStr = htmlStr + (htmlImg % ('images/' + pngFileName))
                    
                    
    else:
        #TODO - add protectino against truncated line
        #x = [dt.datetime.strptime(dt.datetime.strftime(d,'%Y-%m-%d %H:%M:%S') ,'%Y-%m-%d %H:%M:%S') for d in df['date_time']]
        try:
            x = [dt.datetime.strptime(d, '%Y-%m-%d %H:%M:%S') for d in df['datetime']]
        except:
            x = []
            timeStr = ''
            lastTime=''
            for index, row in df.iterrows():
                try:
                    timeStr = row.datetime
                    timeMark = dt.datetime.strptime(str(timeStr),'%Y-%m-%d %H:%M:%S')
                    x.append(timeMark)
                    lastTime=timeMark
                except:
                    print row
                    print row.datetime
                    x.append(lastTime)
                    pass
        #for dataLine in df['datetime']:
        #    try:
        #       x = dt.datetime.strptime(dataLine,'%Y-%m-%d %H:%M:%S')
        #    except:
        #        print 'Warning: malformed data line:'
        #        print dataLine
        #        pass
        #x = df['date_time']
        #print df
        #do plot
        fig, ax = plt.subplots(1)
        fig.autofmt_xdate()
        ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
        title = computerName + ':' + probe + ':' + subsystem
        ax.set_title(title)


        #direvartive
        figD, axD = plt.subplots(1)
        figD.autofmt_xdate()
        axD.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
                
        title = computerName + ':' + probe + ':' + subsystem + ' [/s]'
        axD.set_title(title)

        #  
        emptyPlot=True                     
        for column in columns:
            print column,
            
            dataChanges= False
            try:
                if df[column].std() > 0:
                    dataChanges= True
            except:
                pass
            
            if dataChanges: #is data changing obver time?
                emptyPlot=False
                ax.plot(x, df[column], label=column)
                ax.legend()
                # direvative
                changesPerSecond(df, column)
                axD.plot(x, df[column + '_dvdt'], label=column + '/s')
                axD.legend()
        #
        if (not emptyPlot) or (not plotOnlyChanges):
            #
            ax.legend()   
            pngFileName = '' + system + '_' + probe + '_' + subsystem + '.png'
            pngFileName = pngFileName.replace('/','')
            fig.set_tight_layout(True)
            fig.savefig(dstDir +  '/images/' + pngFileName)   # save the figure to file
            plt.close(fig)   
            htmlStr = htmlStr + (htmlImg % ( 'images/' + pngFileName))
            # direvative
            axD.legend()   
            pngFileName = '' + system + '_' + probe + '_' + subsystem + '_changes.png'
            pngFileName = pngFileName.replace('/','')
            figD.set_tight_layout(True)
            figD.savefig(dstDir +  '/images/' + pngFileName)   # save the figure to file
            plt.close(figD)   
            htmlStr = htmlStr + (htmlImg % ( 'images/' + pngFileName))

#
# stop html
#
htmlStr = htmlStr + (htmlStop)
htmlStr = htmlStr % (ToC)
#
# Write html file
#
htmlfile = computerName + '_' + probeName + '.html'
htmlout = open(dstDir + '/' + htmlfile,'w')
htmlout.write(htmlStr)
htmlout.close()
