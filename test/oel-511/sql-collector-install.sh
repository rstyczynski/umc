#!/bin/bash
# sql-collector installation script

# sql-collector does not need to be installed
# it only needs to exist in varia
export SQLCOLLECTOR_HOME="$HOME/umc/varia/sql-collector"

# sql-collector should be in umc/varia/sql-collector/bin
if [ ! -f $SQLCOLECTOR_HOME/bin/sql-collector ]; then
        echo >&2 "Cannot find sql-collector script in $SQLCOLLECTOR_HOME/bin."
        echo >&2 "Have you properly cloned umc repo with sub-modules?"
fi

# environment variables
echo "" >>~/.bash_profile
echo "# sql-collector environment variables" >>~/.bash_profile
echo "source ~/umc/test/oel-511/sql-collector-env.sh" >>~/.bash_profile 

