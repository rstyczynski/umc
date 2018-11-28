
from utils import Map 

# creates an instance of the umc writer (a child of this class)
def create_instance(config, writer_id):
    writerDef=None
    writers=config.value("common.umcpush.writers")
    
    # get the writer with the specified id
    for writer in writers:
        if writer["writer-id"]==writer_id and writerDef is None:
            writerDef=writer
        elif writer["writer-id"]==writer_id and writerDef is not None:
            raise Exception("Invalid writer definition in the configuration file. There are two writer definitions with the same writer id %s!"%writer["writer-id"])

    mc=writerDef["classname"].split(".")
    if len(mc)!=2:
        raise Exception("The class definition '%s' of the writer id '%s' is not in a required format \{module\}.\{classname\}!"
            %(clazz,writerDef["writer-id"]))
        
    # instantiate the class
    try:
        class_ = getattr(__import__(mc[0]), mc[1])
        wobj=class_(config, writerDef)
    except AttributeError as e:
        raise
        #raise Exception("The writer class %s cannot be found!"%clazz)
    except Exception as e:
        raise Exception("Error occured when creating an instance of the writer's class %s with writer id %s. The error was: %s"
            %(clazz,writerDef["writer-id"],str(e)))
        
    # TODO: check wobj has required methods and fields and is a subclass of UmcWriter
    return wobj
# // create_instance

class UmcWriter(object):
    def __init__(self, config, writerDef):
        self.config=config
        self.writerDef=writerDef
        self.writer_id=writerDef["writer-id"]

        # read common writer's params
        base_key="common.umcpush.writer-params"
        self.params=Map(
            delay_writes = self.config.value(base_key + ".delay-writes", 0.2),
            delay_runs = self.config.value(base_key + ".delay-runs", 10),
            connection_retry_count = self.config.value(base_key + ".connection-retry-count", 5),
            connection_retry_interval = self.config.value(base_key + ".connection-retry-interval", 10),
            write_interval = self.config.value(base_key + ".write-interval", 0),
        )
        
        # base key for this writer's configuration
        #self.base_key="common.umcpush.{writer_id}.".format(writer_id=self.writer_id)

        # update any specific writer's param of this writer
        # update any value that may be overriden in writer's specific parameters
        wparams=self.param("writer-params")
        if wparams is not None:
            for k,v in wparams.items():
                k=k.replace("-", "_")
                # update only params that exist in common params
                if self.params.get(k) is not None:
                    self.params[k]=v
                else:
                    # this param may be used in child's configuration
                    pass        
    # // init
    
    # def param_key(self,param_name):
    #     return self.base_key + param_name
    
    def param(self, param_name, default=None):
         return self.config.value_element(self.writerDef, param_name, default)
            
    def read_umcdef(self, umc_id, umcconf):
        writers=self.config.value_element(umcconf, "writers", []);
        for writer in writers:
            if writer["writer-id"]==self.writer_id:
                return Map(enabled=self.config.value_element(writer, "enabled", True), writerDef=writer)

        # writer definition for this umc instance has not been found
        return Map(enabled=False, writerDef=None)
        
        # if self.config.value_element(umcconf, "writer." + self.writer_id, None) is None:
        #     return Map(enabled=False)
        # else:
        #     return Map(enabled=self.config.value_element(umcconf, "writer." + self.writer_id + ".enabled", True))
    # read_umcdef
                
