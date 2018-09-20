
import re
import sys
import os

class Table:
    def __init__(self, table_def):
        self.table_def = table_def
    
    def format_item(self, cdef, value, skipformat=False, entry=None, adjust=True):
        if cdef.get("format") and not skipformat and value is not None:
            try:
                v = str(cdef["format"](cdef, value, entry))
            except:
                v = "E!"
        else: 
            v = str(value) if value is not None else "-"
        asize=0
        if adjust and cdef.get("_len"):
            asize=cdef["_len"]+2
        
        return "%s"%v.ljust(asize)        
        
    def get_field(self, field_name, data):
        d = data
        for f in field_name.split('.'):
            d = d.get(f)
        return d
        
    def eval_value(self, value, data):
        # get fields placeholders: {placeholder}
        params = list(set(re.findall("\{[a-zA-Z0-9_\-\.]+\}",value)))
        val = value
        if len(params)>1:
            for k in params:
                val = val.replace(k, str(self.get_field(k[1:-1],data)))
            return val        
        if len(params)==1:
            return self.get_field(params[0][1:-1],data)
        if len(params)==0:
            return value
        
    def calc_col_sizes(self):
        for cdef in self.table_def:
            l = len(self.format_item(cdef,cdef["name"], skipformat=True, entry=None, adjust=False))
            if cdef.get("_len") is None or l > cdef["_len"]:
                cdef["_len"] = l                

        for e in self.data:
            for cdef in self.table_def:        
                l = len(self.format_item(cdef,self.eval_value(cdef["value"],e),skipformat=False, entry=e,adjust=False))
                if cdef.get("_len") is None or l > cdef["_len"]:
                    cdef["_len"] = l                
    
    def getTerminalCols(self):
        cols=1000
        try:
            cols = int(os.popen('stty size', 'r').read().split()[1])
        except Exception as e:
            sys.stderr.write("Cannot determine terminal dimensions: %s/n"%(str(e)))
            pass
        return cols
    
    def display(self, data, noterm=False):
        # calc 
        self.data = data
        self.calc_col_sizes()
        
        # display header
        lines=[]
        line = ""
        for cdef in self.table_def:
            line = line + self.format_item(cdef,cdef["name"], skipformat=True, entry=None)
        lines.append(line)

        # display rows
        for e in self.data:
            line = ""
            for cdef in self.table_def:        
                line = line + self.format_item(cdef,self.eval_value(cdef["value"],e),skipformat=False, entry=e)
            lines.append(line)
        
        if not(noterm):
            cols=self.getTerminalCols()
        else:
            cols=1000
        
        for line in lines:
            sys.stdout.write("%s\n"%line[0:cols])         

    def describe(self, noterm=False):
        mlen=0
        for cdef in self.table_def:
            if cdef.get("name") is not None and len(cdef["name"])>mlen:
                mlen=len(cdef["name"])

        if not(noterm):
            cols=self.getTerminalCols()
        else:
            cols=1000

        for cdef in self.table_def:
            if cdef.get("name") is not None:
                line="{name}  {descr}\n".format(name=cdef["name"].ljust(mlen), descr=cdef["help"]) 
                sys.stdout.write(line[0:cols])    
        
