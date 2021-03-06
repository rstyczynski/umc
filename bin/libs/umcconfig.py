
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

# patterns to match environment variables in YAML document
# they must be in a form ${VARIABLE_NAME}
ENVPARAM_PATTERN="\$\{[a-zA-Z0-9_]+\}"

# matcher and resolver to resolve environment variables to values in YAML
def env_constructor(loader, node):
  value = node.value    
  params = list(set(re.findall("(%s)"%ENVPARAM_PATTERN, value)))
  if len(params)>0:
    for k in params:
      env_value=os.environ.get(k[2:-1])
      if env_value is None:
        Msg.err_msg("The environment variable %s used in the configuration file does not exist!"%(k))
      else:
        value = value.replace(k, env_value)
  return value

def include_constructor(loader, node):
    filename = os.path.join(env_constructor(loader, node))
    if not(os.path.exists(filename)):
        Msg.err_msg("The include file %s does not exist!"%filename)
        return []
    else:
        with open(filename, 'r') as f:
            return yaml.load(f)

# register resolver with YAML parser
yaml.add_implicit_resolver('!env', re.compile(r'.*%s.*'%ENVPARAM_PATTERN))
yaml.add_constructor('!env', env_constructor)
yaml.add_constructor('!include', include_constructor)

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
            nfl=os.path.dirname(os.path.realpath(__file__)) + "/../" + self.configFile
            if os.path.exists(nfl):
                self.configFile=nfl
            else:
                raise Exception("Configuration file %s does not exist!"%self.configFile)
        
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

    # reads all umc instances; this converts array of instances returned by !include
    def get_umc_instances(self):
        
        def append_instance(umcinstances, e):
            exists=False
            for u in umcinstances:
                if e["umc-id"]==u["umc-id"]:
                    exists=True
                    break
                # // if
            # // for
            
            if not(exists):
                umcinstances.append(e)
            else:
                Msg.err_msg("The umc instance with the same id=%s already exists!"%(e["umc-id"]))
        # // append_instance            
        
        umcinstances=[]
        for e in self.value("umc-instances", []):
            if isinstance(e, list):
                for e1 in e:
                    append_instance(umcinstances, e1)
            else:
                append_instance(umcinstances, e)
        return umcinstances
    # // get_umc_instances

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
        allinstances=self.get_umc_instances()
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
                

