
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

    # reads all umcrunner params
    def umcrunner_params(self):
        return Map(
            http_enabled        = self.value("common.umcrunner.http.enabled", True),
            tcp_port            = self.value("common.umcrunner.http.tcp-port", 1989),
            
            log_file_copies     = self.value("common.umcrunner.log-file-copies", 1),
            
            run_interval        = self.value("common.umcrunner.run-interval", 10),
            prcstats_interval   = self.value("common.umcrunner.prcstats-interval", 5),
            logstats_interval   = self.value("common.umcrunner.logstats-interval", 60),
            logstats_max_duration = self.value("common.umcrunner.logstats-max-duration", 2),
            orphans_interval    = self.value("common.umcrunner.orphans-interval", 5),
            maxproc_interval    = self.value("common.umcrunner.maxproc-interval", 5),
            maxzombies_interval = self.value("common.umcrunner.maxzombies-interval", 5),
            loop_interval       = self.value("common.umcrunner.loop-interval", 10),
                         
            max_processes       = self.value("common.umcrunner.max-processes", 200),
            retc_history        = self.value("common.umcrunner.returncodes-history", 10),

            proxy_timeout_connect = self.value("common.umcrunner.proxy-timeout-connect", 0.5),
            proxy_timeout_read  = self.value("common.umcrunner.proxy-timeout-read", 5),
            proxy_run_threads   = self.value("common.umcrunner.proxy-run-threads", True),

            min_starting_time   = self.value("common.umcrunner.min-starting-time", 60),
            run_after_failure   = self.value("common.umcrunner.run-after-failure", 60),
            
            oserror_max_attempts = self.value("common.umcrunner.oserror-max-attempts", 5),
            oserror_wait_time   = self.value("common.umcrunner.oserror-wait-time", 60))

    # retrieves umc instance configuration for umcrunner
    def umcrunner_umcdefs(self):
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
    def umcrunner_serverlist(self):
        # default tcp port
        tcp_port = self.value("common.umcrunner.http.tcp-port", 1989)    

        # create dict object
        server_list = {}
        server_binding = self.value("common.umcrunner.http.server-binding")
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
        
    # idbpush params
    def idbpush_params(self):        
        params=Map(
            db_url              = self.value("common.idbpush.db.url", None),
            db_user             = self.value("common.idbpush.db.user", None), 
            db_pass             = self.value("common.idbpush.db.pass", None),
            db_name             = self.value("common.idbpush.db.dbname", None),
            delay_writes        = self.value("common.idbpush.delay-between-writes", 200),
            delay_runs          = self.value("common.idbpush.delay-between-runs", 10000)/1000,
            retry_count         = self.value("common.idbpush.connection-error-retry-count", 5),
            retry_interval      = self.value("common.idbpush.connection-error-retry-interval", 10000)/1000,
            max_batchsize_rows  = self.value("common.idbpush.max-batchsize-rows", 50),
            max_batchsize_files = self.value("common.idbpush.max-batchsize-files", 300),
            log_file_group      = self.value("common.idbpush.log-file-group", 1),
            tzoffset            = utils.float_ex(self.value("common.idbpush.timezone", 0), 0)
        )
        
        # check the db was defined
        if params.db_url == None or params.db_name == None:
            raise Exception("Invalid DB connection details (db_url or db_name is missing).")
        
        # parse url to get host and port
        m = re.search("http://([a-zA-Z0-9\.]+):([0-9]+)/?", params.db_url)    
        if not(m):
            raise Exception('The DB url %s is invalid.'%db_url);
        params.host=m.group(1)
        params.port=m.group(2)
        
        return params
        
    # *** reads and checks umc definition for a specific umc id
    def idbpush_umcdef(self,umc_id):
        # get umc definition
        umcconf=self.value("umc-" + umc_id, None, ":")
        # check umc id and def were retrieved ok
        if umcconf is None:
            raise Exception("Error when getting umc configuration for '%s'!" % (umc_id)) 

        # is enabled        
        enabled=self.value_element(umcconf,"enabled",False)

        # get and check metric
        metric=self.value_element(umcconf, "idbpush.name", None)
            
        # tags and fields cols of this umc definition
        tcols = [x.strip() for x in self.value_element(umcconf, "idbpush.tags").split(',') if x != '' ]
        fcols = [x.strip() for x in self.value_element(umcconf, "idbpush.fields").split(',') if x != '' ]
        
        # combine with common tags and fields cols
        tcols.extend(x for x in 
            [y.strip() for y in self.value("common.idbpush.tags").split(',') ] 
            if x != '' and x not in tcols and '!'+x not in tcols )
        fcols.extend(x for x in 
            [y.strip() for y in self.value("common.idbpush.fields").split(',') ] 
            if x != '' and x not in fcols and '!'+x not in tcols )
        
        # remove all commented out fields and tags
        tcols = [x for x in tcols if not(x.startswith('!')) ]
        fcols = [x for x in fcols if not(x.startswith('!')) ]
        
        # read and check time field and its format
        timeformat=self.value_element(umcconf, "idbpush.timeformat", self.value("common.idbpush.timeformat", "%Y-%m-%d %H:%M:%S"))
        try:
            if timeformat not in ['_unix_', '_time_s_', '_time_ms_']:
                strftime(timeformat, gmtime())
        except Exception as e:
            raise Exception("The time format '%s' is invalid for umc '%s': %s!" % (timeformat,umc_id,e)) 
                
        timefield=self.value_element(umcconf, "idbpush.timefield", self.value("common.idbpush.timefield", "datatime"))   
        tzfield=self.value_element(umcconf, "idbpush.tzfield", None)   
        
        filter=self.value_element(umcconf, "idbpush.filter", None)
        
        # transformation expressions
        transform=self.value_element(umcconf, "idbpush.transform", None)
        
        return Map(umcid=umc_id,umcconf=umcconf,metric=metric,enabled=enabled,tcols=tcols,fcols=fcols,
            timeformat=timeformat,timefield=timefield,tzfield=tzfield,filter=filter,transform=transform,datapoints=[],datafiles=[])
    

