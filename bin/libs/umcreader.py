
import os
import re
import datetime
import csv
import utils

import messages as Msg
from utils import Map

# global variables
epoch = datetime.datetime.utcfromtimestamp(0)

# umc configuration object for umc configuration file metrics.conf
class UmcReader:
    def __init__(self, config, tool):
        self.config=config
        
        section="common.umcpush.{tool}.reader-params.".format(tool=tool)
        self.params=Map(
            max_batchsize_rows  = self.config.value(section + "max-batchsize-rows", 50),
            max_batchsize_files = self.config.value(section + "max-batchsize-files", 300),
            log_file_group      = self.config.value(section + "log-file-group", 1),
            common_tags         = self.config.value(section + "tags").split(','),
            common_fields       = self.config.value(section + "fields").split(','),
            default_timefield   = self.config.value(section + "timefield", "datetime"),
            default_timeformat  = self.config.value(section + "timeformat", "%Y-%m-%d %H:%M:%S"),
            tzoffset            = utils.float_ex(self.config.value(section + "timezone", 0), 0)
        )
        
    # *** reads and checks umc definition for a specific umc id
    def read_umcdef(self, umc_id, umcconf): 
        # tags and fields cols of this umc definition
        tcols = [x.strip() for x in self.config.value_element(umcconf, "reader.tags").split(',') if x != '' ]
        fcols = [x.strip() for x in self.config.value_element(umcconf, "reader.fields").split(',') if x != '' ]
        
        # combine with common tags and fields cols
        tcols.extend(x for x in 
            [y.strip() for y in self.params.common_tags ] 
            if x != '' and x not in tcols and '!'+x not in tcols )
        fcols.extend(x for x in 
            [y.strip() for y in self.params.common_fields ] 
            if x != '' and x not in fcols and '!'+x not in tcols )
        
        # remove all commented out fields and tags
        tcols = [x for x in tcols if not(x.startswith('!')) ]
        fcols = [x for x in fcols if not(x.startswith('!')) ]
        
        # read and check time field and its format
        timeformat=self.config.value_element(umcconf, "reader.timeformat", self.params.default_timeformat)
        try:
            if timeformat not in ['_unix_', '_time_s_', '_time_ms_']:
                strftime(timeformat, gmtime())
        except Exception as e:
            raise Exception("The time format '%s' is invalid for umc '%s': %s!" % (timeformat,umc_id,e)) 
                
        timefield=self.config.value_element(umcconf, "reader.timefield", self.params.default_timefield)   
        tzfield=self.config.value_element(umcconf, "reader.tzfield", None)   
        
        filter=self.config.value_element(umcconf, "reader.filter", None)
        
        # transformation expressions
        transform=self.config.value_element(umcconf, "reader.transform", None)
        
        return Map(tcols=tcols,fcols=fcols,timeformat=timeformat,timefield=timefield,tzfield=tzfield,
            filter=filter,transform=transform)
    # // read_umcdef

    # unix time
    def unix_time_millis(self, dt):
        return int((dt - epoch).total_seconds() * 1000)

    # retrieves the first batch of log files sorted by modified time
    def get_batch_logs(self, logDir):
        pattern = re.compile(".+_[0-9]+.*\.log.{log_file_group}$".format(log_file_group=self.params.log_file_group))
        search_re=logDir + "/[a-zA-Z0-9\._\-]+/([a-zA-Z0-9\-\._]+)" # + "|".join(GlobalContext.config.umc_instanceids(False)) + ")$";
        umc_instanceids=self.config.umc_instanceids(False)
        
        batch=[]; cnt=0
        for dirname, dirnames, filenames in os.walk(logDir):
            m=re.match(search_re, dirname)
            if m and m.group(1) in umc_instanceids:
                for filename in filenames:
                    if pattern.match(filename):
                        cnt=cnt+1
                        if cnt <= self.params.max_batchsize_files: 
                            batch.append(os.path.join(dirname, filename))
            if cnt > self.params.max_batchsize_files:
                break
        return sorted(batch, key=lambda fn: os.stat(fn).st_mtime, reverse=True)
    # // get_batch_logs
        
    # evaluates filter on the row's tags and fields values        
    def eval_filter(self, umc_id, filter, tags, fields):
        try:
            for k,v in tags.items():
                if v is not None:
                    exec(k + "=\"" + v + "\"")
            for k,v in fields.items():
                if v is not None:
                    exec(k + "=" + str(v))
            return eval(filter)
        except Exception as e:
            Msg.err_msg("Error when evaluating the filter '%s' for %s: %s!" % (filter, umc_id, str(e))) 
            return False      
    # // eval_filter

    def eval_transform(self, umc_id, transform, tags, fields):
        try:
            # declare variables and assign values to them
            for k,v in tags.items():
                if v is not None:
                    exec(k + "=\"" + v + "\"")
            for k,v in fields.items():
                if v is not None:
                    exec(k + "=" + str(v))
            
            # transform                 
            for e in transform:
                try:
                    exec(e)
                except Exception as ex:
                    pass
                    #info1_msg("Error when evaluating transformation '%s' for %s: %s"%(e,umc_id,str(ex)))

            # create resulting tags and fields
            __t2 = {}
            for k,v in tags.items():
                exec("__t2['%s']=%s"%(k,k))
            
            __f2 = {}
            for k,v in fields.items():
                exec("__f2['%s']=%s"%(k,k))
            
            return __t2,__f2
        except Exception as e:
            Msg.err_msg("Error when evaluating transformations for %s: %s"%(umc_id, str(e)))
            return tags,fields
    # // eval_transform

    # read data points from the csv log file
    def read_datapoints(self, logfilename, umcdef, create_writeitem_func):    
        datapoints = []; notags=False; nofields=False; 
        tzoffset = self.params.tzoffset   
     
        if umcdef.enabled: 
            # read datapoints
            with open(logfilename, 'r') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=',')
                for row in reader:
                    # remove None keys
                    row = { k:v for k, v in row.items() if k is not None }
                    
                    # timestamp
                    try:
                        if not(umcdef.reader.timefield in row):
                            raise ValueError("Cannot find time field '" + umcdef.reader.timefield + "' in data row!")                         
                        if umcdef.reader.timeformat == "_unix_" or umcdef.reader.timeformat == "_time_s_":
                            timestamp = long(row[umcdef.reader.timefield]) * 1000000000  
                        elif umcdef.reader.timeformat == "_time_ms_":
                            timestamp = long(row[umcdef.reader.timefield]) * 1000000               
                        else:
                            if umcdef.reader.tzfield is not None and umcdef.reader.tzfield in row:
                                tzoffset = utils.float_ex(row[umcdef.reader.tzfield], self.params.tzoffset)                        
                            timestamp = (self.unix_time_millis(datetime.datetime.strptime(row[umcdef.reader.timefield],umcdef.reader.timeformat)) - int(tzoffset*60*60*1000)) * 1000000
                    except Exception as e:
                        # output error and skip this row
                        Msg.err_msg("Cannot read or convert time to timestamp for %s: %s"%(umcdef.umcid,str(e)))
                        continue     
                    
                    # create tags and fields
                    tags   = { k:str(v)            for k, v in row.items() if k in umcdef.reader.tcols }
                    fields = { k:utils.float_ex(v) for k, v in row.items() if k in umcdef.reader.fcols }                
                    notags = (len(tags) == 0)
                    
                    # only add this row if there is at least one field with some value
                    if len([ v for k,v in fields.items() if v is not None ])>0:
                        # evaluate transformations
                        if umcdef.reader.transform is not None:
                            tags,fields = self.eval_transform(umcdef.umcid, umcdef.reader.transform,tags,fields)

                        # only add this row if filter holds on this row or there is no filter
                        if umcdef.reader.filter is None or self.eval_filter(umcdef.umcid, umcdef.reader.filter, tags, fields):
                            record=create_writeitem_func(umcdef, timestamp, fields, tags)
                            if record is not None:
                                datapoints.append(record)
                        
                # // end reading rows
            # // end open file
                
        # check for no tags
        if notags and len(datapoints) > 0:
            Msg.warn_msg("The definition of %s contains no tags presented in the log file %s!"%(umcdef.umcid,os.path.basename(logfilename)))
                    
        return datapoints
        
