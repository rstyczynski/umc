#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May 29 21:15:24 2018

@author: rstyczynski
"""

import pandas as pd
import matplotlib.pyplot as plt

#
# HELPER FUNCTIONS
#
def changesPerSecond(dataset, column):
    if not 'timestamp_dt' in dataset:
        dataset['timestamp_dt'] = dataset['timestamp'].diff()

    columnDelta=column + '_dv'
    dataset[columnDelta] = dataset[column].diff()
    
    columnDelta=column + '_dvdt'
    dataset[columnDelta] = dataset[column + '_dv'] / dataset['timestamp_dt']

#
# 
#
df = pd.read_csv('/Users/rstyczynski/Documents/IKEA/11.Test/TESTS/TEST2505#5/ppseelm-lx41085/tmp/umc/TEST2505#5/2018-05-25/2018-05-25-140250_vmstat.log')
df['datetime'] = pd.to_datetime(df['datetime'])
df.index = df['datetime']

df2_ = pd.read_csv('/Users/rstyczynski/Documents/IKEA/11.Test/TESTS/TEST2505#5/ppseelm-lx41085/tmp/umc/TEST2505#5/2018-05-25/2018-05-25-140250_ifconfig.log')                
df2 = df2_.loc[df2_['device'] == 'eth0']
df2['datetime'] = pd.to_datetime(df2['datetime'])
df2.index = df2['datetime']
                
fig1, axes1 = plt.subplots(3,1, sharex=True)
for ax in axes1:
    ax.xaxis.grid(True, which='minor', linestyle='-', linewidth=0.25)

        
column1 = ' Interrupts'
cnt=df[column1].count()

df[column1 + '_mean'] = df[column1].rolling(cnt/10).mean()
df[column1 + '_mean'].plot(ax=axes1[0], style='g-', grid=True)

column2 = 'ContextSwitches'
cnt=df[column2].count()
df[column2 + '_mean'] = df[column2].rolling(cnt/10).mean()

df[column2 + '_mean'].plot(ax=axes1[1], style='b-', grid=True)

df[column1 + '_corr_' + column2] = df[column1].rolling(window=cnt/10).corr(other=df[column2]).rolling(cnt/10).mean()
df[column1 + '_corr_' + column2].plot(ax=axes1[2], style='r-', grid=True)

#
# 
#
column3=' RXbytes'
changesPerSecond(df2, column3)
cnt=df2[column3].count()

fig2, axes2 = plt.subplots(3, 1, sharex=True)
for ax in axes2:
    ax.xaxis.grid(True, which='minor', linestyle='-', linewidth=0.25)

corr = pd.DataFrame()
corr[column1] = df[column1].resample('5S').mean().ffill().rolling(cnt/10).mean()
corr[column3] = df2[column3 + '_dvdt'].resample('5S').mean().ffill().rolling(cnt/10).mean()
corr[column1 + '_corr_' + column3] = corr[column1].rolling(window=cnt/10).corr(other=corr[column3]).rolling(cnt/10).mean()

corr[column1].plot(ax=axes2[0], style='g-', grid=True)
corr[column3].plot(ax=axes2[1], style='b-', grid=True)
corr[column1 + '_corr_' + column3].plot(ax=axes2[2], style='r-', grid=True)


