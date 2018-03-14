#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import imp
import sys

module = sys.argv[1]

try:
    imp.find_module(module)
    found = exit(0)
except ImportError:
    found = exit(1)
    