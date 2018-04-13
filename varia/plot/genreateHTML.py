#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from graphDrawer_v5 import createClusters
from graphDrawer_v5 import createDataFrames
from graphDrawer_v5 import plotClusters

import sys
import argparse
from dateutil import parser as dateparser

def html(file_names):
    """ Generate HTML file.    
    
    :param file_names: list of images with graphs
    
    :return: N/A         
    """
    
    html_string_start = '''
    <html>
        <head>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">
            <style>body{ margin:0 100; background:whitesmoke; }</style>
        </head>
        <body>'''
        
    html_string_end = '''    
        </body>
    </html>'''
    
    html = html_string_start
    for  file in file_names:
        html+=  '''
            <h2>'''+file+'''</h2>
        <iframe width="1000" height="550" frameborder="0" seamless="seamless" scrolling="no" \
            src="''' + file + '''?width=800&height=550"></iframe>'''
    
    html+= html_string_end
    
    f = open('report.html','w')
    f.write(html)
    f.close()
    

def saveImages():
    """ Save images of graphs in default directory.    
    
    :return: List of images         
    """
    import matplotlib._pylab_helpers
    
    figures=[manager.canvas.figure
         for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers()]
    
    file_names = []
    for i, figure in enumerate(figures):
        #print(figure.get_axes()[0].title)
        file_name = 'report_files/figure%d.png' % i
        figure.savefig(file_name)
        file_names.append(file_name)
    
    return file_names


    
def main(argv):

    parser = argparse.ArgumentParser()    
    parser.add_argument("-fd","--fromDate", help="used for filtering data files based on measurements date",
                        default = '2010-02-14 10:45:10')
    parser.add_argument("-td","--toDate", help="used for filtering data files based on measurements date",
                        default = '2110-02-14 10:48:19')
    parser.add_argument("yamlDirectory", help="directory with yaml configuration files")
    parser.add_argument("dataDirectory", help="directory with CSV files with data")
    
    args = parser.parse_args()

    configDir = args.yamlDirectory
    dataDir = args.dataDirectory
    fromDate = dateparser.parse(args.fromDate)
    toDate = dateparser.parse(args.toDate)
    
    #configDir = "/home/msed/LOGS/TEST1/config" 
    #dataDir = "/home/msed/LOGS/TEST1/data"
     
    fixfiles(dataDir, 'uptime.log')       
    fixfiles(dataDir, 'ifconfig.log')
    #df = mergeDataFrames(dataDir)
    clusters = createClusters(configDir)        
    #groupBy = createGroupByArray(configDir)
    groupBy = [];
    dataFrames = createDataFrames(dataDir, fromDate, toDate, groupBy)    
    
    withoutSplit = [x for x in dataFrames if x['split'].iloc[0] == False]
    plotClusters(clusters, withoutSplit)     

    #withSplit = [x for x in dataFrames if x['split'].iloc[0] == True]
    #plotClustersWithSplit(clusters, withSplit)     
    
    file_names = saveImages()
    html(file_names)
    
    #dd = splitIfNeeded(dataFrames[0], groupBy)
    
if __name__ == "__main__":
    main(sys.argv)