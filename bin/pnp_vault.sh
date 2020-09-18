#!/bin/bash

pnp_root=~/.pnp
pnp_vault_debug=0
pnp_always_replace=1
lock_fd=8

#
# helper
# 

function get_seed() {
    local privacy="$1"

    local seed_script=$(echo $(hostname -f)$0$(stat -c %i%g $0) | sha256sum | cut -f1 -d' ')
    local seed_user=$(echo $(hostname -f)$(whoami)$(stat -c %i%g ~) | sha256sum | cut -f1 -d' ')
    local seed_host=$(echo $(hostname -f)$(stat -c %i%g /etc)  | sha256sum | cut -f1 -d' ')

    case $privacy in
        script)
            if [ -f $0 ]; then
                local seed=$seed_host$seed_script
            else
                >&2 echo 'Warning. Script level privacy chosen, but running from shell. Falling to user level privacy.'
                local seed=$seed_host$seed_user
            fi
            ;;
        user)
            local seed=$seed_host$seed_user
            ;;
        host)
            local seed=$seed_host
            ;;
        *)
            >&2 echo 'Error. Privacy level not known. Falling to user level privacy.'
            local seed=$seed_host$seed_user
            ;;
    esac
    [ $pnp_vault_debug -gt 0 ] && echo "$privacy, $seed"

    echo $seed
}

function rollback_work() {

    exec 8>$pnp_root/secret.lock
    flock -x -w 5 $lock_fd

    if [ -d $pnp_root/secret.prev ]; then
        rm -rf $pnp_root/secret
        mv $pnp_root/secret.prev $pnp_root/secret

        rm -rf $pnp_root/secret.tx
        rm -rf $pnp_root/secret.delete
    fi

    # remove lock
    flock -u $lock_fd
    rm $pnp_root/secret.lock
}

#
# main
#

