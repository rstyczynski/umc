import os
import time
import subprocess
import re
import psutil
import socket
import ctypes

from time import sleep

from utils import Map
import messages as Msg
    
# the main umcrunner run task that runs umc instances according to the configuration
class UmcRunTask():
    UMCRUNNER_SIGNATURE="umcrunner-AF453BD"
    UMC_LAUNCH_CMD="echo \"{signature}\" &>/dev/null; source {umc_home}/umc.h &>/dev/null; set -o pipefail; umc {umc_toolid} collect {delay} {count} {params} 2>>{log_dir}/{umc_toolid}.error.out </dev/null | logdirector.pl -name {umc_toolid} -dir {log_dir} -detectHeader -checkHeaderDups -rotateByTime run -timeLimit {rotation_timelimit} -flush -timeRotationInThread -rotateOnThreadEnd"
    DEFAULT_SHELL="/bin/bash"
    
    def get_log_dir(self, umc_toolid, GlobalContext):
        return "{log_root_dir}/{hostname}/{umc_toolid}".format(log_root_dir=GlobalContext.logRootDir,hostname=socket.gethostname(),umc_toolid=umc_toolid)
    
    # run umc instance
    def run_umc(self,umcdef,GlobalContext): # umc_instanceid,umc_toolid,delay,count,params,rotation_timelimit):
        # create log directory for this tool if it does not exist
        log_dir=self.get_log_dir(umcdef.umc_toolid, GlobalContext)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # tell what we are doing    
        Msg.info1_msg("Starting umc instance id '{umc_instanceid}': umc='{umc_toolid}', delay={delay}, count={count}, params='{params}', rotation_timelimit={rotation_timelimit}, log_dir='{log_dir}'".
            format(umc_instanceid=umcdef.umc_instanceid,umc_toolid=umcdef.umc_toolid,delay=umcdef.delay,count=umcdef.count,params=umcdef.params,
                rotation_timelimit=umcdef.rotation_timelimit,log_dir=umcdef.log_dir))

        # it is important to set setsid as there might be child processes that use tty, this should provide a dedicated tty for them
        # example of such process is sqlcl
        preexec=None
        if "setsid" in umcdef.options:
            preexec=ctypes.CDLL('libc.so.6').setsid
            
        p = psutil.Popen(UmcRunTask.UMC_LAUNCH_CMD.format(umc_toolid=umcdef.umc_toolid,delay=umcdef.delay,count=umcdef.count,params=umcdef.params,rotation_timelimit=umcdef.rotation_timelimit,
                signature=UmcRunTask.UMCRUNNER_SIGNATURE,umc_home=GlobalContext.homeDir,log_dir=log_dir), 
            shell=True, executable=UmcRunTask.DEFAULT_SHELL, preexec_fn=preexec, stdin=None, stdout=None, stderr=None)
        
        return p
    
    def run_task(self, GlobalContext):
        running=[]; started=[]; waiting=[]
        for umcdef in GlobalContext.umcdefs:
            umcdef.lock.acquire()
            try:
                if umcdef.proc is None and time.time()>umcdef.start_after:
                    if umcdef.last_started_time is not None and time.time()-umcdef.last_started_time < GlobalContext.config.umcrunner_params.min_starting_time:
                        Msg.warn_msg("umc instance id '%s' starting frequency is too high (<%d seconds), will not start it now!"
                            %(umcdef.umc_instanceid,GlobalContext.config.umcrunner_params.min_starting_time))
                        waiting.append("%s, WT=%.2fs"%(umcdef.umc_instanceid,GlobalContext.config.umcrunner_params.min_starting_time))                        
                    else:
                        try:
                            # run umcinstance as a child process
                            umcdef.proc = self.run_umc(umcdef, GlobalContext)
                            
                            # start time
                            start_t=time.time()
                            umcdef.start_after=0
                            umcdef.last_started_time=start_t
                            umcdef.num_runs = umcdef.num_runs + 1
                            if umcdef.first_started_time == 0:
                                umcdef.first_started_time = time.time()
                            
                            started.append("%s, PID=%d"%(umcdef.umc_instanceid,umcdef.proc.pid))
                        except Exception as e:
                            Msg.warn_msg("Error occurred while starting umc instance %s. The exception was: %s"%(umcdef.umc_instanceid, str(e)))
                            pass
                else:
                    if umcdef.proc is not None: 
                        running.append("%s, PID=%d"%(umcdef.umc_instanceid,umcdef.proc.pid))
                    else: 
                        waiting.append("%s, WT=%.2fs"%(umcdef.umc_instanceid,umcdef.start_after-time.time()))
            finally:
                umcdef.lock.release()
        # for

        time_run = time.time()
        Msg.info2_msg("Running: %s"%(running))                
        Msg.info2_msg("Started: %s"%(started))                
        Msg.info2_msg("Waiting: %s"%(waiting))                
    
