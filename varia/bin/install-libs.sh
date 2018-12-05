#!/bin/bash
# script to install third-party tools and libraries for umc.
# May-June 2018, tomas@vitvar.com

# the tools will be installed to the current directory from which this script was started
LIBS_HOME="$(pwd)/libs"

# the installation
INSTALL_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
INSTALL_LOG="$LIBS_HOME/install-$(date "+%Y%m%d-%H%M%S").log"
ENV_FILE="$LIBS_HOME/umc-libs-env.sh"

show_help () {
	echo "UMC libraries installation script"
	echo "Usage: $(basename "$0") [--yes] [--python [--no-python-zlib]] [--jdk] [--sqlcl]"
	echo "       [--sql-collector] [--dms-collector] [--influxdb] [--python-libs]"
	echo ""
	echo "When none of the libraries are specified, all libraries will be installed."
	echo "Option --yes will answer all questions as \"yes\"."
	echo ""
}

# INSTALL PYTHON
install_python () {
	# binary file for python and tool directory name
	BINFILE="Python-2.7.11.tgz"
	TOOLDN="Python-2.7.11"

	echo "* Installing python: $BINFILE" 

	if [ ! -d $LIBS_HOME/python ]; then
		# get python 2.7.11 installation binaries
		# check if it exsits in varia and download when it does not
		if [ ! -f $INSTALL_HOME/$BINFILE ]; then
		        cd $INSTALL_HOME
		        wget --progress=bar:force $(cat $INSTALL_HOME/$BINFILE.download)
		fi

		# unpack python 2.7.11
		mkdir -p $LIBS_HOME/python
        cd $LIBS_HOME/python
		echo "  - unpacking..." 
		tar zxfv $INSTALL_HOME/$BINFILE >>$INSTALL_LOG 2>&1
    find $LIBS_HOME/python -type d | xargs chmod 0755
    cd $LIBS_HOME/python/$TOOLDN

		# build zlib
		if $PYTHON_ZLIB; then
			echo "  - building zlib..."
			mkdir -p $LIBS_HOME/zlib
			cd Modules/zlib
			./configure --prefix=$LIBS_HOME/zlib >>$INSTALL_LOG 2>&1
			make install >>$INSTALL_LOG 2>&1

			if [ $? != 0 ]; then
				echo ""
				echo >&2 "An error occured while installing zlib."
				echo >&2 "Check $INSTALL_LOG for details."
			fi

			cd ../..
		fi

		# build python binaries
		echo "  - configuring..." 
		./configure --prefix=$LIBS_HOME/python >>$INSTALL_LOG 2>&1

		# add zlib config
		if $PYTHON_ZLIB; then		
			echo "zlib zlibmodule.c -I$LIBS_HOME/zlib/include -L$LIBS_HOME/zlib/lib -lz" >>Modules/Setup
		fi
		
		echo "  - building..." 
		make >>$INSTALL_LOG 2>&1
		make install >>$INSTALL_LOG 2>&1

		if [ $? != 0 ]; then
			echo ""
			echo >&2 "An error occured while installing Python."
			echo >&2 "Check $INSTALL_LOG for details."
		fi

		# umc scripts use python2 in shebang
		# hence create a symbolic link for python2 to point to python 2.7.11
		cd $LIBS_HOME/python/$TOOLDN/ && ln -s python python2

		# environment variables
		echo "# python" >>$ENV_FILE
		echo "export PATH=$LIBS_HOME/python/Python-2.7.11/:\$PATH" >>$ENV_FILE
		echo "export PYTHONPATH=$LIBS_HOME/python/Python-2.7.11" >>$ENV_FILE
		echo "" >>$ENV_FILE

	else
		echo >&2 "  - Python has already been installed in $LIBS_HOME/python, skipping."
	fi
}

