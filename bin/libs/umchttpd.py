import os
import thread
import threading
import json
import socket
import re
import time
import requests
import datetime

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from threading import Event
from threading import RLock
from itertools import chain
from umctasks import RefreshProcessesTask
from umctasks import get_umc_instance_log_dir

# local libraries
import messages as Msg
import proc_utils as putils
from utils import Map
from utils import PathDef
from utils import tail
from time import sleep
from Queue import Queue 

allinstances_data = None
rlock_allhostsreq = threading.RLock() 

GlobalContext = None

# HTTPServer
class UmcRunnerHTTPServer():
        
    def __init__(self, globalCtx):
        global GlobalContext
        GlobalContext = globalCtx

        self.enabled = False
        self.thread = None
        
        if GlobalContext.params.http_enabled:
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
                self.response = requests.get(self.url,timeout=(GlobalContext.params.proxy_timeout_connect, 
                    GlobalContext.params.proxy_timeout_read), headers=headers)
            elif self.method=="post": 
                self.response = requests.post(self.url,timeout=(GlobalContext.params.proxy_timeout_connect, 
                    GlobalContext.params.proxy_timeout_read), headers=headers)
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
    
    def purge_cache(self):
        topurge=[]
        for url in self.data:
            d=self.data[url]
            if (not(d.lock._RLock__owner)) and (d.created_time is None or d.age is None or time.time()-d.created_time>d.age):
                topurge.append(url)
            # // if purge
        # // for
    
        # purge 
        for url in topurge:
            del self.data[url]
            Msg.info2_msg("The cache item %s has been purged from the cache."%url)
        
    # // purge_cache
    
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
        self.purge_cache()
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
    protocol_version='HTTP/1.1'
    timeout = 10
    
    # helper to format a message in json
    def msg(self, msg, code=200):
        return Map(code=code, json=["{ \"msg\" : \"%s\" }"%msg])
    
    # helper to send response back to the client
    def send(self, code, headers=None, data=None):
        self.send_response(code)
        if headers is not None:
            for k,v in headers.items():
                self.send_header(k, v)
        self.send_header('Content-Length', len(data))
        self.send_header('Connection', 'keep-alive')
        self.end_headers()
        if data is not None:
            self.wfile.write(data)
            self.wfile.write('\n')        
    
    def get_server_list(self, params):
        server_list=[]
        for hostname,server_def in GlobalContext.server_list.items():
            if server_def.enabled:
                if params.params.hostname=='all' or hostname.startswith(params.params.hostname):
                    server_list.append(server_def)
        return server_list
    # get_server_list
    
    def read(self):
        request_headers = self.headers
        content_length = request_headers.getheaders('content-length')
        length = int(content_length[0]) if content_length else 0
        return self.rfile.read(length)
    # read 
    
    # process request in the umcrunner cluster in the following way:
    # if path_def contains {hostname} and its value is 'all', then proxy the request to all umcrunner servers in the cluster; 
    # otherwise redirect the request to respctive hostname; if the hostname is this umcrunner instance, then process the request here
    # the functiona always returns an array of json formatted objects
    def process_cluster_request(self, method, path_def, allow_all, cache_maxage, is_stream, get_content):
        params=PathDef(path_def).params(self.path) #get_path_params(path_def, self.path)
        
        # path must be a valid path and hostname param must exist in it
        if params is None or params.params.hostname is None:
            return None
        
        # get a list of servers this should be proxied to
        # if there is more than one, then proxy them, otherwise run the locally or redirect via client
        server_list = self.get_server_list(params)
        
        # hostname is "all", will forward to individual umcrunner servers
        if len(server_list) > 1 and allow_all:
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
                        Msg.info2_msg("Sending %d proxy requests."%(len(server_list)))
                        
                        start_t=time.time(); prqs=[]                    
                        for server_def in server_list:
                            prqs.append(ProxyRequest(method,'http://{address}:{tcp_port}{fw_path}'
                                .format(address=server_def.address,tcp_port=server_def.tcp_port,
                                fw_path=params.replace(params,Map(hostname=server_def["hostname"]))),
                                GlobalContext.params.proxy_run_threads))
                            prqs[-1].send_request()

                        # wait for all responses
                        for x in prqs: x.wait_for_response()
                        
                        # get all "valid" responses
                        resp = [ r for r in prqs if r.response is not None ]
                        Msg.info2_msg("Data from %d proxy requests retrieved in %.2f seconds."%(len(resp),time.time()-start_t))                                   
                        
                        # add result to cache; the result from individual servers should always be json array                    
                        content = Map(content="[%s]"%",".join([ r.response.text.strip()[1:-1] for r in resp if r.response.text.strip()!= "[]" ]))                        
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
        # // if multiple hostnames        
        elif len(server_list)==1:
            # params.params.hostname should be a valid hostname
            server_def = server_list[0]
            if not(server_def.me):
                # host should be a known host, redirect the request onto it rather than being a proxy
                location_url="http://{address}:{tcp_port}{fw_path}".format(address=server_def.address,tcp_port=server_def.tcp_port,
                    fw_path=params.replace(params,Map(hostname=server_def["hostname"])))
                Msg.info2_msg("Redirecting the request to '%s'"%location_url)                
                self.send(308, { "Location" : location_url }, "")
                return
            else:
                if not(is_stream):
                    content = get_content(params)
                    if content is not None:
                        self.send(content.code, { "Content-Type" : "application/json" }, "[%s]"%",".join(content.json) )
                    else:
                        # should not happen really
                        self.send(500, None, "" )
                    return True
                else:
                    get_content(params)
                    return True
        # // if one hostname only
        else:
            self.send(404, None, "The host '%s' cannot be found or is not allowed!"%params.params.hostname)
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
                if not(ud.get("errorlog")):
                    sl_def = GlobalContext.server_list.get(socket.gethostname())
                    if sl_def is not None and sl_def.address is not None and sl_def.tcp_port is not None and sl_def.me:
                        ud["link_errorlog"]="/logs/error/hosts/{hostname}/umc/{umc_instance}".format(address=sl_def.address,tcp_port=sl_def.tcp_port,hostname=ud.hostname,umc_instance=ud.umc_instanceid)
                
                if params.params.umc=='all' or ud.umc_instanceid.startswith(params.params.umc): 
                    content.json.append(ud.to_json(CustomEncoder,exclude=['proc','options','lock']))
            finally:
                ud.lock.release()
        return content

    # callback to retrieve error log content 
    def callback_umc_errorlog(self, params):
        content=Map(code=200, json=[])
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                if ud.umc_instanceid.startswith(params.params.umc):
                    errorlog="%s/%s.error.out"%(get_umc_instance_log_dir(ud.umc_instanceid,GlobalContext),ud.umc_instanceid)
                    if os.path.exists(errorlog):
                        content.json.append(json.dumps({ "umc_instanceid" : ud.umc_instanceid, "rows": tail(errorlog, 10) }))
                # // if umc id 
            finally:
                ud.lock.release()
        return content
    
    # callback to terminate umc instance
    def callback_umc_terminate(self,params):
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                if ud.umc_instanceid==params.params.umc_instance:
                    if ud.proc is not None:
                        putils.terminate_process_children(ud.proc)
                        RefreshProcessesTask().refresh_single_instance(ud, GlobalContext)
                        return self.msg("%s: umc instance id '%s' was terminated."%(params.params.hostname, ud.umc_instanceid)) 
                    else:
                        return self.msg("%s: umc instance id '%s' is not running."%(params.params.hostname, ud.umc_instanceid)) 
            finally:
                ud.lock.release()
        return self.msg("%s: umc instance id '%s' not found."%(params.params.hostname, params.params.umc_instance), code=404)

    # callback to disable umc instance
    def callback_umc_disable(self,params):
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                if ud.umc_instanceid==params.params.umc_instance:
                    if ud.enabled: 
                        ud.enabled = False
                        self.callback_umc_terminate(params)
                        return self.msg("%s: umc instance id '%s' was disabled."%(params.params.hostname, ud.umc_instanceid)) 
                    else:
                        return self.msg("%s: umc instance id '%s' is already disabled."%(params.params.hostname, ud.umc_instanceid))                         
            finally:
                ud.lock.release()
        return self.msg("%s: umc instance id '%s' not found."%(params.params.hostname, params.params.umc_instance), code=404)

    # callback to enable umc instance
    def callback_umc_enable(self,params):
        for ud in GlobalContext.umcdefs:
            ud.lock.acquire()
            try:
                if ud.umc_instanceid==params.params.umc_instance:
                    if not(ud.enabled):
                        ud.enabled = True
                        return self.msg("%s: umc instance id '%s' was enabled."%(params.params.hostname, ud.umc_instanceid)) 
                    else:
                        return self.msg("%s: umc instance id '%s' is already enabled."%(params.params.hostname, ud.umc_instanceid)) 
            finally:
                ud.lock.release()
        return self.msg("%s: umc instance id '%s' not found."%(params.params.hostname, params.params.umc_instance), code=404)
    
    # callback to stop umcrunner
    def callback_stop(self,params):
        GlobalContext.exitEvent.set()
        return self.msg("%s: umcrunner exit event set."%(params.params.hostname), code=202)

    # callback to stop umcrunner
    # def callback_updatesettings(self,params):
    #     try:
    #         data=json.loads(self.read())
    #         if (data.get("verbose") is not None and (data["verbose"]==True or data["verbose"]==False)):
    #             mode=Msg.verbose_mode(data["verbose"])
    #             return self.msg("%s: verbose mode is %s."%(params.params.hostname,mode), code=202)
    #         else:
    #             raise Exception("Invalid settings data!")
    #     except Exception as e:
    #         self.send_error(400, str(e))
    # callback_updatesettings
    
    # callback to stop umcrunner
    def callback_logstream(self,params):
        q=Queue()
        Msg.subscribe(q)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no") # turn off buffering on nginx proxy servers for this request
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            started=time.time()
            
            # run for 120 seconds
            # the SSE client should reconnect automatically
            while time.time()-started<120:
              try:
                data=q.get()
                if (data is not None):
                    self.wfile.write("data: %s\n\n"%json.dumps(data))
                    q.task_done()
                else:
                  sleep(0.5)
              except Exception as e:
                pass
        finally:
            Msg.unsubscribe(q)
            del q        
    
    # *** HTTP methods handlers
    # reading data
    def do_GET(self):
        # umcrunner stats
        if self.process_cluster_request("get", "/stats/hosts/{hostname}", True,
            GlobalContext.params.logstats_interval, False,
            lambda params : Map(code=200, json=[ GlobalContext.umcrunner_stats.to_json() ] )) is not None:
            return

        # umc stats
        if self.process_cluster_request("get", "/stats/hosts/{hostname}/umc/{umc}", True,
            GlobalContext.params.logstats_interval, False,
            self.callback_umcdef_content) is not None:
            return

        # umc error log
        if self.process_cluster_request("get", "/logs/error/hosts/{hostname}/umc/{umc}", False,
            GlobalContext.params.logstats_interval, False,
            self.callback_umc_errorlog) is not None:
            return
            
        # messages log steam (server-sent events)
        if self.process_cluster_request("get", "/logs/stream/hosts/{hostname}", False, 0, True, self.callback_logstream) is not None:
            return
            
        # others are not found 
        self.send_response(404)

    # modifications
    def do_POST(self):
        # terminate umc instance
        if self.process_cluster_request("post", "/terminate/hosts/{hostname}/umc/{umc_instance}", True, 0, False,
            self.callback_umc_terminate) is not None:            
            return

        # disable umc instance
        if self.process_cluster_request("post", "/disable/hosts/{hostname}/umc/{umc_instance}", True, 0, False,
            self.callback_umc_disable) is not None:            
            return

        # enable umc instance
        if self.process_cluster_request("post", "/enable/hosts/{hostname}/umc/{umc_instance}", True, 0, False,
            self.callback_umc_enable) is not None:            
            return
            
        # enable umc instance
        if self.process_cluster_request("post", "/stop/hosts/{hostname}", True, 0, False,
            self.callback_stop) is not None:            
            return

        # others are not found 
        self.send_response(404)

    # def do_PUT(self):
    #     # update settings
    #     if self.process_cluster_request("put", "/settings/hosts/{hostname}", False, 0, False, 
    #         self.callback_updatesettings) is not None:            
    #         return
    # 
    #     # others are not found 
    #     self.send_response(404)
                    
    def log_request(self, size):
        Msg.info2_msg('HTTP request from (%s) %s %s'%(self.address_string(), self.requestline, str(size)))

    # def handle_one_request(self):
    #     #try:
    #     BaseHTTPRequestHandler.__init__(self, Handler).handle_one_request()
    #     #except:
    #     #    print "*** handle request error!"
        
# threaded HTTP server, this is required due to connections that may be reused in chrome
# hence requests coming from other clients would get blocked
# this is a similar solution provided by a fix here: https://bugs.python.org/issue31639
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True


        
        
