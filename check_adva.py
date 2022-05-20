"""
ADVA VPS Monitoring
2019-01-115 Remi Verchere <remi.verchere@axians.com> - Copy/Paste from Eric Belhomme F5 scripts
2022-04-12- Razcall edit correction on variable condition
Published under MIT license
"""
from __future__ import division
import argparse, netsnmp
import struct, datetime

__author__ = 'Remi VERCHERE'
__contact__ = 'remi.verchere@axians.com'
__license__ = 'MIT'


retText = [
    'OK',
    'WARNING',
    'CRITICAL',
    'UNKNOWN',
]

alarmSeverity = [
    'none',
    'intermediate',
    'critical',
    'major',
    'minor',
    'warning',
    'cleared',
    'notReported'
]


def print_longHelp():
    print("""
ADVA FSP Nagios plugin
================================================

-= modes =-
-----------
* help - This help
* temperature - get temperature

    """)
    print('-= temperature =-\n--------------------\n' + get_temperature.__doc__)
    print('-= volt =-\n--------------------\n' + get_psuvoltin.__doc__)
    print('-= amperes =-\n--------------------\n' + get_amperes.__doc__)
    print('-= alarms -\n--------------------\n' + get_alarms.__doc__)

    print("---\nCopyright {author} <{authmail}> under {license} license".format(
        author = __author__, authmail = __contact__, license = __license__))
    exit(0)

def _check_val(val, warn, crit, inv=0):
    """
Check value threshold
    """
    if inv:
        if int(val) < int(crit):
           return 2
        elif int(val) < int(warn):
            return 1
        else:
            return 0
    else:
        if int(val) > int(crit):
            return 2
        elif int(val) > int(warn):
            return
        else:
            return 0

def get_alarms(perfdata=False):
    retcode = 3
    alarm = 0
    vals = snmpSession.walk( netsnmp.VarList(
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.7.4.5.1.2.1'),
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.7.4.5.1.3.1'),
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.7.4.5.1.4.1'),
    ))
    if vals:
        for alarmEqptSeverity, alarmEqptAffect, alarmEqptTimeStamp in tuple( vals[i:i+3] for i in range(0, len(vals), 3)):
            if int(alarmEqptSeverity) < 5: # TrapAlarmSeverity (INTEGER) {indeterminate (1), critical (2), major (3), minor (4), warning (5), cleared (6), notReported (7) }
                message.append("Alarm {} found".format(alarmSeverity[int(alarmEqptSeverity)]))
                alarm += 1
        if alarm > 0:
            retcode = 2
        else:
            retcode = 0
            message.append("No major errors found")
    else:
        retcode = 0
        message.append("No errors found")
    return retcode

def get_amperes(perfdata=False):
    """
Check Amperes
    """
    retcode = 0
    vals = snmpSession.walk( netsnmp.VarList(
        #netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.2.4.2.2.1.1'),     # currentDiagnosticsAmpere
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.11.1.2.1.1.1.6.1'),     # currentDiagnosticsAmpere
        #netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.2.4.2.2.1.2'),     # currentDiagnosticsUpperThres
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.11.1.2.2.1.1.3.1'),     # currentDiagnosticsUpperThres
    ))
    if vals:
        a = 1
        for ampere, amperemax in tuple( vals[i:i+2] for i in range(0, len(vals), 2)):
           retcode = _check_val(int(ampere), int(amperemax), int(amperemax))
           message.append("Current Ampere {} mA\n".format(ampere))
           if args.perfdata:
               perfmsg.append("'mamps_{}'={};;{}".format(a, ampere, amperemax))
           a += 1
    else:
        retcode = 3
        message.append('Failed to retrieve voltage data')

    return retcode

def get_psuvoltin(perfdata=False):
    """
Check PSU Volt Input
    """
    retcode = 0
    warn = '200000'
    if isinstance(args.warning,str) and args.warning is not None:
        warn = int(args.warning)
    crit = '150000'
    if isinstance(args.critical,str) and args.critical is not None:
        crit = int(args.critical)

    vals = snmpSession.walk( netsnmp.VarList(
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.11.1.2.1.1.1.7.1'),     # PSU Volt Input
    ))
    if vals:
        v = 1
        for volt, in tuple( vals[i:i+1] for i in range(0, len(vals), 1)):
           retcode = _check_val(int(volt), int(warn), int(crit), 1)
           message.append("Input Voltage {} mV\n".format(volt))
           if args.perfdata:
               perfmsg.append("'mvolts_{}'={};{};{}".format(v, volt, warn, crit))
           v += 1
    else:
        retcode = 3
        message.append('Failed to retrieve voltage data')

    return retcode

def get_temperature(perfdata=False):
    """
    """
    vals = snmpSession.walk( netsnmp.VarList(
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.7.10.1.1.6.1.1'),     # Name
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.7.10.1.1.7.1.1'),     # Type
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.11.1.2.1.1.1.5.1.1'),     # Temperature
        netsnmp.Varbind('.1.3.6.1.4.1.2544.1.11.11.1.2.2.1.1.1.1.1'),     # Temperature max
    ))
    if vals:
        retcode = 0
        for name, t, temp, tempmax in tuple( vals[i:i+4] for i in range(0, len(vals), 4)):
           #print "Name: %s, Type: %s, Temperature: %.2f, Max: %.2f " % (name, t, (int(temp) / 10), (int(tempmax) / 10))
           retcode = _check_val(int(temp), int(tempmax), int(tempmax))
           message.append("Temperature for {} is {}°c\n".format(name, (int(temp)/10)))
           if args.perfdata:
               perfmsg.append("'temp_{}'={};;{}".format(name, (int(temp) / 10), (int(tempmax) / 10)))
    else:
        retcode = 3
        message.append('Failed to retrieve temperature data')

    return retcode


##### Main starts here
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Nagios check for ADVA FSP Device')
    parser.add_argument('-H', '--hostname', type=str, help='hostname or IP address', required=True)
    parser.add_argument('-C', '--community', type=str, help='SNMP community (currently only v2c)', required=True)
    parser.add_argument('-m', '--mode', type=str, help='Operational mode',
        choices = [
            'help',
            'temperature',
            'voltage',
            'amperage',
            'alarms',
        ],
        required=True)
    parser.add_argument('-x', '--arg1', type=str, help='optional argument 1 (eg. vs or node name, health flags)', default=None)
    parser.add_argument('-p', '--perfdata', help='enable perfdata', action='store_true')
    parser.add_argument('-w', '--warning', type=str, nargs='?', help='warning trigger', default=10)
    parser.add_argument('-c', '--critical', type=str, nargs='?', help='critical trigger', default=6)

    args = parser.parse_args()
    retcode = 3
    message = []
    perfmsg = []

    snmpSession = netsnmp.Session(Version=2, DestHost=args.hostname, Community=args.community)

    if args.mode == 'help':
        print_longHelp()
    elif args.mode =='temperature':
        retcode = get_temperature(args.perfdata)
    elif args.mode =='voltage':
        retcode = get_psuvoltin(args.perfdata)
    elif args.mode =='amperage':
        retcode = get_amperes(args.perfdata)
    elif args.mode =='alarms':
        retcode = get_alarms(args.perfdata)

    print("{}: ".format(retText[retcode]) + "".join(message))
    if args.perfdata and len(perfmsg):
        print('|' + " ".join(perfmsg))

    exit(retcode)

