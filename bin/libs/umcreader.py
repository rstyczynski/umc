
import sys
import os
import re
import datetime
import csv
import utils
import transform

from time import gmtime, strftime
import messages as Msg
from utils import Map

from scandir import scandir, walk

# global variables
epoch = datetime.datetime.utcfromtimestamp(0)

# utility functions to evaluate python expressions defined in configuration strings
# evaluates filter on the row's tags and fields values        
def eval_filter(filter, timestamp, tags, fields):
    try:
        for k,v in tags.items():
            if v is not None:
                exec(k + "=\"" + str(v) + "\"")
        for k,v in fields.items():
            if v is not None:
                exec(k + "=" + str(v))
        return eval(filter)
    except Exception as e:
        Msg.err_msg("Error when evaluating the filter '%s': %s!" % (filter, str(e))) 
        return False      
# // eval_filter

# transformation of data
def eval_transform(transform_exprs, timestamp, tags, fields):
    try:
        # declare variables and assign values to them
        for k,v in tags.items():
            if v is not None:
                exec(k + "=\"" + v + "\"")
        for k,v in fields.items():
            if v is not None:
                exec(k + "=" + str(v))

        # transform                 
        for expr in transform_exprs:
            try:
                exec(expr)
            except Exception as ex:
                pass
                Msg.info2_msg("Error when evaluating transformation '%s': %s"%(expr,str(ex)))

        # get only variables that come from tags and fiedls, remove all local ones
        # the list in the below expression must contain all local variables in this function prior to this call!
        nf = { k:v for k,v in locals().items() if k not in ["k","v","umc_id","transform_exprs","timestamp","tags","fields","expr","ex"] } 
        
        __t2 = {}; __f2 = {}
        for k,v in nf.items():
            if k in tags.keys():
                exec("__t2['%s']=%s"%(k,k))
            elif k in fields.keys():
                exec("__f2['%s']=%s"%(k,k))
            else:
                exec("value=%s"%(k))
                if isinstance(value,int) or isinstance(value,float):
                    exec("__f2['%s']=%s"%(k,k))
                else:
                    exec("__t2['%s']=%s"%(k,k))
            # new tag or field that resulted from transformation
        # // for

        return __t2,__f2
    except Exception as e:
        Msg.err_msg("Error when evaluating transformations for %s: %s"%(umc_id, str(e)))
        return tags,fields
# // eval_transform

# umc configuration object for umc configuration file metrics.conf
class UmcReader:
    def __init__(self, config, writer_id):
        self.config=config
        
        # read common reader's params
        base_key="common.umcpush.reader-params"
        self.params=Map(
            max_batchsize_rows  = self.config.value(base_key + ".max-batchsize-rows", 50),
            max_batchsize_files = self.config.value(base_key + ".max-batchsize-files", 300),
            log_file_group      = self.config.value(base_key + ".log-file-group", 1),
            common_tags         = self.config.value(base_key + ".common-tags").split(','),
            common_fields       = self.config.value(base_key + ".common-fields").split(','),
            default_timefield   = self.config.value(base_key + ".default-timefield", "datetime"),
            default_timeformat  = self.config.value(base_key + ".default-timeformat", "%Y-%m-%d %H:%M:%S"),
            tzoffset            = utils.float_ex(self.config.value(base_key + ".tzoffset", 0), 0)
        )
        
        # update any value that may be overriden in writer's specific parameters
        writers=config.value("common.umcpush.writers")
        for writer in writers:
            if writer["writer-id"]==writer_id:
                rparams=writer["reader-params"]
                if rparams is not None:
                    for k,v in rparams.items():
                        k=k.replace("-", "_")
                        if self.params.get(k):
                            self.params[k]=v
                        else:
                            Msg.warn_msg("The reader param %s is invalid in %s"%(k,key))
        
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
    def get_batch_logs(self, logDir, umc_instanceids, files_in_buffer=[]):
        pattern = re.compile(".+_[0-9]+.*\.log.{log_file_group}$".format(log_file_group=self.params.log_file_group))
        search_re=logDir + "/[a-zA-Z0-9\._\-]+/([a-zA-Z0-9\-\._]+)" # + "|".join(GlobalContext.config.umc_instanceids(False)) + ")$";
        
        batch=[]; cnt=0
        for dirname, dirnames, filenames in walk(logDir):
            #Msg.info1_msg("walk: %s, filenames=%d"%(dirname,len(filenames)))
            m=re.match(search_re, dirname)
            if m and m.group(1) in umc_instanceids:
                for filename in filenames:
                    fullfname=os.path.join(dirname, filename)
                    if fullfname not in files_in_buffer and pattern.match(filename):
                        cnt=cnt+1
                        if cnt <= self.params.max_batchsize_files: 
                            batch.append(fullfname)
            if cnt > self.params.max_batchsize_files:
                break
        return sorted(batch, key=lambda fn: os.stat(fn).st_mtime, reverse=True)
    # // get_batch_logs
        
    # read data points from a single log file
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
                            tags,fields = eval_transform(umcdef.reader.transform,timestamp,tags,fields)

                        # only add this row if filter holds on this row or there is no filter
                        if umcdef.reader.filter is None or eval_filter(umcdef.reader.filter, timestamp,tags, fields):
                            try:
                                records=create_writeitem_func(umcdef, timestamp, fields, tags)
                                if records is not None and isinstance(records, list):
                                    datapoints+=records
                            except Exception as e:
                                Msg.err_msg("Error occured while creating data points item: %s"%str(e))
                        # // if write data
                        
                # // end reading rows
            # // end open file
                
        # check for no tags
        if notags and len(datapoints) > 0:
            Msg.warn_msg("The definition of %s contains no tags presented in the log file %s!"%(umcdef.umcid,os.path.basename(logfilename)))
                    
        return datapoints
        