function read_secret() {
    local key="$1"
    local privacy="$2"

    if [ -z "$key" ]; then
        >&2 echo "usage: read_secret key user|host|script"
        return 1
    fi

    umask 077

    [ ! -d $pnp_root ] && mkdir -p $pnp_root

    if [ -z "$internal_read" ]; then
        # rollback broken work
        rollback_work

        # lock dataset for changes
        exec 8>$pnp_root/secret.lock
        flock -x -w 5 $lock_fd
        if [ $? -ne 0 ]; then
            echo "Error. Other process keeps dataset."
            return 127
        fi
    fi

    : ${privacy:=user}

    #
    local seed=$(get_seed $privacy)

    local lookup_code=$(echo $(hostname)\_$key | sha256sum | cut -f1 -d' ')
    [ $pnp_vault_debug -gt 0 ] && echo $lookup_code


    local element_pos=0
    local lookup_code_element=.
    local lookup_result=true
    unset value
    while [ ! -z "$lookup_code_element" ]; do

        local lookup_code_element=${lookup_code:$element_pos:1}
        if [ ! -z "$lookup_code_element" ]; then
            local lookup_code_element_value=$((16#$lookup_code_element))
            local seed_element=${seed:$lookup_code_element_value:1}
            [ $pnp_vault_debug -gt 0 ] && echo $element_pos, $lookup_code_element, $lookup_code_element_value, $seed_element
            
            local lookup_code_seed=$(echo $seed_element$element_pos$lookup_code | sha256sum | cut -f1 -d' ')
            [ $pnp_vault_debug -gt 0 ] && echo $lookup_code_seed

            if [ -z "$internal_read" ]; then
                local secret_repo=$pnp_root/secret
            else
                local secret_repo=$internal_read
            fi

            if [ $pnp_always_replace -eq 1 ]; then 
                local kv=$(grep $lookup_code_seed $secret_repo/$seed_element 2>/dev/null | head -1)    
            else
                local kv=$(grep $lookup_code_seed $secret_repo/$seed_element 2>/dev/null | tail -1)
            fi

            if [ -z "$kv" ]; then
                if [ -z "$value" ]; then
                    [ $pnp_vault_debug -gt 0 ] && echo "Not found"
                    lookup_result=false
                else
                    lookup_result=true
                    [ $pnp_vault_debug -gt 0 ] && echo "Value: $value"
                fi
                break
            else
                local value_element=$(echo "$kv" | cut -d' ' -f2)
                local value="$value$value_element"
            fi
            element_pos=$(( $element_pos + 1 ))
        fi
    done
    
    if [ -z "$internal_read" ]; then
        # remove lock
        flock -u $lock_fd
        rm $pnp_root/secret.lock
    fi

    if [ "$lookup_result" = "true" ]; then
        echo "$value"
        return 0
    else
        echo ''
        return 1
    fi
}

function save_secret() {
    local key="$1"
    local value="$2"
    local privacy="$3"

    if [ -z "$key" ]; then
        >&2  echo "usage: save_secret key value user|host|script"
        return 1
    fi

    if [ -z "$value" ]; then
        >&2 echo "usage: save_secret key value user|host|script"
        return 1
    fi

    umask 077

    [ ! -d $pnp_root ] && mkdir -p $pnp_root

    if [ ! -d $pnp_root ]; then 
        >&2 echo "Note: cfg directory does not exist. Creating $pnp_root"
        mkdir $pnp_root
    fi

    if [ "$(stat -c %a $pnp_root)" != "700" ]; then
        >&2 echo "Note: Wrong cfg directory access rights. Fixing $pnp_root to 0700"
        chmod 0700 $pnp_root
    fi

    if [ ! -d $pnp_root/secret ]; then
        mkdir -p $pnp_root/secret
    fi        

    # rollback broken work
    rollback_work

    # lock dataset for changes
    exec 8>$pnp_root/secret.lock
    flock -x -w 5 $lock_fd
    if [ $? -ne 0 ]; then
        echo "Error. Other process keeps dataset."
        return 127
    fi

    rm -rf $pnp_root/secret.tx
    mkdir -p $pnp_root/secret.tx
    
    if [ -d $pnp_root/secret ]; then
        if [ $(ls $pnp_root/secret | wc -l) -gt 0 ]; then
            cp $pnp_root/secret/* $pnp_root/secret.tx
        fi

        rm -rf $pnp_root/secret.prev
        mv $pnp_root/secret $pnp_root/secret.prev
    fi

    : ${privacy:=user}

    if [ $pnp_always_replace -eq 1 ]; then
        internal_read=$pnp_root/secret.tx
        delete_secret $key $privacy
        unset internal_read
    fi

    local seed=$(get_seed $privacy)

    local lookup_code=$(echo $(hostname)\_$key | sha256sum | cut -f1 -d' ')
    [ $pnp_vault_debug -gt 0 ] && echo $lookup_code

    local element_pos=0
    local lookup_code_element=.
    while [ ! -z "$lookup_code_element" ]; do
        local lookup_code_element=${lookup_code:$element_pos:1}
        if [ ! -z "$lookup_code_element" ]; then
            local lookup_code_element_value=$((16#$lookup_code_element))
            local seed_element=${seed:$lookup_code_element_value:1}

            [ $pnp_vault_debug -gt 0 ] && echo $element_pos, $lookup_code_element, $lookup_code_element_value, $seed_element
            
            local lookup_code_seed=$(echo $seed_element$element_pos$lookup_code | sha256sum | cut -f1 -d' ')
            local value_element=${value:$element_pos:1}

            [ $pnp_vault_debug -gt 0 ] && echo $value_element

            if [ ! -z "$value_element" ]; then
                echo "$lookup_code_seed $value_element" >> $pnp_root/secret.tx/$seed_element
            else
                break
            fi
            element_pos=$(( $element_pos + 1 ))
        fi
    done

    #
    # verification
    #
    internal_read=$pnp_root/secret.tx
    local read_value=$(read_secret $key $privacy)
    unset internal_read
    if [ "$value" != "$read_value" ]; then
        echo "Error writing key due to low entropy. Retry with different key. This key is lost."
    
        echo "$key : $value vs. $read_value" 

        rm -rf $pnp_root/secret.tx
        rm -rf $pnp_root/secret
        mv $pnp_root/secret.prev $pnp_root/secret

        # remove lock
        flock -u $lock_fd
        rm $pnp_root/secret.lock
        return 10
    else

        rm -rf $pnp_root/secret.prev
        rm -rf $pnp_root/secret
        mv $pnp_root/secret.tx $pnp_root/secret

        # shuffle entries to eliminate entry order
        if [ $pnp_always_replace -eq 1 ]; then

            rm -rf $pnp_root/secret.shuffle
            mkdir $pnp_root/secret.shuffle

            for secret_file in $pnp_root/secret/*; do
                shuf $secret_file > $pnp_root/secret.shuffle/$(basename $secret_file)
            done
            rm -rf $pnp_root/secret
            mv $pnp_root/secret.shuffle $pnp_root/secret
        
        fi

        # remove lock
        flock -u $lock_fd
        rm $pnp_root/secret.lock
    fi

}


function delete_secret() {
    local key="$1"
    local privacy="$2"

    if [ -z "$key" ]; then
        >&2  echo "usage: delete_secret key  user|host|script"
        return 1
    fi

    umask 077

    [ ! -d $pnp_root ] && mkdir -p $pnp_root

    if [ ! -d $pnp_root ]; then 
        >&2 echo "Note: cfg directory does not exist. Creating $pnp_root"
        mkdir $pnp_root
    fi

    if [ "$(stat -c %a $pnp_root)" != "700" ]; then
        >&2 echo "Note: Wrong cfg directory access rights. Fixing $pnp_root to 0700"
        chmod 0700 $pnp_root
    fi

    if [ ! -d $pnp_root/secret ]; then
        mkdir -p $pnp_root/secret
    fi        

    if [ -z "$internal_read" ]; then

        # rollback broken work
        rollback_work

        # lock dataset for changes
        exec 8>$pnp_root/secret.lock
        flock -x -w 5 $lock_fd
        if [ $? -ne 0 ]; then
            echo "Error. Other process keeps dataset."
            return 127
        fi
    fi

    : ${privacy:=user}

    local seed=$(get_seed $privacy)

    local lookup_code=$(echo $(hostname)\_$key | sha256sum | cut -f1 -d' ')
    [ $pnp_vault_debug -gt 0 ] && echo $lookup_code

    rm -rf $pnp_root/secret.delete
    mkdir $pnp_root/secret.delete
    if [ -z "$internal_read" ]; then
        secret_repo=$pnp_root/secret
    else   
        secret_repo=$internal_read
    fi

    if [ -d $secret_repo ]; then
        if [ $(ls $secret_repo | wc -l) -gt 0 ]; then
            cp $secret_repo/* $pnp_root/secret.delete
        fi
    fi

    local element_pos=0
    local lookup_code_element=.
    while [ ! -z "$lookup_code_element" ]; do
        local lookup_code_element=${lookup_code:$element_pos:1}

        if [ ! -z "$lookup_code_element" ]; then
            local lookup_code_element_value=$((16#$lookup_code_element))
            local seed_element=${seed:$lookup_code_element_value:1}

            [ $pnp_vault_debug -gt 0 ] && echo $element_pos, $lookup_code_element, $lookup_code_element_value, $seed_element
            
            local lookup_code_seed=$(echo $seed_element$element_pos$lookup_code | sha256sum | cut -f1 -d' ')

            if [ -f $pnp_root/secret.delete/$seed_element ]; then
                cat $pnp_root/secret.delete/$seed_element | sed "/^$lookup_code_seed/d"  > $pnp_root/secret.delete/$seed_element.new
                mv $pnp_root/secret.delete/$seed_element.new $pnp_root/secret.delete/$seed_element
            fi

            element_pos=$(( $element_pos + 1 ))
        fi
    done

    rm -rf $secret_repo
    mv $pnp_root/secret.delete $secret_repo

    if [ -z "$internal_read" ]; then
        # remove lock
        flock -u $lock_fd
        rm $pnp_root/secret.lock
    fi
}

#
# 
#
function usage() {
    cat <<EOF
usage: pnp_vault save|read|delete key [value] [privacy]

, where
privacy user|host|script with default user

EOF
}

function __main__() {
    operation=$1; shift

    case $operation in
        save)
            save_secret $@
            ;;
        read)
            read_secret $@
            ;;
        delete)
            delete_secret $@
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# prevent from staring main in source mode
[ -f $0 ] && __main__ $@
