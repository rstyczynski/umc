
import psutil
import messages as Msg

def on_terminate(proc):
    Msg.info2_msg("...process {} terminated with exit code {}".format(proc.pid, proc.returncode))

# terminates all children of this process
def terminate_process_children(proc, timeout=10):
    # get all children processes
    procs = proc.children(recursive=True)
    
    Msg.info1_msg("Terminating process tree of pid %d with %d children..."%(proc.pid,len(procs)))

    if len(procs) > 0:
        # send SIGTERM
        for p in procs:
            try:
                p.terminate()
            except:
                pass
            
        # wait for processes to die
        gone, alive = psutil.wait_procs(procs, timeout=timeout, callback=on_terminate)
        
        # send force kill if there are still live processs
        if alive:
            Msg.warn_msg("There were %d child processes that did not terminare within the timeout of %d seconds. Killing them..."
                %(len(alive),timeout))        
            for p in alive:
                try:
                    p.kill()
                except:
                    pass
# end terminate_process_children
    
# termina all children, i.e umc instances
def terminate_children(timeout=10):
    terminate_process_children(psutil.Process())
