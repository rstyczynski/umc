#!/bin/bash
# this script installs sqlcl locally
# it is used for testing/development of umc sql probes against oracle DB

SQLCLZIP="~/umc/varia/jdk-8u162-linux-x64.tar.gz"

# check that sqlcl installation binaries are in varia
if [ ! -f ~/umc/varia/jdk-8u162-linux-x64.tar.gz ]; then
    echo >&2 "SQLcl installation binaries at ~/umc/varia/jdk-8u162-linux-x64.tar.gz is not available." 
    echo >&2 "Please download the binary first by following a link in ~/umc/varia/jdk-8u162-linux-x64.tar.gz.download"
    exit 1
fi

# install sqlcl locally
mkdir -p ~/libs && rm -fr ~/libs/jdk1.8.0_162 && cd ~/libs && tar xvzf ~/umc/varia/jdk-8u162-linux-x64.tar.gz

# environment variables
echo "" >>~/.bash_profile
echo "# jdk environment variables" >>~/.bash_profile
echo "source ~/umc/test/oel-511/jdk-8u162-env.sh" >>~/.bash_profile


