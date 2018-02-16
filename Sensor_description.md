
Each probe is described by a compact metainformation to specify its location in the system, describe sensed data, etc. Measurements itself are described by name and tags. Tags are used to group together various measurements.

In this version of UMC, tag name is used to gather various measurements together on a single graph.


# YAML
Probe metainformation is collected in a probe.info file using YAML format.

vmstat:
    version:    1.0
    layer:      OS
    subsystem:  kernel
    headers:    
    resources:
        Interrupt:
            - Interrupts: interrupt
        Scheduler:
            - ContextSwitches: interrupt
        CPU:
            - CPUuser: 
            - CPUsystem: 
            - CPUidle: 
            - CPUwaitIO: 
            - ProcessRunQueue: queue
            - ProcessBlocked: queue
        Memory:
            - MemSwpd: 
            - MemFree: 
            - MemBuff: 
            - MemCache: 
        I/O:
            - SwapReadBlocks:
            - SwapWriteBlocks:
            - IOReadBlocks:
            - IOWriteBlocks:


## JSON
Presented below JSON is a representation of above YAML.

{"vmstat":
    {"version":1.0,
    "layer":"OS",
    "subsystem":"kernel",
    "resources": {
        "Interrupt":
            [{"Interrupts":"interrupt"}],
        "Scheduler":
            [{"ContextSwitches":"interrupt"}],
        "CPU":
            [{"CPUuser":null},{"CPUsystem":null},{"CPUidle":null},{"CPUwaitIO":null},{"ProcessRunQueue":"queue"},{"ProcessBlocked":"queue"}],
        "Memory":
            [{"MemSwpd":null},{"MemFree":null},{"MemBuff":null},{"MemCache":null}],
        "I/O":[{"SwapReadBlocks":null},{"SwapWriteBlocks":null},{"IOReadBlocks":null},{"IOWriteBlocks":null}]
        }
    }
}

# PYTHON code to read

import yaml

stream = open("probe.info", "r")
docs = yaml.load_all(stream)
for doc in docs:
    for k,v in doc.items():
        print k, "->", v
    print "\n",


vmstat -> {'subsystem': 'kernel', 'headers': None, 'layer': 'OS', 'version': 1.0, 'resources': {'Interrupt': [{'Interrupts': 'interrupt'}], 'I/O': [{'SwapReadBlocks': None}, {'SwapWriteBlocks': None}, {'IOReadBlocks': None}, {'IOWriteBlocks': None}], 'CPU': [{'CPUuser': None}, {'CPUsystem': None}, {'CPUidle': None}, {'CPUwaitIO': None}, {'ProcessRunQueue': 'queue'}, {'ProcessBlocked': 'queue'}], 'Scheduler': [{'ContextSwitches': 'interrupt'}], 'Memory': [{'MemSwpd': None}, {'MemFree': None}, {'MemBuff': None}, {'MemCache': None}]}}



# For future use
Measurement desciprito nmay be extarnalized to template. It's to be done later.

types:
    - CPU:
        type: 		range
        min:		0
        max:		100
        unit:		'%'
        logscale:	false
        tag:
            - utilization
    - queue:
        type: 		current_value
        min:		0
        max:		50
        unit:		''
        logscale:	false
        tag:
          - runqueue