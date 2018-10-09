
import re
from influxdb import InfluxDBClient
from utils import Map 

import messages as Msg


class InfluxDBWriter:
    
    def __init__(self, config, tool):
        self.tool=tool
        self.config=config
        base_key="common.umcpush.{tool}.".format(tool=self.tool)
        
        # read params
        self.params=Map(
            db_url              = self.config.value(base_key + "connect.url", None),
            db_user             = self.config.value(base_key + "connect.user", None), 
            db_pass             = self.config.value(base_key + "connect.pass", None),
            db_name             = self.config.value(base_key + "connect.dbname", None),
            delay_writes        = self.config.value(base_key + "writer-params.delay-between-writes", 200),
            delay_runs          = self.config.value(base_key + "writer-params.delay-between-runs", 10000)/1000,
            retry_count         = self.config.value(base_key + "writer-params.connection-error-retry-count", 5),
            retry_interval      = self.config.value(base_key + "writer-params.connection-error-retry-interval", 10000)/1000,
            remove_nodata_files = self.config.value(base_key + "writer-params.remove-backlog-files-no-data", False)
        )
        
        # check the db was defined
        if self.params.db_url == None or self.params.db_name == None:
            raise Exception("Invalid DB connection details (db_url or db_name is missing).")
        
        # parse url to get host and port
        m = re.search("http://([a-zA-Z0-9\.]+):([0-9]+)/?", self.params.db_url)    
        if not(m):
            raise Exception('The DB url %s is invalid.'%db_url);
        self.params.host=m.group(1)
        self.params.port=m.group(2)
        
        # create the influxdb client
        self.client=InfluxDBClient(self.params.host, self.params.port, self.params.db_user, 
            self.params.db_pass, self.params.db_name)
        Msg.info1_msg("DB connection details are: host=%s,port=%s,user=%s,pass=xxxxx,dbname=%s"
            %(self.params.host,self.params.port,self.params.db_user,self.params.db_name))
    # // init

    # *** reads and checks umc definition for a specific umc id
    def read_umcdef(self, umc_id, umcconf):
        # TODO: rewrite any idbpush specific csv reader params here

        # get and check metric
        metric=self.config.value_element(umcconf, "writer." + self.tool + ".name", None)
        
        return Map(metric=metric)
    # // idbpush_umcdef
        
    # creates an object to be later writen by this writer
    def createWriteItem(self,umcdef,timestamp,fields,tags):
        return  { "measurement" : umcdef.writer.metric, "time" : timestamp, "fields" : fields, "tags": tags }
    # // createWriteItem
        
    def write(self,datapoints):
        self.client.write_points(datapoints)        
    
        
        
    