#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import imp
import sys

module = sys.argv[1]

try:
    imp.find_module(module)
    sys.exit(0)
except ImportError:
    sys.exit(1)
    
