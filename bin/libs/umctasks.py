import os
import time
import subprocess
import re
import psutil
import socket
import ctypes
import utils

from time import sleep

from utils import Map
import messages as Msg
from scandir import scandir

def get_umc_instance_log_dir(umc_instanceid, GlobalContext):
    return "{log_root_dir}/{hostname}/{umc_instanceid}".format(log_root_dir=GlobalContext.config.logDir,hostname=socket.gethostname(),umc_instanceid=umc_instanceid)

# the main umcrunner run task that runs umc instances according to the configuration
class UmcRunTask():
    UMC_LAUNCH_CMD="source {umc_home}/umc.h &>/dev/null; set -o pipefail; umc {umc_toolid} collect {delay} {count} {params} 2>>{log_dir}/{umc_instanceid}.error.out </dev/null | logdirector.pl -name {umc_instanceid} -dir {log_dir} -detectHeader -checkHeaderDups -rotateByTime run -timeLimit {rotation_timelimit} -logFileGroups {log_file_groups} -flush -timeRotationInThread -rotateOnThreadEnd"
    DEFAULT_SHELL="/bin/bash"
    
    # minimum delay between two umc runs
    # this is to prevent from failures when too frequent runs occur
    MIN_RUN_DELAY=0.05

    def __init__(self):
        self.last_run_time=0

    # run umc instance
    def run_umc(self,umcdef,GlobalContext): 
        # check minimum umc runs delay
        slrun=time.time()-self.last_run_time
        if slrun<UmcRunTask.MIN_RUN_DELAY:
            Msg.info2_msg("Sleeping %.2f seoncds before running the next umc instance..."%(UmcRunTask.MIN_RUN_DELAY-slrun))
            time.sleep(UmcRunTask.MIN_RUN_DELAY-slrun)
        
        # create log directory for this tool if it does not exist
        log_dir=get_umc_instance_log_dir(umcdef.umc_instanceid, GlobalContext)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # tell what we are doing
        Msg.info1_msg("Starting umc instance id '{umc_instanceid}': umc='{umc_toolid}', delay={delay}, count={count}, params='{params}', rotation_timelimit={rotation_timelimit}, log_dir='{log_dir}, log_file_groups={log_file_groups}'".
            format(umc_instanceid=umcdef.umc_instanceid,umc_toolid=umcdef.umc_toolid,delay=umcdef.delay,count=umcdef.count,params=umcdef.params,
                rotation_timelimit=umcdef.rotation_timelimit,log_dir=umcdef.log_dir,log_file_groups=umcdef.log_file_groups))

        # it is important to set setsid as there might be child processes that use tty, this should provide a dedicated tty for them
        # example of such process is sqlcl
        preexec=None
        if "setsid" in umcdef.options:
            preexec=ctypes.CDLL('libc.so.6').setsid

        p = psutil.Popen(UmcRunTask.UMC_LAUNCH_CMD.format(umc_instanceid=umcdef.umc_instanceid,umc_toolid=umcdef.umc_toolid,
                delay=umcdef.delay,count=umcdef.count,params=umcdef.params,rotation_timelimit=umcdef.rotation_timelimit,
                umc_home=GlobalContext.homeDir,log_dir=log_dir,log_file_groups=umcdef.log_file_groups),
            shell=True, executable=UmcRunTask.DEFAULT_SHELL, preexec_fn=preexec, stdin=None, stdout=None, stderr=None)

        self.last_run_time=time.time()
        return p    
    
    def run_task(self, GlobalContext, tdef):
        running=[]; started=[]; waiting=[]
        for umcdef in GlobalContext.umcdefs:
            if umcdef.enabled:
                umcdef.lock.acquire()
                try:
                    if umcdef.proc is None and time.time()>umcdef.start_after:
                        if umcdef.last_started_time is not None and time.time()-umcdef.last_started_time < GlobalContext.params.min_starting_time:
                            Msg.warn_msg("umc instance id '%s' starting frequency is too high (<%d seconds), will not start it now!"
                                %(umcdef.umc_instanceid,GlobalContext.params.min_starting_time))
                            waiting.append("%s, WT=%.2fs"%(umcdef.umc_instanceid,GlobalContext.params.min_starting_time))                        
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
                    umcdef.proc.poll()
                    if not(umcdef.proc.is_running()) and umcdef.proc.returncode is not None:
                        rc=umcdef.proc.returncode
                        if rc != 0:
                            Msg.warn_msg("umc instance %s failed/terminated with exit code %d. Will attempt to restart it after %d seconds."
                                %(umcdef.umc_instanceid,rc,GlobalContext.params.run_after_failure))
                            umcdef.start_after=time.time()+GlobalContext.params.run_after_failure
                            umcdef.num_errors = umcdef.num_errors + 1
                            umcdef.lasterror_time = time.time()
                        umcdef.returncodes.insert(0,(time.time(), rc))
                        if len(umcdef.returncodes)>GlobalContext.params.retc_history:
                            del umcdef.returncodes[-(len(umcdef.returncodes)-GlobalContext.params.retc_history):]
        
                    # clear the process is not runnig or check the process is zombie; this happens when the process ends normally but we still hold a refernece to it
                    if not(umcdef.proc.is_running()) or (umcdef.proc.is_running() and umcdef.proc.status() == psutil.STATUS_ZOMBIE):   
                        del umcdef.proc
                        umcdef.proc=None
                        sleep(0.1)
                                        
                except Exception as e:
                    Msg.warn_msg("There was a problem when quering the process with pid %d: %s"%(umcdef.proc.pid,str(e)))
                    if e.__class__ == psutil.NoSuchProcess:
                        umcdef.proc=None
                    pass
        finally:
            umcdef.lock.release()
    
    def run_task(self, GlobalContext, tdef):
        for umcdef in GlobalContext.umcdefs:
            self.refresh_single_instance(umcdef, GlobalContext)
        
        # report number of open handles per type
        if Msg.verbose:
            fd_result = utils.fd_table_status()
            Msg.info2_msg('Open file handles: %s'%utils.fd_table_status_str())
        
        return True
    
