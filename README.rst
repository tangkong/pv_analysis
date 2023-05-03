======================
LCLS EPICS PV Analysis
======================

Don't look at this I'm shy.  This code is very gross.

Methods
=======

Gathering PV Information
------------------------

Here we largely base our efforts on the fabled ``find_pv`` command, which leverages several
data sources to gather IOC information for a specific PV.

These sources are:

#. /reg/d/iocData/ioc*/iocInfo/IOC.pvlist
    * This file has the all the PV's for a given IOC.  Notably fields may not be listed.
#. /reg/g/pcds/pyps/config/*/iocmanager.cfg
    * IOCManager configs hold information on the IOC's used by a hutch/area.  
    * hosts used in that area
    * A list of ioc information dictionaries
    * in the ``find_ioc`` command, this is raw ``exec``'d, in order to load it into python. 

Other sources
/reg/d/iocCommon/{hosts, hioc}/ioc*/startup.cmd
- look for linux host or IOC host name
Source 3: /reg/d/iocCommon/{hioc, sioc}/<ioc-name>/startup.cmd
- Looks for linux host of IOC host name

Aggregation strategy
--------------------
Table 1: PV's and the IOC they are associated with
Table 2: IOC information, keys are ioc_name

Table1.IOC will align with Table2.ioc_name (primary key)


Looking for Patterns
--------------------