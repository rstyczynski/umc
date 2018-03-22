#!/bin/bash
# this script installs sqlcl locally
# it is used for testing/development of umc sql probes against oracle DB

SQLCLZIP="~/umc/varia/sqlcl-17.4.0.354.2224-no-jre.zip"

# check that sqlcl installation binaries are in varia
if [ ! -f ~/umc/varia/sqlcl-17.4.0.354.2224-no-jre.zip ]; then
	echo >&2 "SQLcl installation binaries at ~/umc/varia/sqlcl-17.4.0.354.2224-no-jre.zip is not available." 
    echo >&2 "Please download the binary first by following a link in $SQLCLZIP.download"
	exit 1
fi

# install sqlcl locally
mkdir -p ~/libs && rm -fr ~/libs/sqlcl && cd ~/libs && unzip ~/umc/varia/sqlcl-17.4.0.354.2224-no-jre.zip

# environment variables
echo "" >>~/.bash_profile
echo "# sqlcl environment variables" >>~/.bash_profile
echo "source ~/umc/test/oel-511/sqlcl-17.4.0-env.sh" >>~/.bash_profile


