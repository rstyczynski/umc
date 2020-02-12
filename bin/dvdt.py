import sys
import os

res_type = sys.argv[1]     # os.environ['herald_res_type'] #'ens3'
res_name = sys.argv[2]     # os.environ['herald_res_name'] #'ens3'
dt = int(sys.argv[3])
dt_column = int(sys.argv[4])
out_format = sys.argv[5]   # map | csv
out_data = sys.argv[6]     # compute | forward
separator = sys.argv[7]
herald_state = sys.argv[8]

header_src = herald_state + '/' + res_type + '/' + res_name + '/header'
state_dst = herald_state + '/' + res_type + '/' + res_name + '/dvdt'
if not os.path.exists(state_dst):
    os.makedirs(state_dst)

line = 'start'
data_prv_set = False

# prepare header / prefix
header_f = open(header_src, "r")
header_line = header_f.read()
header_f.close
#header_line = header_line.replace('\n', '_dvdt' + separator)
header_line = header_line.replace('\n', separator)
header_line = header_line.replace(' ', '')

if header_line.endswith(separator):
    header_line = header_line[0:-1]

header = header_line.split(separator)

if out_data == 'compute' and out_format == 'csv':
    print(header_line)

while line:
    data_now = []
    line = sys.stdin.readline()

    # print inpute data in forward mode
    if out_data == 'forward':
        print(line.rstrip())

    for element in line.rstrip().split(separator):
        try:
            value = int(element)
        except:
            value = 0
        data_now.append(value)

    if data_prv_set == True and line: 
        dv = map(int.__sub__, data_now, data_prv)
        
        print(data_now)
        print(data_prv)
        print(dv)

        if dt_column:
            dt = dv[dt_column]
            if dt == 0: 
                dt = 1

        dvdt = [v / dt for v in dv]

        # wriote dvdt state file
        state_f = open(state_dst + '/state', "w")
        for i in range(len(header)):
            state_f.write(header[i] + '=' + str(dvdt[i]) + '\n')
        state_f.close

        # write dvdt data to stdout if needed
        if out_data == 'compute':
            if out_format == 'csv':
                print(str(dvdt).replace('[','').replace(']',''))
            elif out_format == 'map':
                for i in range(len(header)-1):
                    print(header[i] + '=' + str(dvdt[i]))
            else:
                raise Exception('out_format format unknown:' + out_format)
        
    data_prv = list(data_now)
    data_prv_set = True