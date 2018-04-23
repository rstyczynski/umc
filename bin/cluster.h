#---
#--- Cluster functions library
#---

umc_version=0.1

function cfgCluster {
   clusterName=$1

   # configure user params
   if [ ! -f ~/etc/umc_cluster_$1.cfg ]; then
      echo Error! Cluster configuration does not found!
   else
       . ~/etc/umc_cluster_$1.cfg

       if [ ! -z "$OHS" ]; then
          echo "OHS servers: " $OHS
       else
          echo "OHS not defined."
       fi
       
       if [ ! -z "$SOA" ]; then
            echo "SOA servers: $SOA" 
          
            if [ ! -z "$SOA_ADMIN" ]; then
              echo "SOA_ADMIN admin: $SOA_ADMIN" 
            else
              echo "SOA ADMIN not defined."
            fi

            if [ ! -z "$SOA_ADMIN_URL" ]; then
              echo "SOA_ADMIN_URL admin: $SOA_ADMIN_URL" 
            else
              echo "SOA ADMIN URL not defined."
            fi

            if [ ! -z "$SOA_CFG" ]; then
              echo "SOA CFG: >>>"
              echo "$SOA_CFG"
              echo "<<<"
            else
              echo "SOA CFG not defined."
            fi

       else
          echo "SOA not defined."
       fi

       if [ ! -z "$OSB" ]; then
            echo "OSB servers: $OSB" 

            if [ ! -z "$OSB_ADMIN" ]; then
              echo "OSB_ADMIN admin: $SOA_ADMIN" 
            else
              echo "OSB ADMIN not defined."
            fi

            if [ ! -z "$OSB_ADMIN_URL" ]; then
              echo "OSB_ADMIN_URL admin: $SOA_ADMIN_URL" 
            else
              echo "OSB ADMIN URL not defined."
            fi

            if [ ! -z "$OSB_CFG" ]; then
              echo "OSB_CFG: >>>"
              echo "$OSB_CFG"
              echo "<<<"
            else
              echo "OSB CFG not defined."
            fi

       else
          echo "OSB not defined."
       fi

       if [ ! -z "$TEST" ]; then
          echo "TEST servers: " $OHS
       else
          echo "TEST not defined."
       fi
       
       HOSTS="$OHS $SOA $OSB $TEST"
       
       echo 
       echo "Envirionment configured for the cluster."
   fi

}

function getPassword {

    if [ ! -f ~/.umc/pwd ]; then
        read -p "Enter password:" -s pwd
        echo -n $pwd > ~/.umc/pwd
	chmod 600 ~/.umc/pwd
        unset pwd
        echo
    fi

}

function delPassword {

    if [ ! -f ~/.umc/pwd ]; then
        rm ~/.umc/pwd
    fi

}

function copyCfg {
    #
    # --- Copy configuration to Middleware Admin hosts
    #
   
    getPassword

    error=NO
    echo -n "Copy SOA cfg..."
    ssh $SOA_ADMIN "if [ ! -d etc ]; then mkdir etc; fi"
    echo "$SOA_CFG" | ssh $SOA_ADMIN "cat >etc/umc.cfg"
    if [ $? -eq 0 ]; then
        echo "Done."
    else
        echo "Error."
        error=YES
    fi
    
    echo -n "Copy OSB cfg..."
    ssh $OSB_ADMIN "if [ ! -d etc ]; then mkdir etc; fi"
    echo "$OSB_CFG" | ssh $OSB_ADMIN "cat >etc/umc.cfg"
    if [ $? -eq 0 ]; then
        echo "Done."
    else
        echo "Error."
        error=YES
    fi
    
    if [ "$error" == NO ]; then
        echo Done.
    else
        echo Done with errors.
    fi


    #
    # prepare etc 
    #
    for host in $SOA_ADMIN $OSB_ADMIN; do

    commandToExecute="
    chmod -R a+xr etc
     "

    if [ $host != $(hostname -s) ]; then
      ssh $host "$commandToExecute"
    else
       eval $commandToExecute
    fi

    done

    #
    # add etc to oracle
    #    
    for host in $SOA_ADMIN $OSB_ADMIN; do

    commandToExecute="bash -c '

    ln -s $PWD/etc ~/etc

    '"
    
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi

    done


}


function removeUmc {
    #
    # --- Copy configuration to Middleware Admin hosts
    #
   
    getPassword

    #
    # prepare etc 
    #
    for host in $SOA_ADMIN $OSB_ADMIN; do

    commandToExecute="
    rm etc/umc.cfg
    rmdir etc

    mkdir DELETE.ME
    mv umc DELETE.ME/umc.$RANDOM.$PID
    rm -rf /tmp/umc

     "

    if [ $host != $(hostname -s) ]; then
      ssh $host "$commandToExecute"
    fi

    done

    #
    # add etc to oracle
    #    
    for host in $SOA_ADMIN $OSB_ADMIN; do

    commandToExecute="bash -c '

    rm ~/etc
    rm -rf /tmp/umc

    '"
    
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    fi

    done


}


function distributeUmc {
    #
    # --- Copy umc to all hosts
    #
    for host in $HOSTS; do

    if [ $host != $(hostname -s) ]; then
      scp -r $umcRoot $host:$(dirname $umcRoot)
    fi

    done
}

