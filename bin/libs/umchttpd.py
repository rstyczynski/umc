import thread
import threading
import json
import socket
import re
import time
import requests

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from threading import Event
from threading import RLock
from itertools import chain
from umctasks import RefreshProcessesTask

# local libraries
import messages as Msg
import proc_utils as putils
from utils import Map

allinstances_data = None
rlock_allhostsreq = threading.RLock() 

GlobalContext = None

class PathDef():
    def __init__(self, path_def):
        self.path_def=path_def

    def params(self, path):
        path_re=self.path_def
        
        # find all params in path_def
        params_def=re.findall("(\{[a-zA-Z0-9_]+\})", self.path_def)
        
        # create re pattern by replacing parameters in path_def with pattern to match parameter values
        for p_def in params_def: path_re=path_re.replace(p_def, "([a-zA-Z\-0-9\._]+)")
        
        # get params values
        res=re.findall("^" + path_re + "$", path)
        values=[]
        for x in res:
            if type(x) is tuple: values.extend(list(x))
            else: values.append(x)
        
        params=Map()
        params.__path_def__=self.path_def
        params.__path__=path
        params.replace = self.replace
        for x in range(0, len(params_def)):
            if x < len(values): params[params_def[x][1:-1]]=str(values[x])
            else:
                Msg.warn_msg("The path '%s' does not match definition '%s'"%(path, self.path_def))
                return None
        
        return params
    
    def replace(paramsMap, path):
        params = self.params(path)
        if params is None:
            return None

        new_path=self.path_def
        for k,v in paramsMap:
            if params.get(k):
                new_path = new_path.replace("{%s}"%k,v)
            else:
                Msg.warn_msg("The param '%s' has not been found in path definition '%s'."%(k, self.path_def))
        
        return new_path

# HTTPServer
class UmcRunnerHTTPServer():
        
    def __init__(self, globalCtx):
        global GlobalContext
        GlobalContext = globalCtx

        self.enabled = False
        self.thread = None
        
        if GlobalContext.config.umcrunner_params.http_enabled:
            sl_def = GlobalContext.server_list.get(socket.gethostname())
            if sl_def is not None and sl_def.address is not None and sl_def.tcp_port is not None and sl_def.me:
                self.enabled = True
                self.address = sl_def.address
                self.tcp_port = sl_def.tcp_port 
            else:
                Msg.warn_msg("Cannot determine umcrunner's address and/or tcp_port for http server to bind to. The http server will not be started!")                
        else:
            Msg.info1_msg("HTTP server is disabled.")    
        
    def __run_httpd(self):
        # start the server
        Msg.info1_msg("Starting http server on at %s:%s."%(self.address,self.tcp_port))
        try:
            self.exit = Event()
            self.httpd = ThreadedHTTPServer((self.address, int(self.tcp_port)), Handler, bind_and_activate=False)        
            self.httpd.allow_reuse_address = True
            self.httpd.timeout = 1
            self.httpd.server_bind()
            self.httpd.server_activate()
        except Exception as e:
            Msg.warn_msg("Cannot start HTTP server due to: %s."%(str(e)))
            return
        
        # serve the requests
        try:
            while not(self.exit.is_set()):
                self.httpd.handle_request()
        finally:
            Msg.info1_msg("Closing HTTP server.")
            try:
                self.httpd.server_close()
            except Exception as e:
                Msg.warn_msg("Error occurred while closing the HTTP server: %s"%(str(e)))
    # __run_httpd    

    def start_httpd(self):
        if self.enabled:
            self.thread=threading.Thread(target=self.__run_httpd)
            self.thread.start()
    # start_httpd
    
    def stop_httpd(self):
        if self.thread is not None:
            self.exit.set()
            self.thread.join()
    # stop_httpd


# *** proxy request class
class ProxyRequest():
    def __init__(self, method, url, in_thread=True):
        self.method = method
        self.url = url
        self.response = None
        self.in_thread = in_thread
        if self.in_thread:
            self.thread=threading.Thread(target=self.__send_request)
        
    def __send_request(self):
        try:
            Msg.info2_msg("Sending proxy request %s %s"%(self.method.upper(),self.url))
            headers={ "Via" : "1.1 %s"%socket.gethostname() }
            if self.method=="get": 
                self.response = requests.get(self.url,timeout=(GlobalContext.config.umcrunner_params.proxy_timeout_connect, 
                    GlobalContext.config.umcrunner_params.proxy_timeout_read), headers=headers)
            elif self.method=="post": 
                self.response = requests.post(self.url,timeout=(GlobalContext.config.umcrunner_params.proxy_timeout_connect, 
                    GlobalContext.config.umcrunner_params.proxy_timeout_read), headers=headers)
            else: 
                raise Exception("Method %s is not supported!"%self.method)
        except Exception as e:
            Msg.warn_msg("Proxy request to %s failed: %s"%(self.url,str(e)))
            pass
    # end send request    

    def send_request(self):
        if self.in_thread:
            self.thread.start()
        else:
            self.__send_request()
        
    def wait_for_response(self):
        if self.in_thread:
            self.thread.join()    

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # do not encode psutil.Popen process
        if isinstance(obj, psutil.Popen):
            return None
        else:
            return json.JSONEncoder.default(self, obj)

