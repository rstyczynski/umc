
import yaml
import os
import re
import json
import psutil
import time
import socket
import utils
import messages as Msg

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
    # // init

    # last time the configuration file was modified
    def isModified():
        if self.conf_mtime != os.stat(self.configFile).st_mtime:
            return True
        else:
            return False
    # // isModified

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
    # // value_element

    def value(self, path, default='',delim='.'):
        return self.value_element(self.YAMLfile,path,default,delim)
    # // value

    # retrieves umc id from a log filename
    def get_umcid_from_logfile(self,logfile):
        dirname=os.path.dirname(logfile)
        m=re.match(".+/([a-zA-Z0-9\\._]+)/?$", dirname)
        if m:
            return m.group(1)
        else:
            return None
    # // get_umcid_from_logfile

    def read_umcdefs(self, reader, writer):
        allinstances=self.value("umc-instances", [])
        umcdefs={}
        
        for instance in allinstances:
            umc_id=instance["umc-id"]
            
            umcdef=Map(umcid=umc_id,enabled=False,writer=None,reader=None,instance=instance)
            umcdef.enabled = self.value_element(instance,"enabled",False)                        
            umcdef.writer  = writer.read_umcdef(umc_id,instance)
            umcdef.reader  = reader.read_umcdef(umc_id,instance)
            Msg.info1_msg("Definition retrieved for umc %s"%(umc_id))
            
            if not(umcdef.enabled):
                Msg.info1_msg("umc id %s is disabled by configuration, no datapoints will be read."%(umc_id))
            elif umcdef.writer is None or umcdef.reader is None:
                Msg.info2_msg("umc id %s does not have reader or writer definitions and it will be disabled."%(umc_id))
                umcdef.enabled=False

            # disable if the writer is not enabled
            if not(umcdef.writer.enabled):
                Msg.info2_msg("umc id %s is disabled as its writer is disabled. No data will be read for this umc id."%(umc_id))                            
                umcdef.enabled = False
            
            if umcdefs.get(umc_id) is not None:
                Msg.err_msg("There is a duplicate umc instance with id '%s' in the configuration file!"%(umc_id))            
            else: 
                umcdefs[umc_id]=umcdef
        # // for                        
        
        return umcdefs
    # // read_umcdefs
                

