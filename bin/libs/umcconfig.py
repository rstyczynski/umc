
import yaml
import os
import re
import json
import psutil
import time
import socket
import utils

from threading import RLock
from time import gmtime, strftime

from utils import Map

# umc configuration object for umc configuration file metrics.conf
class UmcConfig:
    # ***
    # *** initialization and helpers
    # ***
    def __init__(self, configFile):
        self.configFile = configFile

        # read configuration file
        try:
            nfl=os.path.dirname(os.path.realpath(__file__)) + "/../" + self.configFile
            if not(os.path.exists(self.configFile)) and os.path.exists(nfl):
                #warn_msg("The configuration file %s does not exist in the current directory, will try the umc home bin directory."%(self.configFile))
                self.configFile = nfl
            
            with open(self.configFile, 'r') as confDoc:
                self.conf=yaml.load(confDoc)
            self.conf_mtime=os.stat(self.configFile).st_mtime   
                             
        except Exception as e:
            raise Exception("Error when reading the configuration file %s: %s"%(self.configFile,e))

    # last time the configuration file was modified
    def isModified():
        if self.conf_mtime != os.stat(self.configFile).st_mtime:
            return True
        else:
            return False

    # reads a configuration value
    def value_element(self, cfg, path, default='',delim='.'):
        finalDoc = cfg
        if finalDoc is not None:
            for e in path.split(delim):
            	try:
            		finalDoc = finalDoc[e]
            	except:
            		finalDoc = default;
        if finalDoc is None:
            finalDoc = default
        return finalDoc

    def value(self, path, default='',delim='.'):
        return self.value_element(self.conf,path,default,delim)

    # returns all umc instance ids from the configuration file
    # these are top-level keys prefixed with "umc-"; keys that do not match this patterns will be ignored
    def umc_instanceids(self, all=True):
        umc_instanceids=[]
        for key in self.conf:
            m = re.match(r"^umc-(.+)",key) 
            if m and (all or self.value(key + ":enabled", False, ":") == True):
                umc_instanceids.append(m.group(1))
        return umc_instanceids

    # *** get umc id from the log file name
    def get_umcid_from_logfile(self,logfile):
        dirname=os.path.dirname(logfile)
        m=re.match(".+/([a-zA-Z0-9\\._]+)/?$", dirname)
        if m:
            return m.group(1)
        else:
            return None
        
                

