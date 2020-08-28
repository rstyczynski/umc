#!/bin/bash

if [ -z "$shared_trace_root" ] || [ -z "$server_env" ] || [ -z "$server_type" ]; then
    echo "Usage: rsync_trace.sh 
, with exported veriables: server_env, server_type, shared_trace_root"
    return 1
fi

rsync -rt ~/trace/obd/ $shared_trace_root/$server_env/$(hostname)/runtime/obd

if [ ! -d $shared_trace_root/$server_env/$(hostname)/runtime/log/$(date +%Y-%m-%d) ]; then
    mkdir -p $shared_trace_root/$server_env/$(hostname)/runtime/log/$(date +%Y-%m-%d)
fi
rsync -t ~/trace/log/$(date +%Y-%m-%d)/ $shared_trace_root/$server_env/$(hostname)/runtime/log/$(date +%Y-%m-%d)