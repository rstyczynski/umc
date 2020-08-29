import sys
import os
import re

res_type = sys.argv[1]     # os.environ['herald_res_type'] #'ens3'
res_name_parameter = sys.argv[2]     # os.environ['herald_res_name'] #'ens3'
dt = int(sys.argv[3])
dt_column = int(sys.argv[4])
dataat = int(sys.argv[5])
out_format = sys.argv[6]   # map | csv
out_data = sys.argv[7]     # compute | forward
separator = sys.argv[8]
herald_state = sys.argv[9]
resource_log_prefix = sys.argv[10]

line = 'start'
data_prv_set = False

header_printed = False

data_now = dict()
data_prv = dict()
data_prv_set = dict()

if not res_name_parameter.startswith('csv:'):

    res_name=res_name_parameter

    header_src = herald_state + '/' + res_type + '/' + res_name + '/header'
    state_dst = herald_state + '/' + res_type + '/' + res_name + '/dvdt'
    if not os.path.exists(state_dst):
        os.makedirs(state_dst)

while line:
    line = sys.stdin.readline()
    #
    # skip header line
    if line.startswith('datetime'): 
        header_line = line
        header_line = header_line.replace('\n', separator)
        header_line = header_line.replace(' ', '')
        #
        if header_line.endswith(separator):
           header_line = header_line[0:-1]
        #
        header = header_line.split(separator)
        #
        if out_data == 'compute' and out_format == 'csv':
            print(header_line)
        
        header_printed = True
        
        continue

    if res_name_parameter.startswith('csv:'):
        # res_name_column=int(res_name_parameter.split(':')[1])
        # #
        # try:
        #     res_name=line.split(separator)[res_name_column-1]
        # except:
        #     continue
        
        res_name_column_def=res_name_parameter.split(':')[1]
        res_name_columns=res_name_column_def.split(',')
        res_name=''
        for res_name_column in res_name_columns:
            try:
                res_name_fragment=line.split(separator)[int(res_name_column)-1]
            except:
                continue
            
            if res_name == '':
                res_name=res_name_fragment
            else:
                res_name=res_name + '_' + res_name_fragment

        # remove non-filename characters
        res_name=re.sub('[^a-zA-Z0-9\.\-\_]','_',res_name)

        data_now[res_name] = list()

        header_src = herald_state + '/' + res_type + '/' + res_name + '/header'
        state_dst = herald_state + '/' + res_type + '/' + res_name + '/dvdt'

        if not os.path.exists(state_dst):
            os.makedirs(state_dst)
        
        if not header_printed:
            # prepare header / prefix
            header_f = open(header_src, "r")
            header_line = header_f.read()
            header_f.close
            #header_line = header_line.replace('\n', '_dvdt' + separator)
            header_line = header_line.replace('\n', separator)
            header_line = header_line.replace(' ', '')
            #
            if header_line.endswith(separator):
                header_line = header_line[0:-1]
            #
            header = header_line.split(separator)
            #
            if out_data == 'compute' and out_format == 'csv':
                print(header_line)
            #
            header_printed = True
    else:
        data_now[res_name] = list()

    # print inpute data in forward mode
    if out_data == 'forward':
        print(line.rstrip())

    line = line.rstrip()
    line_asis = line.split(separator)
    for element in line_asis:
        try:
            value = int(element)
        except:
            value = 0
        data_now[res_name].append(value)

    if sum(data_now[res_name]) == 0:
        continue

    if (res_name in data_prv_set) and line: 
        dv = map(int.__sub__, data_now[res_name], data_prv[res_name])
        
        # print('--- start')
        # print(data_now)
        # print(data_prv)
        # print(dv)
        # print('--- stop')

        if dt_column:
            dt = int(dv[dt_column])
            if dt == 0: 
                dt = 1

        dvdt = [v / dt for v in dv]

        # wriote dvdt state file
        state_f = open(state_dst + '/state', "w")
        for i in range(len(header)-1):
            if i < dataat:
                state_f.write(header[i] + '=' + str(line_asis[i]) + '\n')
            else:
                state_f.write(header[i] + '=' + str(dvdt[i]) + '\n')
        state_f.close

        # write line to dv log 
        if resource_log_prefix != 'no':
            dvdt_log = resource_log_prefix + '_' + res_name + '.log'
            # write header if file does not exist
            if os.path.exists(dvdt_log):
                dvdt_f = open(dvdt_log, "w")
            else:
                dvdt_f = open(dvdt_log, "w")
                for i in range(len(header)-1):
                    dvdt_f.write(header[i])
                    if i < len(header)-1:
                        dvdt_f.write(',')
                dvdt_f.write('\n')
                            
            # write data line
            for i in range(len(header)-1):
                if i < dataat:
                    dvdt_f.write(str(line_asis[i]))
                else:
                    dvdt_f.write(str(dvdt[i]))
                if i < len(header)-1:
                    dvdt_f.write(',')
            dvdt_f.write('\n')    
            
            dvdt_f.close

        # write dvdt data to stdout if needed
        if out_data == 'compute':
            if out_format == 'csv':
                for i in range(len(header)-1):
                    if i < dataat:
                        sys.stdout.write(str(line_asis[i]) + ',')
                    else:
                        sys.stdout.write(str(dvdt[i]) + ',')
                # print last element w/o separator
                sys.stdout.write(str(dvdt[i+1]) + '\n')

                # print(str(header))
                # print(str(dvdt))

            elif out_format == 'map':
                for i in range(len(header)-1):
                    if i < dataat:
                        print(header[i] + '=' + str(line_asis[i]))
                    else:
                        print(header[i] + '=' + str(dvdt[i]))
            else:
                raise Exception('out_format format unknown:' + out_format)
        
    data_prv[res_name] = data_now[res_name]
    data_prv_set[res_name] = True
