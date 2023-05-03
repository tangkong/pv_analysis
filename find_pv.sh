find_pv () 
{ 
    if [ $# -eq 0 ]; then
        echo Usage: find_pv pv_name [pv_name2 ...];
        echo This script will search for each specified EPICS PV in:;
        echo "  ${IOC_DATA}/ioc*/iocInfo/IOC.pvlist";
        echo "";
        echo Then it looks for the linux host or hard IOC hostname in:;
        echo "  ${IOC_COMMON}/hioc/ioc*/startup.cmd";
        echo "If no host is found, the IOC will not autoboot after a power cycle!";
        echo "";
        echo Finally it looks for the boot directory in:;
        echo "  ${IOC_COMMON}/hioc/<ioc-name>/startup.cmd";
        echo "";
        echo "Hard IOC boot directories are shown with the nfs mount name.";
        echo "Typically this is /iocs mounting ${PACKAGE_SITE_TOP}/epics/ioc";
        return 1;
    fi;
    for pv in $*;
    do
        echo PV: $pv;
        ioc_list=`/bin/egrep -l -e "$pv" ${IOC_DATA}/ioc*/iocInfo/IOC.pvlist | /bin/cut -d / -f5`;
        for ioc in $ioc_list;
        do
            echo "      IOC:            $ioc";
            ioc_pv=`/bin/egrep UPTIME ${IOC_DATA}/$ioc/iocInfo/IOC.pvlist | /bin/sed -e "s/:UPTIME.*//"`;
            if (( ${#ioc_pv} == 0 )); then
                echo "  IOC_PV:         Not found!";
            else
                echo "  IOC_PV:         $ioc_pv";
            fi;
            hioc_list=`/bin/egrep -l -e "$ioc" ${IOC_COMMON}/hioc/ioc*/startup.cmd | /bin/cut -d / -f6`;
            if (( ${#hioc_list} )); then
                for hioc in $hioc_list;
                do
                    echo "      HIOC:           $hioc";
                    echo "      STARTUP:        ${IOC_COMMON}/hioc/$hioc/startup.cmd";
                    boot_list=`/bin/egrep -w -e "^chdir" ${IOC_COMMON}/hioc/$hioc/startup.cmd | /bin/cut -d \" -f2`;
                    for d in $boot_list;
                    do
                        echo "  BOOT_DIR:       $d";
                    done;
                done;
            fi;
            ${PYPS_SITE_TOP}/apps/ioc/latest/find_ioc --name $ioc;
        done;
    done
}