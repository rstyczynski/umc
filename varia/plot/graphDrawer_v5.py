# -*- coding: utf-8 -*-
"""
TODO:
    1. select of data based on tags (for example: given host)
    2. Some statistics......

"""

def createClusters(path):
    """ Method that creates clusters based on Yaml entry files.

    :param path: path to Yaml files
    :return: dictionary of clusters, eg: {'Scheduler': {'ContextSwitches': 'interrupt'}} 
    
    """
    import yaml
    import os

    files = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.yaml')]
    clusters = {}    
    
    for file in files:
        stream = open(file, 'r')    
        configuration = yaml.load(stream)
            
        rootKey = list(configuration.keys())[0]
        for clusterItem in configuration[rootKey]["metrics"].keys():
            for subclusterItem in configuration[rootKey]["metrics"][clusterItem]:
                value = configuration[rootKey]["metrics"][clusterItem][subclusterItem]           
                
                if(value is not None):                
                    clusterName = clusterItem + "_" + value 
                else:
                    clusterName = clusterItem    
                
                values = clusters.get(clusterName, [])
                values.append(subclusterItem)
                clusters[clusterName] = values
        
    return clusters


def createGroupByArray(path):
    """ Method that list of "group by" columns. Used to split data frames later on.

    :param path: path to Yaml files
    :return: list of columns
    
    WARNING: Currently one file supported only!
    """
    import yaml
    import os

    files = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.yaml')]
    groupBy = []    
    
    for file in files:
        stream = open(file, 'r')    
        configuration = yaml.load(stream)
            
        rootKey = list(configuration.keys())[0]
        
        if(configuration[rootKey]["groupBy"] is not None):
            groupBy = configuration[rootKey]["groupBy"].keys()
                
    return list(groupBy)


def createDataFrames(path, fromDate, toDate, groupBy):
    """ Method that load files with time series into DataFrames. Only CSV files are read.

    :param path: directory of CSV files
    :param fromDate: used to filer data files based on timestamp
    :param toDate: used to filer data files based on timestamp
    :param groupBy: list of columns used to split dataframe into smaller data frames
    :return: list of data frames

    """
    import pandas as pd
    import os
    from datetime import datetime
    
    df = mergeDataFrames(path)
    
    
    updatedDF = []
    for oneDF in df:
        if(len(oneDF) == 0):
            continue
                
        try:
            
            oneDF['cDatetime'] = oneDF.timestamp.map(datetime.fromtimestamp)
            oneDF = oneDF[(oneDF.cDatetime >= fromDate) & (oneDF.cDatetime <= toDate)]        
            oneDF['chartName'] = "["+ oneDF['source'][:1].iloc[0] +"/"+ oneDF['system'][:1].iloc[0] + "]"                         
            oneDF['split'] = False
            oneDF = oneDF.sort_values(['cDatetime'])
        
        except:
            print(oneDF.columns)
            print(oneDF.tail)
            print(len(oneDF.timestamp.notnull()))
            raise
            
        oneDF = splitIfNeeded(oneDF, groupBy)        
        updatedDF.extend(oneDF)        
    
    
    return updatedDF

def splitIfNeeded(dataFrame, groupBy):
    """ Method splits dataFrame into more smaller one based on "groupBy" columns.

    :param dataFrame: data frame to split
    :param groupBy: list of columns used to split dataframe into smaller data frames
    :return: list of data frames

    """    
    dataFrames = []
    
    if(len(groupBy)==0):
        return [dataFrame]
    
    if set(groupBy).issubset(dataFrame.columns):
        for x,y in dataFrame.groupby(groupBy):
            y['chartName'] = '['+'/'.join(x) + ']'
            y['split'] = True
            dataFrames.append(y)            
        
    else:
        dataFrames = [dataFrame]
        
    return dataFrames


def plotClusters(clusters, timeSeries):
    """ Method that plots charts for a dictionary of clusters. Each cluster is drawn 
    as separate chart.

    :param clusters: dicitionary of clusters, eg: {'Scheduler': {'ContextSwitches': 'interrupt'}}, 
    where 'Scheduler' is one specific cluster
    :param timeSeries: list of DataFrames with data to draw. Each dataframe originages from one file, 

    :return: N/A
    """
    import matplotlib.pyplot as plt
    import os
    
    chart_number = plt.gcf().number + 1
    plots = []
    for cluster in clusters.keys():
        figure = plt.figure(chart_number, figsize = (30,20))
        #figure = plt.figure(chart_number)
        plt.title(cluster)
        plt.xticks(rotation='vertical')
        
        plotCluster(clusters[cluster], timeSeries)  
               
        chart_number+=1
    

def plotCluster(cluster, timeSeries):
    """ Method that plots chart for one cluster.

    :param cluster: list of metrics withing cluster to draw
    :param timeSeries: list of DataFrames with data to draw. Each dataframe originates from one file, 

    :return: N/A
    
    """
    import matplotlib.pyplot as plt    
    
    legend = []
    for specificSeries in timeSeries:    
        for item in cluster:
            if item in specificSeries.columns:
                host = specificSeries.chartName.iloc[0]                          
                
                plt.plot(specificSeries.cDatetime, specificSeries[item], marker = '.')        
                legend.append(host + item)
        
    plt.legend(legend)#, loc='upper left', bbox_to_anchor=(0,-0.3))                    



def plotClustersWithSplit(clusters, timeSeries):
    """ Method that plots charts for a dictionary of clusters. Each cluster is drawn 
    as separate chart. Additionally each DateFrame is draws separately.

    :param clusters: dicitionary of clusters, eg: {'Scheduler': {'ContextSwitches': 'interrupt'}}, 
    where 'Scheduler' is one specific cluster
    :param timeSeries: list of DataFrames with data to draw. Each dataframe originages from one file, 

    :return: N/A
    """
    import matplotlib.pyplot as plt
    import os
    
    chart_number = plt.gcf().number + 1
    plots = []
    for cluster in clusters.keys():
        for ts in timeSeries:
            figure = plt.figure(chart_number)
            plt.title(cluster + " - " + ts.chartName.iloc[0])
            plt.xticks(rotation='vertical')
            
            plotCluster(clusters[cluster], [ts])  
                   
            chart_number+=1


def fixfiles(path, file_name):
    
    import pandas as pd
    import os

    for dp,dn,fn in os.walk(path):
        for f in fn:
            if (f.endswith(file_name) and os.path.getsize(os.path.join(dp, f))>0):
                with open(os.path.join(dp, f), 'r+') as file:
                    line = file.readline()
                    if(",TMP" in line):
                        continue
                    
                    line= line.rstrip('\r\n') + ",TMP"                                    
                    content = file.read()                
                    file.seek(0, 0)
                    file.write(line.rstrip('\r\n') + '\n' + content)                   


def mergeDataFrames(path):
    
    import pandas as pd
    import os

    dataFrames = {}
    for dp,dn,fn in os.walk(path):
        for f in fn:
            if (f.endswith('.log') and not f.endswith('wls.log') \
                and not f.endswith('top.log') and os.path.getsize(os.path.join(dp, f))>0):
                
                try:
                                                            
                    df = pd.read_csv(os.path.join(dp, f), index_col=False)                
                    df = df[df.timestamp.notnull()]
                    if(len(df) == 0):
                        continue

                    key = df['source'].iloc[0] + df['system'].iloc[0]
                    if(key in dataFrames.keys()):
                        newDF = dataFrames[key].append(df)
                        dataFrames[key] = newDF
                    else:
                        dataFrames[key] = df
                                        
                except:
                    print(df)
                    raise
                
                
    return list(dataFrames.values())
