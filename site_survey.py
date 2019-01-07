#!/usr/bin/env python3

import operator
import re
import subprocess
import time

import iw_parse


class SiteSurvey:
    def __init__(self):
        self._controlmaster = None
        self._cm_options = [
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ControlMaster=auto',
            '-o', 'ControlPath ~/.ssh/.%C',
        ]

    def __del__(self):
        self.disconnect()

    def connect(self, s):
        if not self._controlmaster:
            self._controlmaster = subprocess.Popen(['sshpass',
                    '-p', s.pw, 'ssh'] + self._cm_options + [
                    '-o', 'LogLevel=error', '-MNn', '-l', s.user, s.host])

    def disconnect(self):
        if self._controlmaster:
            self._controlmaster.terminate()
            self._controlmaster = None

    def scan(self, s):
        try:
            if s.remote:
                self.connect(s)
                time.sleep(0.5)
            uptime = {}
            cells_all = {}
            while True:
                bssids = set()
                screen = []
                time.sleep(0.5)
                screen.append('\033c')
                if s.remote:
                    res = subprocess.check_output(['ssh'] +
                            self._cm_options + [
                            '-l', s.user, s.host,
                            'iwlist', s.intf, 'scan'])
                else:
                    res = iw_parse.call_iwlist(s.intf)
                cells = iw_parse.get_parsed_cells(res.decode().split('\n'))
                cells.sort(key=operator.itemgetter('Quality'))

                screen.append('BSSID              SSID                              Freq  Chan  Encr  Qual  Sig  Noise  Mode')
                for cell in cells:
                    line = '{}  {:<32}  {:<5}  {:>3}  {}  {:>3}%  {:>3}  {:>5}  {:<8}'.format(cell['Address'], cell['Name'], cell['Frequency'], cell['Channel'], cell['Encryption'], cell['Quality'], cell['Signal Level'], cell['Noise Level'], cell['Mode'])
                    bssid = cell['Address']
                    bssids.add(bssid)
                    if bssid in uptime:
                        uptime[bssid] = uptime[bssid] + 1
                    else:
                        uptime[bssid] = 0
                    cells_all[bssid] = line
                for bssid in cells_all:
                    line = cells_all[bssid]
                    line = line + '  ' + str(uptime[bssid])
                    if not bssid in bssids:
                        line = '\033[33m' + line + '\033[0m'
                    if s.ssid and line.find(s.ssid) != -1:
                        line = '\033[36m' + line + '\033[0m'
                    screen.append(line)
                for bssid in (uptime.keys() - bssids):
                    uptime[bssid] = 0

                print('\n'.join(screen))
        except KeyboardInterrupt:
            print('')
            pass
        finally:
            self.disconnect()

if __name__ == "__main__":
    import settings

    sur = SiteSurvey()
    sur.scan(settings.s)
