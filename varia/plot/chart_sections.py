#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed May 30 16:02:36 2018

@author: rstyczynski
"""

alldf = pd.read_csv('/Users/rstyczynski/Documents/IKEA/11.Test/TESTS/TEST2905#2-jmeter/TEST2905#16.log')
alldf['timeStamp'] = pd.to_datetime(alldf['timeStamp'], unit='ms')
alldf.index = alldf['timeStamp']
                    
alldf['responseCode'] = alldf['responseCode'].astype(str)

for code in alldf['responseCode'].unique():
    alldf['code'+ code] = alldf.apply(lambda r: r['elapsed'] if r['responseCode'] == code else 0, axis=1)

print(alldf.columns)

