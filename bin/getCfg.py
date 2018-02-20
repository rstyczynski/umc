#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import yaml

yamlFile=sys.argv[1]
getData=sys.argv[2]


with open(yamlFile, 'r') as yamlDoc:
    doc = yaml.load(yamlDoc)

finalDoc=doc
for cfgElement in getData.split('.'):
    finalDoc = finalDoc[cfgElement]
print finalDoc
