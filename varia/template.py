#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 13:57:07 2018

@author: rstyczynski
"""

#!/usr/bin/python
import jinja2

templateLoader = jinja2.FileSystemLoader(searchpath="/Users/rstyczynski/github/umc/varia/jmeter/lib")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "plantuml.jinja"
template = templateEnv.get_template(TEMPLATE_FILE)

FLOW = 'A\nB\nC'

outputText = template.render(FLOW=FLOW, TESTID='ss')  

print(outputText)
