#!/bin/bash
# this script will install python 2.7.11 locally
# this is required in a restricted environment when cannot update python version os-wide
# this script assumes and umc is under current user's home

# get python 2.7.11 installation binaries
# check if it exsits in varia and download when it does not
if [ ! -f ~/umc/varia/Python-2.7.11.tgz ]; then
        cd ~/umc/varia
        wget --progress=bar:force $(cat ~/umc/varia/Python-2.7.11.tgz.download)
fi

# unpack python 2.7.11
mkdir ~/python
cd ~/python
tar zxfv ../umc/varia/Python-2.7.11.tgz
find ~/python -type d | xargs chmod 0755
cd ~/python/Python-2.7.11

# build python binaries
./configure --prefix=$HOME/python
make && make install

# umc scripts use python2 in shebang
# hence create a symbolic link for python2 to point to python 2.7.11
cd $HOME/python/Python-2.7.11/
ln -s python python2

echo "source ~/umc/test/oel-511/python-2.7.11-env.sh" >>~/.bash_profile
