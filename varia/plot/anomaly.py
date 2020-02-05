"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import pylab

import pandas as pd

import time

def thresholding_algo(y, lag, threshold, influence):
    signals = np.zeros(len(y))
    filteredY = np.array(y)
    meanFilter = [0]*len(y)
    stdFilter = [0]*len(y)
    meanFilter[lag - 1] = np.mean(y[0:lag])
    stdFilter[lag - 1] = np.std(y[0:lag])
    for i in range(lag, len(y)):
        if abs(y[i] - meanFilter[i-1]) > threshold * stdFilter [i-1]:
            
            if y[i] > meanFilter[i-1]:
                signals[i] = 1
            else:
                signals[i] = -1
            
            filteredY[i] = influence * y[i] + (1 - influence) * filteredY[i-1]
        else:
            signals[i] = 0
            filteredY[i] = y[i]
        
        meanFilter[i] = np.mean(filteredY[(i-lag):i])
        stdFilter[i] = np.std(filteredY[(i-lag):i])

    return dict(signals = np.asarray(signals),
                meanFilter = np.asarray(meanFilter),
                stdFilter = np.asarray(stdFilter),
                filteredY = np.asarray(filteredY)
                )
    

# Data
y = np.array([1,1,1.1,1,0.9,1,1,1.1,-3,-5,1,1.1,1,1,0.9,1,1,1.1,1,1,1,1,1.1,0.9,1,1.1,1,1,0.9,
       1,1.1,1,1,1.1,1,0.8,0.9,1,1.2,0.9,1,1,1.1,1.2,1,1.5,1,3,2,5,3,2,1,1,1,0.9,1,1,3,
       2.6,4,3,3.2,2,1,1,0.8,4,4,2,2.5,1,1,1])

y = np.array([1,1,1.1,1,0.9,1,1,1.1,-3,-5,1,1.1,1,1,0.9,1,1,1.1,1,1,1,1,1.1,0.9,1,1.1,1,1,0.9,
       1,1.1,1,1,1.1,1,0.8,0.9,1,1.2,0.9,1,1,1.1,1.2,1.2,1.3,1.4,1.5,2,3,4,4,4,4,5,5,5,4,3,
       4,4,3,4,4,3,3,4,4,3,4,4,4,4,5,5,5,4,3,
       4,4,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,3,3,4,4,4,2,2.5,1,1,1])
    
#df = pd.read_csv('/Users/rstyczynski/Documents/IKEA/11.Test/TESTS/TEST2505#5/ppseelm-lx41085/tmp/umc/TEST2505#5/2018-05-25/2018-05-25-140250_vmstat.log')
#df['datetime'] = pd.to_datetime(df['datetime'])
#df.index = df['datetime']

#y = df[' CPUuser'].values
    
# Settings: lag = 30, threshold = 5, influence = 0
lag = 30
threshold = 2
influence = 2

start = time.time()
for cnt in range(0, 100):
    # Run algo with settings from above
    result = thresholding_algo(y, lag=lag, threshold=threshold, influence=influence)
end = time.time()
print(end - start)

# Plot result
pylab.subplot(211)
pylab.plot(np.arange(1, len(y)+1), y)

pylab.plot(np.arange(1, len(y)+1),
           result["meanFilter"], color="cyan", lw=2)

pylab.plot(np.arange(1, len(y)+1),
           result["meanFilter"] + threshold * result["stdFilter"], color="green", lw=2)

pylab.plot(np.arange(1, len(y)+1),
           result["meanFilter"] - threshold * result["stdFilter"], color="green", lw=2)

pylab.subplot(212)
pylab.step(np.arange(1, len(y)+1), result["signals"], color="red", lw=2)
#pylab.ylim(-1.5, 1.5)

#pylab.plot(result["filteredY"], color="red", lw=2)