# file log stats and info collection
class CollectLogStatsTask():    
    
    def run_task(self, GlobalContext, tdef):    
        if GlobalContext.umcdefs is not None:
            for ud in GlobalContext.umcdefs:
                if ud.enabled:
                    ud.lock.acquire()
                    try:
                        log_stats=Map(backlog_total=0, errorlog_mtime=0, errorlog_size=0, errorlog_tail=[])                    
                        log_dir=get_umc_instance_log_dir(ud.umc_instanceid, GlobalContext)                
                        
                        if os.path.isdir(log_dir):
                            for file in [os.path.basename(f.path) for f in scandir(log_dir)]:
                                # match the log file waiting to be consumed
                                # there is a maximum of 9 groups (1-9)
                                m1 = re.match(r"^{umc_instanceid}_[0-9\-]+.log.([1-9])$".format(umc_instanceid=ud.umc_instanceid), file) 
                                if m1:
                                    fg_key="backlog_group_%s"%m1.group(1)
                                    if log_stats.get(fg_key) is None:
                                        log_stats[fg_key]=1
                                    else:
                                        log_stats[fg_key]+=1
                                    log_stats.backlog_total += 1
                                # // if match log file
                                
                                # match the error log
                                m2 = re.match(r"^{umc_instanceid}(_[0-9\-]+)?.error.out$".format(umc_instanceid=ud.umc_instanceid), file) 
                                if m2:
                                    stat=os.stat(log_dir + "/" + file)
                                    log_stats.errorlog_size=stat.st_size
                                    if log_stats.errorlog_size>0:
                                        log_stats.errorlog_mtime=stat.st_mtime
                                    else:
                                        log_stats.errorlog_mtime=0
                                    #the below takes too much time to finish, better not run this
                                    #log_stats.errorlog_tail=utils.tail(log_dir + "/" + file, 10)
                                # // if match error log
                            # // for 
                        else:
                            Msg.warn_msg("Directory %s does not exist!"%log_dir)
                        
                        # update log stats
                        ud.log_stats = log_stats                    
                    finally:
                        ud.lock.release()
                # // if enabled
            # // for
        # // if 
        
        return True           
    # // run_task    