class HTTPCache():
    """HTTP cache for proxy requests"""
    
    def __init__(self):
        self.data = {}        
    
    def create_data(self,url, content, created_time, age):
        if self.data.get(url) is None:
            self.data[url] = Map()
        
        self.data[url].content=content 
        self.data[url].created_time=created_time
        self.data[url].age=age
        if self.data[url].lock is None: 
            self.data[url].lock=RLock()
        
        return self.data[url]
    # create_data    
    
    def acquire_lock(self,url):
        if self.data.get(url) is None:
            self.create_data(url, None, None, None)
        self.data[url].lock.acquire()
    # acquire_lock
    
    def release_lock(self,url):
        if self.data.get(url) is not None and self.data[url].lock is not None:
            self.data[url].lock.release()
    # release_lock
    
    def get(self,url):
        d=self.data.get(url)
        if d is not None and d.created_time is not None and d.age is not None and time.time()-d.created_time<=d.age:
            return d
        else:
            return None
    # get

# global cache
cache = HTTPCache()                
                
# *** http server class for api requests 
class Handler(BaseHTTPRequestHandler):
    server_version = "umcrunner, BaseHTTP/0.3, Python/2.7.11"    
    
    # helper to format a message in json
    def msg(self, msg, code=200):
        return Map(code=code, json=["{ \"msg\" : \"%s\" }"%msg])
    
    # helper to send response back to the client
    def send(self, code, headers=None, data=None):
        self.send_response(code)
        if headers is not None:
            for k,v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        if data is not None:
            self.wfile.write(data)
            self.wfile.write('\n')        
    
    # process request in the umcrunner cluster in the following way:
    # if path_def contains {hostname} and its value is 'all', then proxy the request to all umcrunner servers in the cluster; 
    # otherwise redirect the request to respctive hostname; if the hostname is this umcrunner instance, then process the request here
    # the functiona always returns an array of json formatted objects
    def process_cluster_request(self, method, path_def, cache_maxage, get_content):
        params=PathDef(path_def).params(self.path) #get_path_params(path_def, self.path)
        
        # path must be a valid path and hostname param must exist in it
        if params is None or params.hostname is None:
            return None
        
        # hostname is "all", will forward to individual umcrunner servers
        if params.hostname=="all":
            # check if this has been proxied already
            if self.headers.get("Via") is None:
                # acquire lock on this path to prevent other threads from doing the same
                cache.acquire_lock(self.path)
                try:
                    # check if in cache 
                    content = cache.get(self.path)
                    if content is None:       
                        # not in cache              
                        # proxy to all umcrunner hosts including "me" (this one)
                        Msg.info2_msg("Sending %d proxy requests."%(len(GlobalContext.server_list.items())))
                        
                        start_t=time.time(); prqs=[]                    
                        for hostname,server_def in GlobalContext.server_list.items():
                            if server_def.enabled:
                                prqs.append(ProxyRequest(method,'http://{address}:{tcp_port}{fw_path}'
                                    .format(address=server_def.address,tcp_port=server_def.tcp_port,fw_path=self.path.replace("all", hostname)),
                                    GlobalContext.config.umcrunner_params.proxy_run_threads))
                                prqs[-1].send_request()

                        # wait for all responses
                        for x in prqs: x.wait_for_response()
                        
                        # get all "valid" responses
                        resp = [ r for r in prqs if r.response is not None ]
                        Msg.info2_msg("Data from %d proxy requests retrieved in %.2f seconds."%(len(resp),time.time()-start_t))                                   
                        
                        # add result to cache; the result from individual servers should always be json array                    
                        content = Map(content="[%s]"%",".join([ r.response.text.strip()[1:-1] for r in resp ]))
                        if cache_maxage > 0:
                            cache.create_data(self.path, content.content, time.time(), cache_maxage) 
                    # if not in cache
                    else:
                        Msg.info2_msg("Serving request for %s from cache."%self.path)
                    
                    # send back response
                    self.send(200, { "Content-Type" : "application/json" }, content.content )
                finally:
                    cache.release_lock(self.path)
                return True
            # if not via
            else:
                Msg.warn_msg("A request to %s can only come from a client, not a proxy! (%s)"%(self.path,self.headers.get("Via"))) 
                self.send(400, None, "Request to the resource that comes via a proxy is not allowed!")
                return False              
        # if hostname=="all"
        else:
            # params.hostname should be a valid hostname
            server_def = GlobalContext.server_list.get(params.hostname)
            if server_def is not None:
                if not(server_def.me):
                    # host should be a known host, redirect the request onto it rather than being a proxy
                    self.send(308, { "Location" : "http://{address}:{tcp_port}{fw_path}"
                        .format(address=server_def.address,tcp_port=server_def.tcp_port,fw_path=self.path.replace("all", params.hostname)) }, "")
                    return
                else:
                    content = get_content(params)
                    if content is not None:
                        self.send(content.code, { "Content-Type" : "application/json" }, "[%s]"%",".join(content.json) )
                    else:
                        # should not happen really
                        self.send(500, None, "" )
                    return True
            else:
                self.send(404, None, "The host %s does not exist!"%params.hostname)
                return False
        # else 
    # process_cluster_request       

    # *** callbacks used for process_cluster_requests
    # callback to retrieve all umcdefs content 
    def callback_umcdef_content(self, params):
        content=Map(code=200, json=[])
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                content.json.append(ud.to_json(CustomEncoder,exclude=['proc','options','lock']))
            finally:
                ud.lock.release()
        return content
    
    # callback to terminate umc instance
    def callback_umc_terminate(self,params):
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                if ud.umc_instanceid==params.umc_instance:
                    if ud.proc is not None:
                        putils.terminate_process_children(ud.proc)
                        RefreshProcessesTask().refresh_single_instance(ud, GlobalContext)
                        return self.msg("%s: umc instance id '%s' was terminated."%(params.hostname, ud.umc_instanceid)) 
                    else:
                        return self.msg("%s: umc instance id '%s' is not running."%(params.hostname, ud.umc_instanceid)) 
            finally:
                ud.lock.release()
        return self.msg("%s: umc instance id '%s' not found."%(params.hostname, params.umc_instance), code=404)

    # callback to disable umc instance
    def callback_umc_disable(self,params):
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                if ud.enabled and ud.umc_instanceid==params.umc_instance:
                    ud.enabled = False
                    self.callback_umc_terminate(params)
                    return self.msg("%s: umc instance id '%s' was disabled."%(params.hostname, ud.umc_instanceid)) 
            finally:
                ud.lock.release()
        return self.msg("%s: umc instance id '%s' not found."%(params.hostname, params.umc_instance), code=404)

    # callback to enable umc instance
    def callback_umc_enable(self,params):
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                if not(ud.enabled) and ud.umc_instanceid==params.umc_instance:
                    ud.enabled = True
                    return self.msg("%s: umc instance id '%s' was enabled."%(params.hostname, ud.umc_instanceid)) 
            finally:
                ud.lock.release()
        return self.msg("%s: umc instance id '%s' not found."%(params.hostname, params.umc_instance), code=404)
    
    # *** HTTP methods handlers
    # reading data
    def do_GET(self):
        # umcrunner stats
        if self.process_cluster_request("get", "/stats/hosts/{hostname}", 
            GlobalContext.config.umcrunner_params.stats_interval, 
            lambda params : Map(code=200, json=[ GlobalContext.umcrunner_stats.to_json() ] )) is not None:
            return

        # all umc stats
        if self.process_cluster_request("get", "/stats/hosts/{hostname}/umc", 
            GlobalContext.config.umcrunner_params.stats_interval, 
            self.callback_umcdef_content) is not None:
            return
            
        # others are not found 
        self.send_response(404)

    # modifications
    def do_POST(self):
        # terminate umc instance
        if self.process_cluster_request("post", "/terminate/hosts/{hostname}/umc/{umc_instance}", 0, 
            self.callback_umc_terminate) is not None:            
            return

        # disable umc instance
        if self.process_cluster_request("post", "/disable/hosts/{hostname}/umc/{umc_instance}", 0, 
            self.callback_umc_disable) is not None:            
            return

        # enable umc instance
        if self.process_cluster_request("post", "/enable/hosts/{hostname}/umc/{umc_instance}", 0, 
            self.callback_umc_enable) is not None:            
            return
            
        # others are not found 
        self.send_response(404)
        
        #if self.path == "/stopall":
        #    GlobalContext.exitEvent.set()
        #    self.send(202) # accepted
        #    return        
 
    def log_request(self, size):
        Msg.info2_msg('HTTP request from (%s) %s %s'%(self.address_string(), self.requestline, str(size)))

# threaded HTTP server, this is required due to connections that may be reused in chrome
# hence requests coming from other clients would get blocked
# this is a similar solution provided by a fix here: https://bugs.python.org/issue31639
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True


        
        
