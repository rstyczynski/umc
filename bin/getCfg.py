#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import yaml

yamlFile=sys.argv[1]
getData=sys.argv[2]
try:
    delim=sys.argv[3]
except:
    delim='.'
    
try:
    yamlDoc = open(yamlFile, 'r')
    doc = yaml.load(yamlDoc, Loader=yaml.SafeLoader)

    finalDoc=doc
    for cfgElement in getData.split(delim):
	try:
		finalDoc = finalDoc[cfgElement]
	except:
		finalDoc = '';
    print finalDoc
except IOError:
    pass