class RefreshProcessesTask():

    def refresh_single_instance(self, umcdef, GlobalContext):
        umcdef.lock.acquire()
        try:
            if umcdef.proc is not None:
                try:
                    # update the process return code if any
                    if umcdef.proc is not None:
                        umcdef.proc.poll()
                        if not(umcdef.proc.is_running()) and umcdef.proc.returncode is not None:
                            rc=umcdef.proc.returncode
                            if rc != 0:
                                Msg.warn_msg("umc instance %s failed/terminated with exit code %d. Will attempt to restart it after %d seconds."
                                    %(umcdef.umc_instanceid,rc,60))
                                umcdef.start_after=time.time()+60
                                umcdef.num_errors = umcdef.num_errors + 1
                                umcdef.lasterror_time = time.time()
                            umcdef.returncodes.insert(0,(time.time(), rc))
                            if len(umcdef.returncodes)>GlobalContext.config.umcrunner_params.retc_history:
                                del umcdef.returncodes[-(len(umcdef.returncodes)-GlobalContext.config.umcrunner_params.retc_history):]
                        
                    # clear the process is not runnig or check the process is zombie; this happens when the process ends normally but we still hold a refernece to it
                    if not(umcdef.proc.is_running()) or (umcdef.proc.is_running() and umcdef.proc.status() == psutil.STATUS_ZOMBIE):   
                        umcdef.proc=None
                        sleep(0.1)
                    
                except Exception as e:
                    Msg.warn_msg("There was a problem when quering the process with pid %d: %s"%(umcdef.proc.pid,str(e)))
                    if e.__class__ == psutil.NoSuchProcess:
                        umcdef.proc=None
                    pass
        finally:
            umcdef.lock.release()
    
    def run_task(self, GlobalContext):
        for umcdef in GlobalContext.umcdefs:
            self.refresh_single_instance(umcdef, GlobalContext)
        return True
    
# stats collection
class CollectStatsTask():    
    
    # def backlog(umc_toolid, max_files):
    #     log_dir=get_log_dir(umc_toolid)
    # 
    #     count = 0
    # 
    #     try:
    #         str='ls -U1 {log_dir}/ 2>/dev/null | grep "{umc_toolid}_" 2>/dev/null | head -{max_files} 2>/dev/null | wc -l'.format(log_dir=log_dir,umc_toolid=umc_toolid,max_files=max_files+1)
    #         cmd=subprocess.Popen(str, shell=True, stdout=subprocess.PIPE)
    #         for e in cmd.stdout:
    #             count = int(e)
    #             break
    #     except Exception as e:
    #         count = 0
    #         print str(e)
    #         pass
    # 
    #     '''    
    #     pattern="{umc_toolid}_.+".format(umc_toolid=umc_toolid)
    #     for f in os.listdir(log_dir):
    #         if f.find(pattern):
    #             count = count + 1
    #         if count > max_files:
    #             break
    #     '''
    # 
    #     return count
    
    def run_task(self, GlobalContext):
        if GlobalContext.umcdefs is not None:
            start_t=time.time();
            for ud in GlobalContext.umcdefs:
                ud.lock.acquire()
                try:
                    stats = {}; 
                    
                    # backlog
                    max_files=5
                    bg = 0 #backlog(ud.umc_toolid, max_files)
                    stats["backlog"] = ">%d"%max_files if bg > max_files else str(bg) 
                    
                    # process info
                    p = {}
                    try:
                        if ud.proc is not None:
                            p["top_pid"] = ud.proc.pid
                            p["uptime"] = time.time() - ud.proc.create_time()
                            
                            kids = ud.proc.children(True)
                            rss = 0.0; cpu = 0
                            for k in kids:
                                d = k.as_dict(attrs=['cpu_times', 'memory_info'])
                                cpu = cpu + d["cpu_times"].user
                                rss = rss + d["memory_info"].rss

                            p["rss"] = float(rss/1024/1024) # in MB
                            p["cpu"] = cpu   
                            p["num_chproc"] = len(kids)             
                            
                        # end if
                    except:
                        pass
                    
                    stats["p"] = p
                    ud.stats = stats        
                finally:
                    ud.lock.release()
            # for            
            Msg.info2_msg("Stats collected in %.2f seconds"%(time.time()-start_t))
            return True
        # if umcdefs