# // CollectLogStatsInfoTask
    
# stats collection
class CollectPrcStatsTask():        
    def run_task(self, GlobalContext, tdef):
        umc_counts=Map(count=0, enabled=0, disabled=0, running=0, waiting=0, num_children=0,
            rss=0, cpu=0, cpu_s=0, runs=0, errors=0, last_errortime=0, backlog_total=0)
        if GlobalContext.umcdefs is not None:
            for ud in GlobalContext.umcdefs:
                ud.lock.acquire()
                try:
                    umc_counts.count += 1
                    if ud.enabled: umc_counts.enabled += 1
                    else:
                        umc_counts.disabled += 1
                    umc_counts.errors += ud.num_errors
                    umc_counts.runs += ud.num_runs
                    
                    # update last error time from the error log if it was sooner
                    if ud.log_stats is not None and ud.log_stats.errorlog_mtime > ud.lasterror_time:
                        ud.lasterror_time = ud.log_stats.errorlog_mtime

                    if ud.lasterror_time > umc_counts.last_errortime:
                        umc_counts.last_errortime = ud.lasterror_time
                    
                    if time.time()<ud.start_after:
                        umc_counts.waiting += 1
                    umc_counts.backlog_total += ud.log_stats.backlog_total if ud.get("log_stats") and ud.get("log_stats").get("backlog_total") else 0 

                    # umc instance statistics
                    stats = {}; 
                    
                    # process info
                    p = {}
                    try:
                        if ud.proc is not None:
                            umc_counts.running += 1
                            
                            p["top_pid"] = ud.proc.pid
                            p["uptime"] = time.time() - ud.proc.create_time()
                            p["cmdline"] = ud.proc.cmdline()
                            
                            kids = ud.proc.children(True)
                            rss = 0.0; cpu = 0
                            for k in kids:
                                d = k.as_dict(attrs=['cpu_times', 'memory_info'])
                                cpu = cpu + d["cpu_times"].user
                                rss = rss + d["memory_info"].rss

                            p["rss"] = float(rss/1024/1024) # in MB
                            p["cpu"] = cpu   
                            p["cpu_s"] = cpu/p["uptime"]   
                            p["num_chproc"] = len(kids)
                            
                            umc_counts.rss += p["rss"]
                            umc_counts.cpu += p["cpu"]
                            umc_counts.cpu_s += p["cpu_s"]                            
                            umc_counts.num_children += p["num_chproc"]    
                        # // end if
                    except:
                        pass
                    
                    stats["p"] = p
                    ud.stats = stats        
                finally:
                    ud.lock.release()
            # // for            
            
            # umcrunner stats
            proc=psutil.Process()
            d = proc.as_dict(attrs=['cpu_times', 'memory_info'])
            uptime=time.time()-proc.create_time()
            hostname=socket.gethostname()
            GlobalContext.umcrunner_stats = Map(
                pid=proc.pid,
                hostname=hostname,
                uptime=uptime,
                cpu=d["cpu_times"].user,
                cpu_s=d["cpu_times"].user/uptime,
                rss=float(d["memory_info"].rss/1024/1024),
                threads=proc.num_threads(),
                umc_counts=umc_counts,
                link_umcinstances="/stats/hosts/{hostname}/umc/all".format(hostname=hostname)
            )
            
            return True
        # if umcdefs

