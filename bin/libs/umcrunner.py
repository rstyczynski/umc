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

class UmcRunner:
    # reads all umcrunner common parameters
    def __init__(self, config):
        self.config=config
        self.params=Map(
            http_enabled        = self.config.value("common.umcrunner.http.enabled", True),
            tcp_port            = self.config.value("common.umcrunner.http.tcp-port", 1989),
            
            log_file_copies     = self.config.value("common.umcrunner.log-file-copies", 1),
            
            run_interval        = self.config.value("common.umcrunner.run-interval", 10),
            prcstats_interval   = self.config.value("common.umcrunner.prcstats-interval", 5),
            logstats_interval   = self.config.value("common.umcrunner.logstats-interval", 60),
            logstats_max_duration = self.config.value("common.umcrunner.logstats-max-duration", 2),
            orphans_interval    = self.config.value("common.umcrunner.orphans-interval", 5),
            maxproc_interval    = self.config.value("common.umcrunner.maxproc-interval", 5),
            maxzombies_interval = self.config.value("common.umcrunner.maxzombies-interval", 5),
            loop_interval       = self.config.value("common.umcrunner.loop-interval", 10),
                         
            max_processes       = self.config.value("common.umcrunner.max-processes", 200),
            retc_history        = self.config.value("common.umcrunner.returncodes-history", 10),

            proxy_timeout_connect = self.config.value("common.umcrunner.proxy-timeout-connect", 0.5),
            proxy_timeout_read  = self.config.value("common.umcrunner.proxy-timeout-read", 5),
            proxy_run_threads   = self.config.value("common.umcrunner.proxy-run-threads", True),

            min_starting_time   = self.config.value("common.umcrunner.min-starting-time", 60),
            run_after_failure   = self.config.value("common.umcrunner.run-after-failure", 60),
            
            oserror_max_attempts = self.config.value("common.umcrunner.oserror-max-attempts", 5),
            oserror_wait_time   = self.config.value("common.umcrunner.oserror-wait-time", 60))

    # get umcrunner server list
    def serverlist(self):
        # default tcp port
        tcp_port = self.config.value("common.umcrunner.http.tcp-port", 1989)    

        # create dict object
        server_list = {}
        server_binding = self.config.value("common.umcrunner.http.server-binding")
        for sb in server_binding:
            sb_def = { k:v.strip('",\'') for k,v in re.findall(r'(\S+)=(".*?"|\S+)', sb) }
            if sb_def.get("hostname") is not None:
                df = Map(
                    hostname=sb_def["hostname"],
                    address=sb_def["address"],
                    tcp_port=sb_def["tcp_port"] if sb_def.get("tcp_port") else tcp_port,
                    enabled=(True if sb_def.get("enabled") is not None and sb_def["enabled"].lower() == 'true' else False),
                    me=(True if sb_def.get("hostname").lower()==socket.gethostname().lower() else False)
                    # TODO: check that address is on this host = better "me"
                )
                server_list[sb_def["hostname"]] = df
        
        return server_list
    # // serverlist

    # umcrunner umc instance specific parameters 
    def read_umcdefs(self):
        for umc_instanceid in self.config.umc_instanceids():
            # yaml key where the configuration should be located
            key="umc-%s"%umc_instanceid
            
            # get umc definition
            umcconf=self.config.value(key, None, ":")
            if umcconf is None:
                raise Exception("umc configuration for '%s' does not exist (YAML key %s not found)!" % (umc_id, key)) 

            # is this entry for this host?
            hostname=socket.gethostname().lower()
            hosts = [ h.strip().lower() for h in self.config.value_element(umcconf, "umcrunner.hosts", '').split(',') ]                
                
            if "_all_" in hosts or hostname in hosts:
                # enabled        
                enabled=self.config.value_element(umcconf, "enabled", False)

                # parameters
                rotation_timelimit = None
                umc_toolid = None; delay = None; count = None; params = None        
                paramslist=self.config.value_element(umcconf, "umcrunner.params", None)
                
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
                
                options = [ o.strip() for o in self.config.value_element(umcconf, "umcrunner.options", "").split(',') ]
                                
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
            
            # // end if for this host
        # // end for
    # // read_umcdefs   