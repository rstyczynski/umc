source ~/umc/bin/umc.h &>/dev/null

if [ $? != 0 ]; then 
	echo ''
	echo 'Error setting up umc, see below the details:' 
	source $HOME/umc/bin/umc.h 
	echo '' 
else 
	umc
fi

# the below is for umc sql-collector to connect to a testing DB
# Oracle DB instance to connect to
export DB_HOST=""
export DB_PORT="1521"
export DB_SERVICE="xe"

# if $DB_HOST is empty, let's assume that there is a DB listening on the IP of this machine's gateway
# this is useful to connect to a DB running e.g. in the docker on the host computer (docker pull wnameless/oracle-xe-11g)
if [ "$DB_HOST" = "" ]; then
	export DB_HOST=$(/sbin/route | grep "default" | awk '{print $2}')
	echo "DB Host guessed as $DB_HOST"
fi

# check if DBHOST is listening on the defined port
echo 2>/dev/null >/dev/tcp/$DB_HOST/$DB_PORT
if [ ! $? -eq 0 ]; then
    echo ""
	echo >&2 "DB host is not listening at $DB_HOST:$DB_PORT"
	echo >&2 "Oracle DB is either not running or this is wrong host/port information."
	echo >&2 "Check the DB, let this script guess it by leaving DB_HOST variable blank or set it in umc/test/oel-511/sqlcl-17.4.0-env.sh"
	echo >&2 "Perhaps you can use a docker image wnameless/oracle-xe-11g ?"
fi

# the u/p here is valid for XE db running as a docker container wnameless/oracle-xe-11g
export DB_CONNSTR="sys/oracle@$DB_HOST:$DB_PORT:$DB_SERVICE as sysdba"
echo "DB connection string is $DB_CONNSTR"

