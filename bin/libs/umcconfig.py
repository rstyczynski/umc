
import yaml
import os
import re
import json
import psutil
import time
import socket

from threading import RLock

from utils import Map

# umc configuration object for umc configuration file metrics.conf
class UmcConfig:
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
            
            # umcrunner parameters
            self.umcrunner_params = Map(
                http_enabled        = self.value("common.umcrunner.http.enabled", True),
                tcp_port            = self.value("common.umcrunner.http.tcp-port", 1989),
                
                run_interval        = self.value("common.umcrunner.run-interval", 10),
                stats_interval      = self.value("common.umcrunner.stats-interval", 5),
                orphans_interval    = self.value("common.umcrunner.orphans-interval", 5),
                maxproc_interval    = self.value("common.umcrunner.maxproc-interval", 5),
                maxzombies_interval = self.value("common.umcrunner.maxzombies-interval", 5),
                loop_interval       = self.value("common.umcrunner.loop-interval", 10),
                             
                max_processes       = self.value("common.umcrunner.max-processes", 200),
                retc_history        = self.value("common.umcrunner.returncodes-history", 10),

                proxy_timeout_connect = self.value("common.umcrunner.proxy-timeout-connect", 0.5),
                proxy_timeout_read    = self.value("common.umcrunner.proxy-timeout-connect", 0.5),
                proxy_run_threads   = self.value("common.umcrunner.proxy-run-threads", True),

                min_starting_time   = self.value("common.umcrunner.min-starting-time", 60),
                run_after_failure   = self.value("common.umcrunner.run-after-failure", 60))
                             
        except Exception as e:
            raise Exception("Error when reading the configuration file %s: %s"%(self.configFile,e))

    def isModified():
        if self.conf_mtime != os.stat(self.configFile).st_mtime:
            return True
        else:
            return False

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
    def umc_instanceids(self):
        umc_instanceids=[]
        for key in self.conf:
            m = re.match(r"^umc-(.+)",key) 
            if m:
                umc_instanceids.append(m.group(1))
        return umc_instanceids

    # retrieves umc instance id configuration for umcrunner
    def conf_umcrunner(self):
        for umc_instanceid in self.umc_instanceids():
            # yaml key where the configuration should be located
            key="umc-%s"%umc_instanceid
            
            # get umc definition
            umcconf=self.value(key, None, ":")
            if umcconf is None:
                raise Exception("umc configuration for '%s' does not exist (YAML key %s not found)!" % (umc_id, key)) 

            # is this entry for this host?
            hostname=socket.gethostname().lower()
            hosts = [ h.strip().lower() for h in self.value_element(umcconf, "umcrunner.hosts", '').split(',') ]                
                
            if "_all_" in hosts or hostname in hosts:
                # enabled        
                enabled=self.value_element(umcconf, "enabled", False)

                # parameters
                rotation_timelimit = None
                umc_toolid = None; delay = None; count = None; params = None        
                paramslist=self.value_element(umcconf, "umcrunner.params", None)
                
                if paramslist:
                    # parse param list
                    m = re.match(r"^([0-9]+) ([a-zA-Z0-9_]+) ([+\-]?[0-9]+) ([0-9]+)(.*)", paramslist) 
                    if m:
                        rotation_timelimit = m.group(1)
                        umc_toolid = m.group(2)
                        delay = m.group(3)
                        count = m.group(4)
                        params = m.group(5)
                        if len(params) > 0:
                            params = params.strip()        
                    else:
                        raise Exception("umcrunner.params is not valid for '%s'"%key)    
                
                options = [ o.strip() for o in self.value_element(umcconf, "umcrunner.options", "").split(',') ]
                                
                yield Map(
                    hostname=hostname,
                    umc_instanceid=umc_instanceid,
                    enabled=enabled,
                    rotation_timelimit=rotation_timelimit,
                    umc_toolid=umc_toolid,
                    delay=delay,
                    count=count,
                    params=params,
                    options=options,
                    num_runs=0,
                    num_errors=0,
                    first_started_time=0,
                    start_after=0,
                    returncodes=[],
                    lock=RLock()
                )
            
            # end if for this host
        # end for
    # end conf_umcrunner    
        
    # get umcrunner server list
    def get_server_list(self):
        # default tcp port
        tcp_port = self.value("common.umcrunner.http.tcp-port", 1989)    

        # create dict object
        server_list = {}
        server_binding = self.value("common.umcrunner.http.server-binding")
        for sb in server_binding:
            sb_def = { k:v.strip('",\'') for k,v in re.findall(r'(\S+)=(".*?"|\S+)', sb) }
            if sb_def.get("hostname") is not None:
                df = Map(
                    address=sb_def["address"],
                    tcp_port=sb_def["tcp_port"] if sb_def.get("tcp_port") else tcp_port,
                    enabled=(True if sb_def.get("enabled") is not None and sb_def["enabled"].lower() == 'true' else False),
                    me=(True if sb_def.get("hostname").lower()==socket.gethostname().lower() else False)
                    # TODO: check that address is on this host = better "me"
                )
                server_list[sb_def["hostname"]] = df
        
        return server_list
        
        
