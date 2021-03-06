'''
Function : ENIQ PM Alarm
Version : V1.0
Date : 20170727
Author : laurance.gao@ericsson.com
Usage:  10,25,40,55 * * * * /usr/bin/python /eniq/home/dcuser/PMAlarm/pmalarm.py > /dev/null
InputFile: /eniq/home/dcuser/PMAlarm/sqlinput
Output: /eniq/home/dcuser/PMAlarm/<date>/<datetime-datetime>.log
'''

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import re
import pexpect

time_offset = 10
time_delay = 15
ROP = 15

UAS_IP = '10.217.12.87'
UAS_user = 'eric'
UAS_passwd = 'Supp0rt@eric'
dir = '/eniq/home/dcuser/PMAlarm'

time_structure = time.localtime(time.time() - time_offset*60 - time_delay*60)
sql_stoptime = time.strftime('%b %d %Y %I:%M%p', time_structure)
stamp_stoptime = time.strftime('%Y%m%d%H%M',time.localtime(time.mktime(time.strptime(sql_stoptime, '%b %d %Y %I:%M%p'))))
sql_starttime = time.strftime('%b %d %Y %I:%M%p', time.localtime(time.mktime(time.strptime(sql_stoptime, '%b %d %Y %I:%M%p')) - ROP*60))
stamp_starttime = time.strftime('%Y%m%d%H%M',time.localtime(time.mktime(time.strptime(sql_starttime, '%b %d %Y %I:%M%p'))))
date = stamp_starttime[:8]
file_stamp = stamp_starttime + '-' + stamp_stoptime

os.chdir(dir)
fin = open('sqlinput')
input = fin.readlines()
fin.close()
input[1] = re.sub(r'= ".*" and', '= "' + sql_starttime + '" and', input[1])
fout = open('sqlinput', 'w')
for line in input:
    fout.write(line)
fout.close()
if not os.path.exists(date):
    os.mkdir(date)
os.chdir(date)
os.system('/eniq/sybase_iq/OCS-15_0/bin/iqisql -Udc -Pdc -Sdwhdb -w1000 -i../sqlinput -o ' + file_stamp + '.log')

fin = open(file_stamp + '.log')
input = fin.readlines()
fin.close()

if len(input) > 4:
    try:
        telnet = pexpect.spawn('/usr/bin/telnet ' + UAS_IP)
        prompt = telnet.expect('login: ', timeout=5)
        telnet.sendline(UAS_user)
        telnet.expect('Password: ', timeout=5)
        telnet.sendline(UAS_passwd)
        telnet.expect('eric@uas2> ', timeout=5)
        for line in input[2:len(input)-2]:
            DATETIME_ID = re.findall(r'\s+(\w.*\w)\s+SubNetwork=ONRM_ROOT_MO', line)
            print DATETIME_ID[0]
            SN = re.findall(r'\s+(SubNetwork=ONRM_ROOT_MO.*[A-Z]+)\s+', line)
            print SN[0]
            EUtranCellTDD = re.findall(r'MeContext=.+[A-Z]+\s+(\d+)\s+', line)
            print EUtranCellTDD[0]
            pmRrcConnMax = re.findall(r'\s+(\d+)\.00000000\s+', line)
            print pmRrcConnMax[0]
            AccessRate = re.findall(r'\s+(\d+\.\d\d)\d+\s+$', line)
            print AccessRate[0]
            cmd = '/opt/ericsson/bin/fmx_event -e "PMAlarm" -m "PMAlarm" SP="Performance KPI exceeds threshold" OOR="' + SN[0] + '"' + ' severity=3 PT="Cell ' + EUtranCellTDD[0] + ' RRC.ConnMax is ' + pmRrcConnMax[0] + ', RadioAccessRate is ' + AccessRate[0] +'% in ROP ' + DATETIME_ID[0] + '"'
            telnet.sendline(cmd)
            telnet.expect('eric@uas2> ', timeout=10)
            print telnet.before
            print telnet.after
                
    except Exception,e:
        print Exception,':',e 
    finally:
        telnet.close()

else:
    print "No data in database!"
