#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  6 14:08:12 2018

@author: rstyczynski
"""

import os
import sys
import fileinput

print ("Text to search for:")
textToSearch = '##'

print ("File to perform Search-Replace on:")
fileToSearch  = '/Users/rstyczynski/Documents/IKEA/11.Test/TESTS/TEST3105#12/README'

tempFile = open( fileToSearch, 'r+' )

verbatim=False

for line in fileinput.input( fileToSearch ):
    if textToSearch in line :
        if verbatim:
            print '</verbatim>'
        print '<h2>' + line.replace(textToSearch, '').replace('\n','').replace('\r','') + '</h2>'
        print '<verbatim>'
        verbatim=True
    else:
        print line

if verbatim:
    print '</verbatim>'