# INSTALL JDK
install_jdk () {
	# binary file for jdk and tool directory name
	BINFILE="jdk-8u162-linux-x64.tar.gz"
	TOOLDN="jdk1.8.0_162"	

	echo "* Installing jdk: $BINFILE" 

	if [ ! -d $LIBS_HOME/$TOOLDN ]; then
		# check that sqlcl installation binaries are in varia
		if [ ! -f $INSTALL_HOME/$BINFILE ]; then
		    echo ""
		    echo >&2 "SQLcl installation binaries at $INSTALL_HOME/$BINFILE are not available." 
		    echo >&2 "Please download the binary first by following a link in $INSTALL_HOME/$BINFILE.download"
		    exit 1
		fi

		# install sqlcl locally
		echo "  - unpacking..." 
		cd $LIBS_HOME && tar xvzf $INSTALL_HOME/$BINFILE >>$INSTALL_LOG 2>&1

		# replace random with urandom
		sed -i.bckp s#securerandom.source=file:/dev/random#securerandom.source=file:/dev/urandom#g $LIBS_HOME/$TOOLDN/jre/lib/security/java.security
		echo "  - /dev/random replaced by /dev/urandom in $LIBS_HOME/$TOOLDN/jre/lib/security/java.security" 

		# environment variables
		echo "# Java" >>$ENV_FILE
		echo "export PATH=$LIBS_HOME/jdk1.8.0_162/bin/:\$PATH" >>$ENV_FILE
		echo "export JAVA_HOME=$LIBS_HOME/jdk1.8.0_162" >>$ENV_FILE
		echo "" >>$ENV_FILE
	else		
		echo >&2 "  - JDK has already been installed in $LIBS_HOME/$TOOLDN, skipping."		
	fi
}

# INSTALL SQLcl (SQL command line)
install_sqlcl () {
	# binary file for sqlcl
	BINFILE="sqlcl-17.4.0.354.2224-no-jre.zip"
	TOOLDN="sqlcl"

	echo "* Installing sqlcl: $BINFILE" 

	if [ ! -d $LIBS_HOME/$TOOLDN ]; then
		# check that sqlcl installation binaries are in varia
		if [ ! -f $INSTALL_HOME/$BINFILE ]; then
			echo ""
			echo >&2 "SQLcl installation binaries at $INSTALL_HOME/$BINFILE are not available." 
		  echo >&2 "Please download the binary first by following a link in $INSTALL_HOME/$BINFILE.download"
			exit 1
		fi

		# install sqlcl locally
		echo "  - unpacking..." 
		cd $LIBS_HOME && unzip $INSTALL_HOME/$BINFILE >>$INSTALL_LOG 2>&1
		
		# add min and max JVM memory
		sed -i.bckp '/AddVMOption -Xss10M/a AddVMOption -Xms128m\nAddVMOption -Xmx128m\nAddVMOption -Duser.timezone=UTC' $LIBS_HOME/sqlcl/bin/sql
		
		# env variables
		echo "# sqlcl" >>$ENV_FILE
		echo "export PATH=$LIBS_HOME/sqlcl/bin/:\$PATH" >>$ENV_FILE
		echo "" >>$ENV_FILE
	else
		echo >&2 "  - SQLcl has already been installed in $LIBS_HOME/$TOOLDN, skipping."				
	fi

}

# INSTALL SQL COLLECTOR
install_sqlcollector () {
	# binary file for sql collector
	BINFILE="sql-collector"
	TOOLDN="sql-collector"

	echo "* Installing SQL collector: $BINFILE" 

	if [ ! -d $LIBS_HOME/$TOOLDN ]; then

		# sql-collector should be in umc/varia/sql-collector/bin
		if [ ! -f $INSTALL_HOME/$BINFILE/bin/sql-collector ]; then
		        echo ""
		        echo >&2 "Cannot find sql-collector script in $INSTALL_HOME/$BINFILE."
		        echo >&2 "Have you properly cloned umc repo with sub-modules?"
		fi

		echo "  - copying..." 
		cp -R $INSTALL_HOME/$BINFILE $LIBS_HOME/$TOOLDN

		echo "# SQL collector" >>$ENV_FILE
		echo "export SQLCOLLECTOR_HOME=\"$LIBS_HOME/sql-collector\"" >>$ENV_FILE
		echo "export PATH=\$SQLCOLLECTOR_HOME/bin/:\$PATH" >>$ENV_FILE
		echo "" >>$ENV_FILE

	else
		echo >&2 "  - SQL collector has already been installed in $LIBS_HOME/$TOOLDN, skipping."						
	fi
}

