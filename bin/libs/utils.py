
import os
import sys
import stat
import json
import re

_fd_types = (
    ('REG', stat.S_ISREG),
    ('FIFO', stat.S_ISFIFO),
    ('DIR', stat.S_ISDIR),
    ('CHR', stat.S_ISCHR),
    ('BLK', stat.S_ISBLK),
    ('LNK', stat.S_ISLNK),
    ('SOCK', stat.S_ISSOCK)
)

# *** helper Map object
class Map(dict):
    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __delattr__(self, item):
        self.__delitem__(item)

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]

    def to_json(self,encoder=None,exclude=[]):
        d = { k:v for k,v in self.__dict__.items() if k not in exclude }        
        return json.dumps(d, skipkeys=True,cls=encoder)

class PathDef():
    def __init__(self, path_def):
        self.path_def=path_def

    def params(self, path):
        path_re=self.path_def
        
        # find all params in path_def
        params_def=re.findall("(\{[a-zA-Z0-9_\.]+\})", self.path_def)
        
        # create re pattern by replacing parameters in path_def with pattern to match parameter values
        for p_def in params_def: path_re=path_re.replace(p_def, "([a-zA-Z\-0-9\._]+)")
        
        # get params values
        res=re.findall("^" + path_re + "$", path)
        values=[]
        for x in res:
            if type(x) is tuple: values.extend(list(x))
            else: values.append(x)
        
        params=Map()
        params.params=Map()
        params.__path_def__=self.path_def
        params.__path__=path
        params.replace = self.replace
        for x in range(0, len(params_def)):
            if x < len(values): params.params[params_def[x][1:-1]]=str(values[x])
            else:
                #Msg.warn_msg("The path '%s' does not match definition '%s'"%(path, self.path_def))
                return None
        
        return params
    
    def replace(self, params, paramsMap):        
        new_path=params.__path__
        for k,v in paramsMap.items():
            if params.params.get(k):
                new_path = new_path.replace("%s"%params.params.get(k), v, 1)
            else:
                raise Exception("The param '%s' has not been found in path definition '%s'."%(k, self.path_def))
        
        return new_path

# convert to float, return def (default is None) when cannot convert
def float_ex(val, defv=None):
    try:
        return float(val)
    except:
        return defv 

def unpack(dict, s):
    ns=s
    for k,v in dict.items():
        ns = ns.replace("{%s}"%k,str(v))
    return ns

# from https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
                             
def fd_table_status():
    result = []
    for fd in range(100):
        try:
            s = os.fstat(fd)
        except Exception as e:
            continue
        for fd_type, func in _fd_types:
            if func(s.st_mode):
                break
        else:
            fd_type = str(s.st_mode)
        result.append((fd, fd_type))
    return result

def fd_table_status_str():
    fd_result = fd_table_status()
    return ', '.join(['{0}: {1}'.format(*i) for i in fd_result])
    
def tail(f, n, offset=0):
    stdin,stdout = os.popen2("tail -n "+str(n)+" "+f)
    stdin.close()
    lines = stdout.readlines(); stdout.close()
    return lines    

