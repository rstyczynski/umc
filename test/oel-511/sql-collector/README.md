# Oracle SQL Query Metric Collector

Oracle SQL Query Metric Collector is a javascript utility running in SqlCl that can be used to run arbitrary SQL queries in a Oracle DB and writing results to standard output in CSV format. The utility runs a SQL query on pre-defined intervals and a pre-defined number of times. It was originally developed as a probe for Universal Metric Collector but can be used independently. 

Type ./sql-executor.sh --help for more information on how to use it.

```
Oracle SQL query metric collector
Usage: --query <string> --count <number> --interval <number> [--noHeaders] [--showSQLErrors] [--#([a-zA-Z0-9_\-\*\+\.]+) <string>] 

Where: 
   --query                    SQL query file.
   --count                    Number of iterations the query will run.
   --interval                 Delay in seconds betwen iterations.
   --noHeaders                Headers will not be written to the output.
   --showSQLErrors            SQL errors will be written to the output.
   --#([a-zA-Z0-9_\-\*\+\.]+) A regular expression to replace a string with a value in the query.
```

./sql-executor.sh "$DB_CONNSTR" --query flowstat.sql --interval 2 --count 5 --#__SOAINFRA PRFMX_SOAINFRA