# INSTALL DMS COLLECTOR
install_dmscollector () {
	# binary file for dms collector
	BINFILE="dms-collector"
	TOOLDN="dms-collector"

	echo "* Installing DMS collector: $BINFILE" 

	if [ ! -d $LIBS_HOME/$TOOLDN ]; then

		# dms-collector should be in umc/varia/dms-collector/bin
		if [ ! -f $INSTALL_HOME/$BINFILE/bin/dms-collector ]; then
		        echo ""
		        echo >&2 "Cannot find dms-collector script in $INSTALL_HOME/$BINFILE."
		        echo >&2 "Have you properly cloned umc repo with sub-modules?"
		fi

		echo "  - copying..." 
		cp -R $INSTALL_HOME/$BINFILE $LIBS_HOME/$TOOLDN

		echo "# DMS collector" >>$ENV_FILE
		echo "export DMSCOLLECTOR_HOME=\"$LIBS_HOME/dms-collector\"" >>$ENV_FILE
		echo "export PATH=\$DMSCOLLECTOR_HOME/bin/:\$PATH" >>$ENV_FILE
		echo "" >>$ENV_FILE

	else
		echo >&2 "  - DMS collector has already been installed in $LIBS_HOME/$TOOLDN, skipping."						
	fi
}

# INSTALL INFLUXDB
install_influxdb () {
	# binary file for influxdb
	BINFILE="influxdb-1.6.1_linux_amd64.tar.gz"
	TOOLDN="influxdb-1.6.1-1"

	echo "* Installing influxdb: $BINFILE"

	if [ ! -d $LIBS_HOME/$TOOLDN ]; then
		# get influxdb installation binaries
		# check if it exsits in varia and download when it does not
		if [ ! -f $INSTALL_HOME/$BINFILE ]; then
			    echo "Influxdb installation binaries at $INSTALL_HOME/$BINFILE are not available."
			    echo "Trying to download..."

		        cd $INSTALL_HOME
		        wget --progress=bar:force --no-check-certificate $(cat $INSTALL_HOME/$BINFILE.download)

		        # check it was downloaded ok
		        if [ $? -ne 0 ]; then
			    	echo ""
			    	echo >&2 "The binary cannot be downloaded as per the link in $INSTALL_HOME/$BINFILE.download." 
			    	echo >&2 "Please check you network connection, check the link in the download file or download the file manually."
			    	exit 1
			    fi

			    echo "Influxdb binaries downloaded to $INSTALL_HOME/$BINFILE"
		fi

		# copy to libs directory
		echo "  - unpacking..." 
		cd $LIBS_HOME && tar xvzf $INSTALL_HOME/$BINFILE >>$INSTALL_LOG 2>&1

		# change the configuration 
		sed -i.bckp s#/var/lib/influxdb#$LIBS_HOME/$TOOLDN/var/influxdb#g $LIBS_HOME/$TOOLDN/etc/influxdb/influxdb.conf
		sed -i.bckp s/#.reporting-disabled.=.false/reporting-disabled=true/g $LIBS_HOME/$TOOLDN/etc/influxdb/influxdb.conf
		rm $LIBS_HOME/$TOOLDN/etc/influxdb/influxdb.conf.bckp
		echo "  - changed required configuration in $LIBS_HOME/$TOOLDN/etc/influxdb/influxdb.conf"

		# create influxd start up script
		echo "if [ \"\$(ps ax | grep influxdb | grep -v grep | awk '{ print \$1 }')\" != \"\" ]; then" >$LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh
		echo "   echo \"influxdb is already running!\"" >>$LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh
		echo "   exit 1" >>$LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh
		echo "fi" >>$LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh
		echo "" >>$LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh
		echo "$LIBS_HOME/$TOOLDN/usr/bin/influxd >$LIBS_HOME/$TOOLDN/var/log/influxdb/influxd.log 2>&1 &" >>$LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh
		echo "echo \"influxdb started, log is in $LIBS_HOME/$TOOLDN/var/log/influxdb/influxd.log\"" >>$LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh

		# create influxd stop script
		echo "if [ \"\$(ps ax | grep influxdb | grep -v grep | awk '{ print \$1 }')\" = \"\" ]; then" >$LIBS_HOME/$TOOLDN/usr/bin/stop-influxd.sh
		echo "   echo \"influxdb is not running!\"" >>$LIBS_HOME/$TOOLDN/usr/bin/stop-influxd.sh
		echo "   exit 1" >>$LIBS_HOME/$TOOLDN/usr/bin/stop-influxd.sh
		echo "fi" >>$LIBS_HOME/$TOOLDN/usr/bin/stop-influxd.sh
		echo "" >>$LIBS_HOME/$TOOLDN/usr/bin/stop-influxd.sh
		echo "kill \$(ps ax | grep influxdb | grep -v grep | awk '{ print \$1 }')" >>$LIBS_HOME/$TOOLDN/usr/bin/stop-influxd.sh

		chmod +x $LIBS_HOME/$TOOLDN/usr/bin/start-influxd.sh
		chmod +x $LIBS_HOME/$TOOLDN/usr/bin/stop-influxd.sh
		echo "  - influxdb setup completed, you can run it with start-influxd.sh and stop it with stop-influxd.sh"
		
		# environment variables
		echo "# influxdb" >>$ENV_FILE
		echo "export INFLUXDB_CONFIG_PATH=\"$LIBS_HOME/$TOOLDN/etc/influxdb/influxdb.conf\"" >>$ENV_FILE
		echo "export PATH=$LIBS_HOME/$TOOLDN/usr/bin:\$PATH" >>$ENV_FILE
		echo "" >>$ENV_FILE
	else
		echo >&2 "  - Influxdb has already been installed in $LIBS_HOME/$TOOLDN, skipping."						
	fi
}