function prepareUmc {
    #
    # --- Change permission to very wide to make oracle user able to use umc files.
    #
    for host in $HOSTS; do

    commandToExecute="
    chmod -R a+xr umc
    ls -lh

    mkdir -p /tmp/umc;
    chmod 777 /tmp/umc;
    "

    if [ $host != $(hostname -s) ]; then
      ssh $host "$commandToExecute"
    else
       eval $commandToExecute
    fi

    done


}
 
function measureLinux {
    #
    # --- Linux
    #
    
    if [ -z "$HOSTS" ]; then
        echo "Error: HOSTS are not configured."
        return 1
    fi
            
    DURATION_OS=$(( $DURATION * $DURATION_BASE / $INTERVAL_OS ))

    for host in $HOSTS; do

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    nohup umc_collectAll.sh $INTERVAL_OS $DURATION_OS \"vmstat
    free
    top
    uptime
    meminfo
    netstattcp
    ifconfig
    iostat\" –nonblocking --testId=$TESTID --logDir=/tmp/umc >/dev/null 2>&1 &

    '"
    
    if [ $host != $(hostname -s) ]; then
      ssh $host "$commandToExecute"
    else
      eval "$commandToExecute"
    fi

    done
}
 
 
function measureSOA {
    #
    # --- SOA
    #
    
    if [ -z "$SOA" ]; then
        echo "Error: SOA not configured."
        return 1
    fi
        
    host=$SOA_ADMIN
    DURATION_WLS=$(( $DURATION * $DURATION_BASE / $INTERVAL_WLS ))

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    nohup umc_collectAll.sh $INTERVAL_WLS $DURATION_WLS \"wls --subsystem=general --url=$SOA_ADMIN_URL
    wls --subsystem=jmsruntime --url=$SOA_ADMIN_URL
    wls --subsystem=jmsserver --url=$SOA_ADMIN_URL
    wls --subsystem=datasource --url=$SOA_ADMIN_URL
    wls --subsystem=channel --url=$SOA_ADMIN_URL
    soabindings --url=$SOA_ADMIN_URL \" -–nonblocking --testId=$TESTID --logDir=/tmp/umc >/dev/null 2>&1 &

    '"

    getPassword

    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi
}
 
 
function measureOSB {
    #
    # --- OSB
    #
    
    if [ -z "$OSB" ]; then
        echo "Error: OSB not configured."
        return 1
    fi
    
    host=$OSB_ADMIN
    DURATION_WLS=$(( $DURATION * $DURATION_BASE / $INTERVAL_WLS ))

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    nohup umc_collectAll.sh $INTERVAL_WLS $DURATION_WLS \"wls --subsystem=general --url=$OSB_ADMIN_URL
    wls --subsystem=jmsruntime --url=$OSB_ADMIN_URL
    wls --subsystem=jmsserver --url=$OSB_ADMIN_URL
    wls --subsystem=datasource --url=$OSB_ADMIN_URL 1
    wls --subsystem=channel --url=$OSB_ADMIN_URL1
    businessservice --url=$OSB_ADMIN_URL --metrics_type=SERVICE
    businessservice --url=$OSB_ADMIN_URL --metrics_type=URI
    businessservice --url=$OSB_ADMIN_URL --metrics_type=OPERATION \" -–nonblocking --testId=$TESTID --logDir=/tmp/umc >/dev/null 2>&1 &

    '"

    getPassword
        
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi
}
 
 
function stopMeasurements {
    #
    # --- Stop
    #

    if [ -z "$HOSTS" ]; then
        echo "Error: HOSTS are not configured."
        return 1
    fi
        
    for host in $HOSTS; do

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    umc_stopAll.sh;

    '"

    getPassword
        
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi

    if [ $host != $(hostname -s) ]; then
      ssh $host $commandToExecute"
    else
      eval "$commandToExecute"
    fi

    done
}
 
 
function getDataFiles {
    #
    # --- Change permission
    #
    
    if [ -z "$HOSTS" ]; then
        echo "Error: HOSTS are not configured."
        return 1
    fi
        
    for host in $HOSTS; do

    commandToExecute="bash -c '

    . umc/bin/umc.h;
    cd /tmp;
    chmod -R 777 umc;
    cd umc
    ls -Rlh

    '"

    getPassword
        
    if [ $host != $(hostname -s) ]; then
      cat ~/.umc/pwd | ssh $host sudo -kS su oracle -c  "$commandToExecute"
    else
      cat ~/.umc/pwd | sudo -kS su oracle -c "$commandToExecute"
    fi

    done


    #
    # --- tar and copy
    #
    DATE=$(date +"%d-%m-%y")
    mkdir /tmp/umc_archive

    for host in $HOSTS; do

    commandToExecute="bash -c \"

    rm umc*.tar.gz
    tar czf umc\_$TESTID_$DATE\_\$(hostname -s).tar.gz /tmp/umc/$TESTID

    \""

    if [ $host != $(hostname -s) ]; then
      ssh $host "$commandToExecute"
      scp $host:umc\_$TESTID_$DATE\_$host.tar.gz /tmp/umc_archive
    else
      cat ~/.umc/pwd | sudo -kS su $(whoami) -c "$commandToExecute"
      cp umc\_$TESTID_$DATE\_$host.tar.gz /tmp/umc_archive
    fi

    done
    chmod -R 777 /tmp/umc_archive
}


echo Universal Metrics Collector Cluster initialized.