# checks if there are sub-processes that are "orphans", i.e. they do not have a parent process
# which was started by umcrunner. This will happen if someone externally kill this umcrunner started process.  
class OrphansCheckTask():    
    
    # retrieves all pids and their pgid from os
    def get_all_pgids(self):
        pgids={}
        cmd=subprocess.Popen('ps ax -o pid,pgid', shell=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
        try:
            for e in cmd.stdout:
                m = re.match(r"^[ ]*([0-9]+)[ ]+([0-9]+)[ ]*$", e) 
                if m:
                    pid = int(m.group(1))
                    pgid = m.group(2)            
                    if pgid not in pgids:
                        pgids[pgid] = []
                    if pid != os.getpid():
                        pgids[pgid].append(pid)
        finally:
            del cmd
        return pgids
    # get_all_pgids
    
    def run_task(self, GlobalContext, tdef):
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
    def run_task(self, GlobalContext, tdef):
        kids=psutil.Process().children(True)

        Msg.info2_msg("There are %d children processes."%(len(kids)))
            
        if len(kids) > GlobalContext.params.max_processes:
            Msg.warn_msg("The current number of child processes %d exceeds the maximum of %d; umcrunner will be paused."
                %(len(kids),GlobalContext.params.max_processes))
            return False
        else:
            return True    

# check for maximum number of zombie processes that cannot exceed the maximum number of umcrunner instances
class MaxZombiesTask():
    def run_task(self, GlobalContext, tdef):
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
        
    def addTask(self, targetClass, time_interval, run_on_global_pause=False, time_limit_pause=0, 
        pause_for=0, time_limit_disable=0, disabled=False):        
        taskdef=Map(
            time_interval=time_interval, target=targetClass(), run_on_global_pause=run_on_global_pause, 
            time_limit_pause=time_limit_pause, pause_for=pause_for, time_limit_disable=time_limit_disable,
            last_run_time=0, last_run_duration=0, result=True, disabled=disabled, run_after=0)
        taskdef.name=taskdef.target.__class__.__name__
        self.tasks.append(taskdef)
        return taskdef
        
    def run_all(self):
        paused = self.GlobalContext.paused
        for tdef in self.tasks:
            if time.time()-tdef.last_run_time > tdef.time_interval and (tdef.run_on_global_pause or not(paused)):
                if tdef.run_after==0 or time.time()>tdef.run_after:
                    if not(tdef.disabled):                         
                        # inform that the task is resumed if it was puased
                        if tdef.run_after>0:
                            tdef.run_after=0
                            Msg.info1_msg("The task %s is resumed."%(tdef.name))
                        
                        # run the task    
                        start_t=time.time()
                        tdef.result = tdef.target.run_task(self.GlobalContext, tdef)
                        end_t=time.time()
                        if not(tdef.result):
                            paused = True
                        tdef.last_run_time = end_t
                        tdef.last_run_duration=end_t-start_t
                        
                        # check to be disabled due to hard limit
                        if tdef.time_limit_disable>0 and tdef.last_run_duration > tdef.time_limit_disable:
                            tdef.disabled=True
                            Msg.warn_msg("The task %s was running for %.2f seconds which is more than the hard maximum of %.2f seconds. The task will be disabled."
                                %(tdef.name, tdef.last_run_duration, tdef.time_limit_disable))
                                
                        # check to be paused due to soft limit
                        elif tdef.time_limit_pause>0 and tdef.last_run_duration > tdef.time_limit_pause:
                            tdef.run_after=end_t+tdef.pause_for
                            Msg.warn_msg("The task %s was running for %.2f seconds which is more than the soft maximum of %.2f seconds. The task will be paused for %.2f seconds."
                                %(tdef.name, tdef.last_run_duration, tdef.time_limit_pause, tdef.pause_for))
                        else:
                            # report on task duration
                            Msg.info2_msg("The task %s was running for %.2f seconds."%(tdef.name,tdef.last_run_duration))

                    # // not disabled
                # // locally paused
            else:
                pass

        old_paused = self.GlobalContext.paused
        self.GlobalContext.paused = not(all([ tdef.result for tdef in self.tasks if tdef.result is not None ]))

        if self.GlobalContext.paused != old_paused:
            Msg.warn_msg("umcrunner state has been %s."%("PAUSED" if self.GlobalContext.paused else "RESUMED"))


