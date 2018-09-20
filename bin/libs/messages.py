
import sys
import datetime

# messages colors
class bcolors:
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    
# messages types
MSG_INFO  = 0
MSG_ERROR = 1
MSG_WARN  = 2
    
lasterror=None          # last error text
lasterrorcount=0        # last error count
verbose=False
    
# *** print info message
def message(type, msg, forcePrint=False):
    global lasterror; global lasterrorcount
    
    # count number of errors and exit if the error message is the same as the previous one
    if type == MSG_ERROR and lasterror == msg:
        lasterrorcount=lasterrorcount+1
        return

    # default is stdout
    out = sys.stdout
    
    # error stream
    if type == MSG_ERROR or type == MSG_WARN:
        out = sys.stderr
        
    # colors
    out_color = ''; end_color_out = ''
    error_color=bcolors.FAIL; end_color_error = bcolors.ENDC
    if type == MSG_ERROR and sys.stderr.isatty():
        out_color = bcolors.FAIL; end_color_out = bcolors.ENDC
    if type == MSG_WARN and sys.stderr.isatty():
        out_color = bcolors.WARNING; end_color_out = bcolors.ENDC

    # only write info messages in verbose mode
    if ((verbose or forcePrint) and type == MSG_INFO) or type == MSG_ERROR or type == MSG_WARN:
        # the message has changed but tell how many previous error messages there were if not only one
        if lasterrorcount > 0:
            if not(sys.stderr.isatty()):
                error_color=''; end_color_error=''
                
            sys.stderr.write("[" + str(datetime.datetime.now()) + "]:" + error_color + 
                " The previous error occurred %d times!"%lasterrorcount + end_color_error + "\n")
            sys.stderr.flush()
            lasterrorcount=0
        
        # write the message to respective stream
        out.write("[" + str(datetime.datetime.now()) + "]:" + out_color + " " + msg + end_color_out + "\n")  
        out.flush()
        
        # if the message type is error, remember the message and reset the counter
        if type == MSG_ERROR:
            lasterror=msg
            lasterrorcount=0
        else:
            lasterror=None

def info1_msg(msg):
    message(MSG_INFO, msg, True)

def info2_msg(msg):
    message(MSG_INFO, msg)
    
def err_msg(msg):
    message(MSG_ERROR, msg)    

def warn_msg(msg):
    message(MSG_WARN, msg)    
