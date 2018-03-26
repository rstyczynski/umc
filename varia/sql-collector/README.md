# Oracle SQL Query Metric Collector

Oracle SQL Query Metric Collector is a javascript utility running in [SQLcl](http://www.oracle.com/technetwork/developer-tools/sqlcl/overview/sqlcl-index-2994757.html) that can be used to run arbitrary SQL queries in a Oracle DB and writing results to standard output in CSV format. The utility runs a SQL query in defined intervals and defined number of times. It was originally developed as a probe for [Universal Metric Collector](https://github.com/rstyczynski/umc) but can be used independently. 

In order to use sql-collector, you need to have the following in your system:

1. [Oracle SQL command line utility (SQLcl)](http://www.oracle.com/technetwork/developer-tools/sqlcl/overview/sqlcl-index-2994757.html) available on your system path.
2. Access to an Oracle database.

If you want to just test ```sql-collector``` and you do not have a working Oracle database available, you can use Oracle Database Express Edition (xe) that can also be run as a Docker container (see [Oracle XE Docker Image](https://hub.docker.com/r/wnameless/oracle-xe-11g/) for details).

Run ```sql-collector --help``` to get more information on how to use this tool.

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

If you can access your database at ```127.0.0.1:1521``` as user ```brian``` with password ```topsecret```, you have a SQL query available in a file ```mysqlquery.sql```, and you want to run this query 3 times with interval 10 seconds, then run the below command:  

```
sql-collector --connect brian/topsecret@127.0.0.1:1521 --query mysqlquery.sql --interval 10 --count 3 
```

In addition, if you want to replace any string or your custom defined placeholder in the sql query file, you can use a regular expression to replace your placeholder string with some value. For example, the below command will replace ```__MYSCHEMA``` placeholder in ```mysqlquery.sql``` with ```HERSCHEMA``` value. You can define as many placeholders as you need. 

```
sql-collector --connect brian/topsecret@127.0.0.1:1521 --query mysqlquery.sql --interval 10 --count 3 --#MYSCHEMA HERSCHMEA 
```

# License

free and free