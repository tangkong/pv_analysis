import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

# Set up for gathering information on the available PV's in LCLS
# Basically mimic find_pv and take its sources


logger = logging.getLogger(__file__)


def initialize_db(db_path: Path = None):
    """ Initialize the sql database, deleting an old one if it exists in the path"""
    if db_path is None:
        db_path = Path(__file__).parent.parent / 'data' / 'LCLS_PV.db'
    print(db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.executescript(
        '''
        DROP TABLE IF EXISTS pv_db1;
        CREATE TABLE pv_db1 (
            pv TEXT NOT NULL,
            source_pvlist TEXT,
            query_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            IOC TEXT,
            IOC_PV TEXT
        );
        '''
    )

    conn.commit()
    conn.close()


def read_iocmanager_cfg(cfg_path: Path):
    """ 
    Returns a ... config
    just execs the file, so it must be python syntax I guess
    """

    with open(cfg_path, 'r') as f:
        # if file[0].startswith('allow_console'):
        #     file.pop(0)
            
        # # COMMITHOST
        # commit_line = [line for line in file if line.startswith('COMMITHOST')][0]
        # commit_host = commit_line.split(' = ')[1].strip('"\'')

        # # hosts
        # host_section = re.findall(r'hosts *= *\[([^][]*)\]')[0]
        # host_list = [s.strip('\n "\'') for s in host_section.split(',')]
        # host_list = [h for h in host_list if h]


        # # procmgr_config
        # procmgr_section = re.findall(r'procmgr_config *= *((.|\n)*)', file)[0][0]
        # cfg_sections = re.findall(r'\{([^{}]*)\}', procmgr_section)
        # procmgr_data = []
        config = {'procmgr_config': None, 'hosts': None, 'dir':'dir',
                  'id':'id', 'cmd':'cmd', 'flags':'flags', 'port':'port', 'host':'host',
                  'disable':'disable', 'history':'history', 'delay':'delay', 'alias':'alias',
                  'hard':'hard' }
        
        # original iocmanager does weird exec shenanigans, unless I want to build
        # an actual parser, I'm just going to copy it

        exec(f.read(), {}, config)

        return config        


def gather_ioc_info(dump_path = None):
    pv_lists = Path('/reg/d/iocData/').glob('ioc*/iocInfo/IOC.pvlist')

    ## Map ioc to host and boot directory
    ioc_info = dict()
    for pv_list in pv_lists:
        ioc = pv_list.parent.parent.name
        ioc_info[ioc] = dict()

    iocmgr_cfgs = Path('/reg/g/pcds/pyps/config/').glob('*/iocmanager.cfg')
    for cfg_path in iocmgr_cfgs:
        config = read_iocmanager_cfg(cfg_path)
        for proc_cfg in config['procmgr_config']:
            try:
                proc_ioc_info = ioc_info[proc_cfg['id']]
            except KeyError:
                logger.warning(f'{proc_cfg["id"]} missing from initial pvlist')
                # ioc not found in initial pvlist search.  Skip?...
                continue

            proc_ioc_info['host'] = proc_cfg.get('host', 'None')
            proc_ioc_info['port'] = proc_cfg.get('port', 'None')
            proc_ioc_info['dir'] = proc_cfg.get('dir', 'None')
            proc_ioc_info['alias'] = proc_cfg.get('alias', 'None')
            proc_ioc_info['iocmgr_cfg'] = str(cfg_path)

    if dump_path:
        with open(dump_path, 'w') as f:
            json.dump(ioc_info, f, indent=4)

    return ioc_info


def pull_source(
    connection: sqlite3.Connection,
    ioc_info: Optional[Dict[str, Any]] = None,
    dry_run: bool = True
):
    """ Gather data from source 1, /reg/d/iocData/ioc*/iocInfo/IOC.pvlist """
    # grab cursor

    pv_lists = Path('/reg/d/iocData/').glob('ioc*/iocInfo/IOC.pvlist')
    pv_regex = re.compile(r'^\w+(:\w+)+(\.\w+)*$')

    # host_list = Path('/reg/d/iocCommon/hosts/').glob('ioc*/startup.cmd')
    hard_ioc_lists = Path('/reg/d/iocCommon').glob('/hioc/ioc*/startup.cmd')
    

    # # look for hard ioc, hioc should match other IOC's
    # for hioc in hard_ioc_lists:
    #     hioc_name = str(hioc.parent.name)
    #     startup = str(hioc)
    #     with open(hioc, 'r') as f:
    #         for line in f.readlines():
    #             re_result = re.match('^chdir\((.*)\)', line)
    #             if re_result:
    #                 boot_dir = re_result[1].strip(' "')

    pv_lists = Path('/reg/d/iocData/').glob('ioc*/iocInfo/IOC.pvlist')
    for pv_list in pv_lists:
        # look for ioc PV host.  IOC in 
        ioc_name = pv_list.parent.parent.name
        all_pv_data = []
        with open(pv_list, 'r') as f:
            # line format: PVNAME:SOMETHING:ELSE, "recordtype"
            for line in f:
                pv_data = []
                pv = line.split(', ')[0]
                # verify format of pv is correct
                if not pv_regex.match(pv):
                    continue
                
                pv_data.extend([pv, str(pv_list), ioc_name])

                # To apply to all the lines matching ioc
                if pv.endswith(':UPTIME'):
                    ioc_pv = pv.removesuffix(':UPTIME')

                all_pv_data.append(pv_data) 
        

        # curr_ioc_info = ioc_info[ioc_name]

        print(f'Parsed file ({pv_list}), found ({len(all_pv_data)}) PVs')
        # print(f"...Updating {ioc_name}")
        if not dry_run:
            cursor = connection.cursor()
            cursor.executemany(
                """
                INSERT INTO pv_db1 (pv, source_pvlist, IOC, query_time)
                VALUES (?,?,?,CURRENT_TIMESTAMP)
                """, all_pv_data
            )

            cursor.execute(
                "UPDATE pv_db1 SET "
                f"  IOC_PV = \'{ioc_pv}\' "
                # f"  ALIAS = \'{curr_ioc_info.get('alias', 'None')}\', "
                # f"  DIR = \'{curr_ioc_info.get('dir', 'None')}\', "
                # f"  source_iocmgrcfg = \'{curr_ioc_info.get('iocmgr_cfg', 'None')}\', "
                # f"  HOST = \'{curr_ioc_info.get('host', 'None')}\', "
                # f"  PORT = \'{curr_ioc_info.get('port', 'None')}\' "
                f"WHERE IOC = \'{ioc_name}\';"
            )

            connection.commit()
            # connection.close()
