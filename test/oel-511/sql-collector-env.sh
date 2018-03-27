#!/bin/bash
# sql-collector environment variables 

export SQLCOLLECTOR_HOME="$HOME/umc/varia/sql-collector"

# sql-collector should be in umc/varia/sql-collector/bin
if [ ! -f $SQLCOLLECTOR_HOME/bin/sql-collector ]; then
	echo >&2 "Cannot find sql-collector script in $SQLCOLLECTOR_HOME/bin."
	echo >&2 "Have you properly cloned umc repo with sub-modules?"
fi

export PATH=$SQLCOLLECTOR_HOME/bin/:$PATH