# helper function to install a python library
install_pythonlib () {
	module="$1"
	version="$2"
	echo "  - Checking module $module..."
	python $INSTALL_HOME/../bin/checkModule.py $module
	if [ $? -ne 0 ]; then
		echo "  - Module $module is not installed."
		
		cd $INSTALL_HOME/python-libs
		archfile=$(find . | egrep "$module-$version\.(zip|tar\.gz)$" | head -1)
		
		# check that archive exists
		if [ "$archfile" = "" ]; then
			# retrieve url from pypi.org/simple
			echo "  - Retrieving the module archive URL..."
			url=$(wget -qO- https://pypi.org/simple/$module/ | egrep -o "\"https://.*$module-$version\.(tar\.gz|zip)[\#\=a-zA-Z0-9\-\_]+\"")
			
			if [ "$url" = "" ]; then
				echo >&2 "  - Cannot get an URL for module $module-$version. The module will not be installed!"
				echo >&2 "  - Try to download the module manually from https://pypi.org/simple/$module/ and run the installer again."
				return
			fi
			
			# download the archive
			echo "  - Downloading the module..."
			wget --progress=bar:force $(echo $url | cut -d "\"" -f 2) >/dev/null 2>&1 
			
			archfile=$(find . | egrep "$module-$version\.(zip|tar\.gz)$" | head -1)
			if [ "$archfile" = "" ]; then
				echo >&2 "  - Unable to download archive for module $module-$version. The module will not be installed!"
				echo >&2 "  - Try to download the module manually from https://pypi.org/simple/$module/ and run the installer again."
				return
			fi
			
		fi
			
		# unpack archive file
		echo "  - Unpacking $archfile..."		
		if [[ $archfile =~ tar\.gz$ ]]; then tar xvzf $archfile >>$INSTALL_LOG 2>&1; fi		
		if [[ $archfile =~ \.zip$ ]]; then unzip $archfile >>$INSTALL_LOG 2>&1; fi
			
		# go to module installation directory
		pwd=$(pwd)
		cd $module-* >>$INSTALL_LOG 2>&1

		# check that archive was possible to unpack
		if [ $? -ne 0 ]; then
			echo >&2 "  - Cannot unpack archive $archfile. The module $module will not be installed!"
			return
		fi
		
		# install locally
		mdir=$(pwd)
		echo "  - Installing $module locally..."
		python setup.py install --user >>$INSTALL_LOG 2>&1
		
		# check the result of setup
		if [ $? -ne 0 ]; then
			echo >&2 "  - The module $module was not installed successfully!"
		fi
		
		cd $pwd
		rm -fr $mdir
	else
		echo "  - Module $module has already been installed."		
	fi
}

# INSTALL INFLUXDB
install_influxdb_python () {
	source $ENV_FILE
	
	echo "* Installing python libraries for influxdb"
	
	# the following order of libraries reflects dependencies among the libraries
	install_pythonlib "setuptools" "39.2.0"
	install_pythonlib "setuptools_scm" "2.1.0"
	install_pythonlib "chardet" "3.0.4"
	install_pythonlib "pytz" "2018.4"
	install_pythonlib "idna" "2.5"
	install_pythonlib "certifi" "2018.4.16"
	install_pythonlib "six" "1.11.0"
	install_pythonlib "urllib3" "1.22"
	install_pythonlib "requests" "2.18.4"
	install_pythonlib "python-dateutil" "2.7.3"
	install_pythonlib "influxdb" "5.0.0"
	install_pythonlib "psutil" "5.4.6"	
	install_pythonlib "PyYAML" "3.12"	
	install_pythonlib "scandir" "1.9"	
}

# parse arguments
INSTALLIBS=""
PYTHON_ZLIB=true
for i in "$@"; do
	case $i in
	    --yes)
	    ALLYES="YES"
	    shift
	    ;;
	    --python)
	    INSTALLIBS="$INSTALLIBS python_"
	    shift 
	    ;;
			--no-python-zlib)
	    PYTHON_ZLIB=false
	    shift 
	    ;;
	    --jdk)
	    INSTALLIBS="$INSTALLIBS jdk"
	    shift 
	    ;;
	    --sqlcl)
	    INSTALLIBS="$INSTALLIBS sqlcl"
	    shift 
	    ;;
	    --sql-collector)
	    INSTALLIBS="$INSTALLIBS sqlcollector"
	    shift 
	    ;;
			--dms-collector)
	    INSTALLIBS="$INSTALLIBS dmscollector"
	    shift 
	    ;;
	    --influxdb)
	    INSTALLIBS="$INSTALLIBS influxdb_"
	    shift 
	    ;;
			--python-libs)
	    INSTALLIBS="$INSTALLIBS pythonlibs"
	    shift 
	    ;;
	    *)
	          show_help
	          exit
	    ;;
	esac
