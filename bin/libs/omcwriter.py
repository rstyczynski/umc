import sys
import re
import utils
import json
import requests
import time

import messages as Msg

from requests.auth import HTTPBasicAuth
from utils import Map 
from datetime import datetime as dt
from time import sleep
from umcwriter import UmcWriter

class OMCWriter(UmcWriter):
    
    def __init__(self, config):
        super(OMCWriter, self).__init__(config, "omc")
        
        # read params
        self.omc_params=Map(
            base_url=self.param("connect.base-url"), 
            data_url=self.param("connect.data-url"),
            proxies=self.param("connect.proxies"),
            user=self.param("connect.user"), 
            upass=self.param("connect.pass", ""),
            connect_timeout=self.param("connect.connect-timeout", 5),
            read_timeout=self.param("connect.read-timeout", 10))
        
        # check the db was defined
        if self.omc_params.data_url == None:
            raise Exception("Invalid connection details (data_url is missing).")
    # // init

    # reads and checks umc definition for a specific umc id
    def read_umcdef(self, umc_id, umcconf):
        key="writer." + self.writer_id + "."

        # get and check metric
        fields=self.config.value_element(umcconf,key+"fields", None)
        entity=self.config.value_element(umcconf,key+"entity", None)
        
        if fields is not None:
            return Map(fields=fields, entity=entity)
        else:
            return None
    # // read_umcdef
        
    def run_request(self, method, url, data=None, ContentType=None):
        return requests.request(method, self.omc_params.base_url+url, 
            proxies=self.omc_params.proxies,
            timeout=(self.omc_params.connect_timeout, self.omc_params.read_timeout), 
            auth=HTTPBasicAuth(self.omc_params.user, self.omc_params.upass) if self.omc_params.user is not None else None,
            allow_redirects=True,
            headers={'Content-Type': ContentType } if ContentType is not None else None,
            data=json.dumps(data) if data is not None else None)
    # // run_request
        
    # creates an object to be later writen by this writer
    def createWriteItem(self,umcdef,timestamp,fields,tags):
        # values from the reader are in float; this will convert them all to int
        # TODO: define explicit function to convert based on a defined type
        f = { k:int(v) for k,v in fields.items() }
        f.update(tags)
        
        # create the payload
        data = { k:v for k,v in umcdef.writer.entity.items() }
                     
        # the timestamp from the reader is in UTC time already 
        # (note that it could have been converted by using timezone parameter)
        # will send timestamp in UTC; if other timezone is required, this will need to be implemented here
        data["collectionTs"]=dt.utcfromtimestamp(timestamp/1000000000).isoformat() + "Z"  
        data["metricNames"]=[ metric for metric in umcdef.writer.fields.split(",") ]        
        data["metricValues"] = [ [ "%s"%f.get(k) for k in data["metricNames"] ] ]
        
        return data #"measurement" : umcdef.writer.metric, "time" : timestamp, "fields" : fields, "tags": tags }
    # // createWriteItem
        
    def write(self,datapoints,exit_event=None):
        Msg.info2_msg("Uploading %d records to OMC..."%len(datapoints))        
        response = self.run_request('POST',self.omc_params.data_url, datapoints, 'application/octet-stream')
        if response.status_code<300:
            resp=json.loads(response.text)
            status_uri=resp["statusUri"]
            
            start_t=time.time()
            while resp["status"]=="IN_PROGRESS" and (exit_event is not None and not(exit_event.is_set())):
                response=self.run_request('GET',status_uri)
                if response.status_code>=300:
                    raise Exception("OMC status request failed with status code %d"%response.status_code)    
                
                resp=json.loads(response.text)
                if resp["status"]=="IN_PROGRESS":
                    exit_event.wait(1) if exit_event is not None else sleep(1)
            # // while

            if resp["status"]=="FAILED":
                raise Exception("OMC upload reuqest failed. %s."
                    %(resp["errorMessage"]))
            elif exit_event is None or not(exit_event.is_set()):
                Msg.info2_msg("OMC upload reuqest processed in %d seconds. %s: %s."
                    %(time.time()-start_t,resp["status"],resp["errorMessage"]))
        else:
            raise Exception("OMC data upload request failed with status code %d"%response.status_code)    
        