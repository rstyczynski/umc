
Each probe is described by a compact metainformation to specify its location in the system, describe sensed data, etc. Measurements itself are described by name and tags. Tags provided in the metainformation file are static, but the UMC roadmap envision dynamic tags to be used as well. Dynamic tags will be aded to the stream by various filters, aggregstors, shape detectors, threshold checkers, etc. Both static and dynamic tags are used to group together various measurements e.g. to dynamically create graphs.


# YAML
Probe metainformation is collected in a probe.info file using YAML format.

vmstat:
    version:    1.0
    layer:      OS
    subsystem:  kernel
    header: >
        ProcessRunQueue, ProcessBlocked,
        MemSwpd,MemFree,MemBuff,MemCache,
        SwapReadBlocks,SwapWriteBlocks,
        IOReadBlocks,IOWriteBlocks,
        Interrupts,ContextSwitches,
        CPUuser,CPUsystem,CPUidle,CPUwaitIO
    rawheader:
        directive:  
        expected: >  
                procs -----------memory---------- ---swap-- -----io---- -system-- ----cpu----
                 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa
    resources:
        Interrupt:
            Interrupts: interrupt
        Scheduler:
            ContextSwitches: interrupt
        CPU:
            CPUuser: 
            CPUsystem: 
            CPUidle: 
            CPUwaitIO: 
            ProcessRunQueue: queue
            ProcessBlocked: queue
        Memory:
            MemSwpd: 
            MemFree: 
            MemBuff: 
            MemCache: 
        I/O:
            SwapReadBlocks:
            SwapWriteBlocks:
            IOReadBlocks:
            IOWriteBlocks:


## JSON
Presented below JSON is a representation of above YAML.

{
	"vmstat": {
		"version": 1,
		"layer": "OS",
		"subsystem": "kernel",
		"header": "ProcessRunQueue, ProcessBlocked, MemSwpd,MemFree,MemBuff,MemCache, SwapReadBlocks,SwapWriteBlocks, IOReadBlocks,IOWriteBlocks, Interrupts,ContextSwitches, CPUuser,CPUsystem,CPUidle,CPUwaitIO\n",
		"resources": {
			"Interrupt": {
				"Interrupts": "interrupt"
			},
			"Scheduler": {
				"ContextSwitches": "interrupt"
			},
			"CPU": {
				"CPUuser": null,
				"CPUsystem": null,
				"CPUidle": null,
				"CPUwaitIO": null,
				"ProcessRunQueue": "queue",
				"ProcessBlocked": "queue"
			},
			"Memory": {
				"MemSwpd": null,
				"MemFree": null,
				"MemBuff": null,
				"MemCache": null
			},
			"I/O": {
				"SwapReadBlocks": null,
				"SwapWriteBlocks": null,
				"IOReadBlocks": null,
				"IOWriteBlocks": null
			}
		}
	}
}
# PYTHON code to read this structure

import yaml

stream = open("probe.info", "r")
doc = yaml.load(stream)

info = doc['vmstat']

print info['version']
print info['layer']
print info['subsystem']
print info['header']
for resource, resourceMetrics in info['resources'].iteritems():
    print resource
    for metricName, tag in resourceMetrics.iteritems():
        print "--", metricName, "->", tag
        
Output:
1.0
OS
kernel
ProcessRunQueue, ProcessBlocked, MemSwpd,MemFree,MemBuff,MemCache, SwapReadBlocks,SwapWriteBlocks, IOReadBlocks,IOWriteBlocks, Interrupts,ContextSwitches, CPUuser,CPUsystem,CPUidle,CPUwaitIO

Interrupt
-- Interrupts -> interrupt
I/O
-- IOWriteBlocks -> None
-- SwapReadBlocks -> None
-- IOReadBlocks -> None
-- SwapWriteBlocks -> None
CPU
-- CPUuser -> None
-- CPUsystem -> None
-- CPUidle -> None
-- CPUwaitIO -> None
-- ProcessBlocked -> queue
-- ProcessRunQueue -> queue
Scheduler
-- ContextSwitches -> interrupt
Memory
-- MemSwpd -> None
-- MemCache -> None
-- MemFree -> None
-- MemBuff -> None


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