done

# install all if none is specified
if [ "$INSTALLIBS" == "" ]; then INSTALLIBS="ALL"; fi

mkdir -p $LIBS_HOME
echo "UMC libraries installation script"
echo "- Directory with installation binaries is in $INSTALL_HOME"
echo "- Libraries will be installed in "$LIBS_HOME""
echo "- Installation log will be in "$INSTALL_LOG""

while [ true ] && [ "$ALLYES" != "YES" ]; do
	echo ""
	read -p "Do you wish to continue?" yn
    case $yn in
        [Yy]* ) break;;    	
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

echo ""
echo "* Installing libraries to $LIBS_HOME..."

if [[ $INSTALLIBS =~ (.*"python_".*|ALL) ]] ; 					then install_python; fi
if [[ $INSTALLIBS =~ (.*"jdk".*|ALL) ]] ; 							then install_jdk; fi
if [[ $INSTALLIBS =~ (.*"sqlcl".*|ALL) ]] ; 						then install_sqlcl; fi
if [[ $INSTALLIBS =~ (.*"sqlcollector".*|ALL) ]] ; 			then install_sqlcollector; fi
if [[ $INSTALLIBS =~ (.*"dmscollector".*|ALL) ]] ; 			then install_dmscollector; fi
if [[ $INSTALLIBS =~ (.*"influxdb_".*|ALL) ]] ; 				then install_influxdb; fi
if [[ $INSTALLIBS =~ (.*"pythonlibs".*|ALL) ]] ; 				then install_influxdb_python; fi

chmod +x $ENV_FILE

echo "* Done"
echo ""

