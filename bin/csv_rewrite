#!/usr/local/bin/python3

from __future__ import print_function
import sys
import os
import sys
import csv
import getopt
from datetime import datetime

#  write to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# soluton for strange head problem
# https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-when-piping-prog-py-othercmd
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL) 

# ~ 

script_name = 'csv_formatter'

cli_args = [
  'columns=', 
  'name=', 
  'data_starts_at=', 
  'show_current_data', 
  'record_max_age=',
  'accept_older_records',
  'datetime_col=',
  'datetime_tz_col=',
  'csv_row_buffer_size=',
  'null_value_mark='
]

def usage():
  print("Usage: {} ".format(script_name), end='')
  print(cli_args)

try:
    opts, args = getopt.getopt( sys.argv[1:], '', cli_args )
except getopt.GetoptError as err:
    print(str(err))
    usage()
    sys.exit(1)

columns_csv = ''
data_starts_at=5

show_current_data = False
record_max_age = 300
reject_older_records = True

datetime_col = 0
datetime_tz_col= 1
csv_row_buffer_size=100
null_value_mark='(!)'

for opt, arg in opts:
    if opt in ('--help'):
        usage()
        sys.exit(2)
    elif opt in ('--name'):
        name = arg
    elif opt in ('--columns'):
        columns_csv = arg
    elif opt in ('--data_starts_at'):
        data_starts_at = int(arg)
    elif opt in ('--show_current_data'):
        show_current_data = True
    elif opt in ('--record_max_age'):
        record_max_age = int(arg)
    elif opt in ('--record_max_age'):
        record_max_age = int(arg)
    elif opt in ('--accept_older_records'):
        reject_older_records = False
    elif opt in ('--datetime_col'):
        datetime_col = int(arg)
    elif opt in ('--datetime_tz_col'):
        datetime_tz_col = int(arg)
    elif opt in ('--csv_row_buffer_size'):
        csv_row_buffer_size = int(arg)
    elif opt in ('--null_value_mark'):
        null_value_mark = arg
    else:
        usage()
        sys.exit(1)

columns = columns_csv.split(',')
columns_pos = []

csv_header = []
data_header = []
system_header = []

csv_row_buffer = []

latest_record_timestamp = 0

reader = csv.reader(sys.stdin)
for csv_row in reader:
    if len(csv_row) == 0:
      break

    record_date_time_str = csv_row[datetime_col]
    record_date_time_tz_str = csv_row[datetime_tz_col]
    if record_date_time_str == 'datetime':
        if len(data_header) != 0:
          eprint('Info: Header already registered. Ignoring new one.')
        else:
          # remove spaces
          for col_name in csv_row:
            csv_header.append(col_name.strip())
          
          system_header = csv_header[0:data_starts_at]

          # no given column names in argumets. use all columns in source order
          if len(columns) == 1 and columns[0] == '':
            for column in csv_header[data_starts_at:len(csv_header)]:
              columns_pos.append(csv_header.index(column))
              data_header.append(column)
          else:
            # use column names from argments with provided rder
            for column in columns:
              if column in csv_header:
                columns_pos.append(csv_header.index(column))
              else:
                columns_pos.append(-1)

              data_header.append(column)
          
          new_line = True
          for col_name in system_header:
            if new_line:
              print("{}".format(col_name), end='')
              new_line = False
            else:
              print(",{}".format(col_name), end='')

          for col_name in data_header:
            if new_line:
              print("{}".format(col_name), end='')
              new_line = False
            else:
              print(",{}".format(col_name), end='')
            
          print()

          # print data from pre-header buffer
          if len(csv_row_buffer) > 0:
            for csv_row_accu in csv_row_buffer:
              for pos in range(0, data_starts_at):
                if pos == 0:
                  print("{}".format(csv_row_accu[pos]), end='')
                else:
                  print(",{}".format(csv_row_accu[pos]), end='')

              for pos in columns_pos: 
                if pos >= 0:
                  print(",{}".format(csv_row_accu[pos]), end='')
                else:
                  print(",{}".format(null_value_mark), end='')

              print()  
            
            csv_row_buffer = []

    else:
      record_date_time_full_str = record_date_time_str + ' ' + record_date_time_tz_str
      record_date_time = datetime.strptime(record_date_time_full_str, '%Y-%m-%d %H:%M:%S %z')

      record_age = datetime.now().timestamp() - record_date_time.timestamp()

      
      # ignore old records
      if show_current_data and (record_age > record_max_age):
        eprint("Info: Data row older than allowed age. This age:{}, max age:{}, csv record:{}".format(record_age,record_max_age,csv_row))
      elif reject_older_records and (record_date_time.timestamp() <= latest_record_timestamp):
        eprint("Info: Data row older than newest seen. Ignoring. This record:{}, latest seen:{}, csv record:{}".format(record_date_time, latest_record_timestamp,csv_row))
      else:
        latest_record_timestamp = record_date_time.timestamp()
        # wait for header row
        if len(data_header) == 0:
          eprint("Info: Waiting for header column. This row will be flushed just after header arrives.")
          csv_row_buffer.append(csv_row)

          if len(csv_row_buffer) > csv_row_buffer_size:
            eprint('Error: Waiting for header column failed after {} data rows.'.format(csv_row_buffer_size))
            sys.exit(1)
        else:

          # print current csv data
          for pos in range(0, data_starts_at):
            if pos == 0:
              print("{}".format(csv_row[pos]), end='')
            else:
              print(",{}".format(csv_row[pos]), end='')

          for pos in columns_pos: 
            if pos >= 0:
              print(",{}".format(csv_row[pos]), end='')
            else:
              print(",{}".format(null_value_mark), end='')
          #
          print()
        
