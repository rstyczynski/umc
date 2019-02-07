import re
import messages as Msg

from influxdb import InfluxDBClient
from utils import Map 
from umcwriter import UmcWriter

class InfluxDBWriter(UmcWriter):
    
    def __init__(self, config, writerDef):
        super(InfluxDBWriter, self).__init__(config, writerDef)
        
        # read params
        self.idb_params=Map(
            db_url  = self.param("connect.url", None),
            db_user = self.param("connect.user", None), 
            db_pass = self.param("connect.pass", None),
            db_name = self.param("connect.dbname", None)
        )
        
        # check the db was defined
        if self.idb_params.db_url == None or self.idb_params.db_name == None:
            raise Exception("Invalid DB connection details (db_url or db_name is missing).")
        
        # parse url to get host and port
        m = re.search("http://([a-zA-Z0-9\.]+):([0-9]+)/?", self.idb_params.db_url)    
        if not(m):
            raise Exception('The DB url %s is invalid.'%db_url);
        self.idb_params.host=m.group(1)
        self.idb_params.port=m.group(2)
        
        # create the influxdb client
        self.client=InfluxDBClient(self.idb_params.host, self.idb_params.port, self.idb_params.db_user, 
            self.idb_params.db_pass, self.idb_params.db_name)
        Msg.info1_msg("DB connection details are: host=%s,port=%s,user=%s,pass=xxxxx,dbname=%s"
            %(self.idb_params.host,self.idb_params.port,self.idb_params.db_user,self.idb_params.db_name))
    # // init

    # *** reads and checks umc definition for a specific umc id
    def read_umcdef(self, umc_id, umcconf):
        umcdef=super(InfluxDBWriter, self).read_umcdef(umc_id, umcconf)
        if umcdef.enabled:
            # TODO: rewrite any idbpush specific csv reader params here

            umcdef.metric=self.config.value_element(umcdef.writerDef, "name", None)
            include=self.config.value_element(umcdef.writerDef, "include", None)
            exclude=self.config.value_element(umcdef.writerDef, "exclude", None)
            
            if include is not None:
                umcdef.include = [ x.strip() for x in include.split(',') ]
            if exclude is not None:
                umcdef.exclude = [ x.strip() for x in exclude.split(',') ]
        # umcdef enabled
        
        return umcdef
    # // idbpush_umcdef
        
    # creates an object to be later writen by this writer
    def createWriteItem(self,umcdef,timestamp,fields,tags):
        t = { k:v for k,v in tags.items()   if (umcdef.writer.include is None or k in umcdef.writer.include) and (umcdef.writer.exclude is None or k not in umcdef.writer.exclude) }
        f = { k:v for k,v in fields.items() if (umcdef.writer.include is None or k in umcdef.writer.include) and (umcdef.writer.exclude is None or k not in umcdef.writer.exclude) }
        
        return  [ { "measurement" : umcdef.writer.metric, "time" : timestamp, "fields" : f, "tags": t } ]
    # // createWriteItem
        
    def write(self,datapoints,exit_event):
        self.client.write_points(datapoints)        
    
        
        
    