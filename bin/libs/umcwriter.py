
from utils import Map 

# creates an instance of the umc writer (a child of this class)
def create_instance(config, clazz):
    mc=clazz.split(".")
    if len(mc)!=2:
        raise Exception("The class definition '%s' is not in a required format \{module\}.\{classname\}!"%clazz)
        
    # instantiate the class
    try:
        class_ = getattr(__import__(mc[0]), mc[1])
        wobj=class_(config)
    except AttributeError as e:
        raise
        #raise Exception("The writer class %s cannot be found!"%clazz)
    except Exception as e:
        raise Exception("Error occured when creating an instance of the writer's class %s: %s"%(clazz,str(e)))
        
    # TODO: check wobj has required methods and fields and is a subclass of UmcWriter
    return wobj
# // create_instance

class UmcWriter(object):
    def __init__(self, config, writer_id):
        self.writer_id=writer_id
        self.config=config

        # read common writer's params
        base_key="common.umcpush.writer-params"
        self.params=Map(
            delay_writes = self.config.value(base_key + ".delay-writes", 200),
            delay_runs = self.config.value(base_key + ".delay-runs", 10000)/1000,
            connection_retry_count = self.config.value(base_key + ".connection-retry-count", 5),
            connection_retry_interval = self.config.value(base_key + ".connection-retry-interval", 10000)/1000,
        )

        # base key for this writer's configuration
        self.base_key="common.umcpush.{writer_id}.".format(writer_id=self.writer_id)

        # update any specific writer's param of this writer
        # update any value that may be overriden in writer's specific parameters
        wparams=self.config.value(self.base_key + "writer-params", default=None)
        if wparams is not None:
            for k,v in wparams.items():
                k=k.replace("-", "_")
                # update only params that exist in common params
                if self.params.get(k):
                    self.params[k]=v
                else:
                    # this param may be used in child's configuration
                    pass        
    # // init
    
    def param_key(self,param_name):
        return self.base_key + param_name
    
    def param(self, param_name, default=None):
         return self.config.value(self.param_key(param_name), default)
                
