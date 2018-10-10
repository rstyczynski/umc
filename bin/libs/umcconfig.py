
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
    def __init__(self, configFile=None, logDir=None):
        self.configFile = configFile

        # location of configuration file
        self.configFile=configFile
        if self.configFile is None or self.configFile == "":
            # try to get the config file from UMCRUNNER_CONFIG env variable
            self.configFile=os.environ.get('UMCRUNNER_CONFIG', None)

        if self.configFile is None or self.configFile == "":
            raise Exception("A valid configuration file must be specified on command line or in UMCRUNNER_CONFIG environment variable!")
            
        # check it exists, if not, look for it in the umc bin directory
        if not(os.path.exists(self.configFile)):
            nfl==os.path.dirname(os.path.realpath(__file__)) + "/../" + self.configFile
            if os.path.exists(nfl):
                self.configFile=nfl
            else:
                raise Exception("Configuration file %s does not exist!"%sself.configFile)
        
        # location of logs
        self.logDir = logDir
        if self.logDir == None or self.logDir == "":
            self.logDir=os.environ.get('UMC_LOG_DIR',os.path.dirname(os.path.realpath(__file__)) + "/../logs") 

        # read configuration file
        try:
            with open(self.configFile, 'r') as confDoc:
                self.YAMLfile=yaml.load(confDoc)
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
        return self.value_element(self.YAMLfile,path,default,delim)

    # retrieves umc id from a log filename
    def get_umcid_from_logfile(self,logfile):
        dirname=os.path.dirname(logfile)
        m=re.match(".+/([a-zA-Z0-9\\._]+)/?$", dirname)
        if m:
            return m.group(1)
        else:
            return None

    def read_umcdef(self,umc_id):
        return self.value("umc-" + umc_id, None, ":")        

    # returns all umc instance ids 
    # these are top-level keys prefixed with "umc-"; 
    # top-level keys that do not match this patterns will be ignored
    def umc_instanceids(self, all=True):
        umc_instanceids=[]
        for key in self.YAMLfile:
            m = re.match(r"^umc-(.+)",key) 
            if m and (all or self.value(key + ":enabled", False, ":") == True):
                umc_instanceids.append(m.group(1))
        # // for
        return umc_instanceids
    # // umc_instanceids
    
        
                