# checks if there are sub-processes that are "orphans", i.e. they do not have a parent process
# which was started by umcrunner. This will happen if someone externally kill this umcrunner started process.  
class OrphansCheckTask():    
    
    # retrieves all pids and their pgid from os
    def get_all_pgids(self):
        pgids={}
        cmd=subprocess.Popen('ps ax -o pid,pgid', shell=True, stdout=subprocess.PIPE)
        for e in cmd.stdout:
            m = re.match(r"^[ ]*([0-9]+)[ ]+([0-9]+)[ ]*$", e) 
            if m:
                pid = int(m.group(1))
                pgid = m.group(2)            
                if pgid not in pgids:
                    pgids[pgid] = []
                if pid != os.getpid():
                    pgids[pgid].append(pid)
        return pgids
    # get_all_pgids
    
    def run_task(self, GlobalContext):
        orphans = []
        pids = self.get_all_pgids()[str(os.getpgrp())]
        procs = psutil.Process().children(recursive=True)
        
        for pid in pids:
            try:
                os.kill(int(pid), 0)
            except OSError:
                # we are not so fast, the process ended in the meantime 
                pass
            else:
                # the process is live; check it exist in process tree
                found = False
                for p in procs:
                    if p.pid == pid:
                        found = True
                        break
                
                if not found:
                    orphans.append(pid)
            # else
        # for pid

        # pause if there are orhpans
        if len(orphans)>0:
            Msg.warn_msg("There are %d orphan processes, will pause umcrunner until orhpans exist!"%(len(orphans)))
            Msg.info2_msg("The orhpans are: %s"%orphans)
            return False
        else:
            return True
# OrphansCheckTask

# check for the maximum number of processes that umcrunner can spawn
class MaxProcessesTask():
    def run_task(self, GlobalContext):
        kids=psutil.Process().children(True)

        Msg.info2_msg("There are %d children processes."%(len(kids)))
            
        if len(kids) > GlobalContext.config.umcrunner_params.max_processes:
            Msg.warn_msg("(%s) The current number of child processes %d exceeds the maximum of %d. umcrunner will be paused."%(self.__class__.__name__,len(kids),GlobalContext.config.umcrunner_params.max_processes))
            return False
        else:
            return True    

# check for maximum number of zombie processes that cannot exceed the maximum number of umcrunner instances
class MaxZombiesTask():
    def run_task(self, GlobalContext):
        kids=psutil.Process().children(True)
        
        nz = 0
        for p in kids:
            try:
                if p.status() == psutil.STATUS_ZOMBIE:
                    nz = nz + 1
            except Exception as e:
                pass

        Msg.info2_msg("There are %d zombie processes"%(nz))

        if nz > len(GlobalContext.umcdefs):
            Msg.warn_msg("There are %d zombie processes which exceeds the number of umc instances %d. Will pause umc runner until the zombie processes will disappear!"%
                (nz,len(GlobalContext.umcdefs)))
            return False
        else:
            return True        

# *** main class definition
class TasksDef():
        
    def __init__(self, global_ctx):
        self.GlobalContext = global_ctx
        self.tasks = []
        
    def addTask(self, targetClass, time_interval, run_on_pause=False):
        taskdef=Map(last_time=0, time_interval=time_interval, target=targetClass(), run_on_pause=run_on_pause, result=True)
        self.tasks.append(taskdef)
        return taskdef
        
    def run_all(self):
        paused = self.GlobalContext.paused
        for t in self.tasks:
            if time.time()-t.last_time > t.time_interval and (t.run_on_pause or not(paused)):
                t.result = t.target.run_task(self.GlobalContext)
                if not(t.result):
                    paused = True
                t.last_time = time.time()
            else:
                pass

        old_paused = self.GlobalContext.paused
        self.GlobalContext.paused = not(all([ t.result for t in self.tasks if t.result is not None ]))

        if self.GlobalContext.paused != old_paused:
            Msg.warn_msg("umcrunner state has been %s."%("PAUSED" if self.GlobalContext.paused else "RESUMED"))


