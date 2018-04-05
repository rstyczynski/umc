#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import yaml

yamlFile=sys.argv[1]
getData=sys.argv[2]

try:
    yamlDoc = open(yamlFile, 'r')
    doc = yaml.load(yamlDoc)

    finalDoc=doc
    for cfgElement in getData.split('.'):
	try:
		finalDoc = finalDoc[cfgElement]
	except:
		finalDoc = '';
    print finalDoc
except IOError:
    pass
