#!/usr/bin/env python3

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
                    '-p', s.password, 'ssh'] + self._cm_options + [
                    '-o', 'LogLevel=error', '-MNn', '-l', s.user, s.address])

    def disconnect(self):
        if self._controlmaster:
            self._controlmaster.terminate()
            self._controlmaster = None

    def scan(self, s):
        try:
            if s.remote:
                self.connect(s)
                time.sleep(1)
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
                            '-l', s.user, s.address,
                            'iwlist', s.intf, 'scan'])
                else:
                    res = iw_parse.call_iwlist(s.intf)
                cells = iw_parse.get_parsed_cells(res.decode().split('\n'))

                screen.append('BSSID              SSID                              Freq  Chan  Encr  Qual  Sig  Noise  Mode    Uptime')
                for cell in cells:
                    bssid = cell['Address']
                    bssids.add(bssid)
                    if bssid in uptime:
                        uptime[bssid] = uptime[bssid] + 1
                    else:
                        uptime[bssid] = 0
                    cells_all[bssid] = cell
                cells_sorted = sorted(list(cells_all.values()), key=lambda k: int(k['Quality']), reverse=True)
                for cell in cells_sorted:
                    if s.openonly and cell['Encryption'] != 'Open':
                        continue
                    bssid = cell['Address']
                    line = self._format_cell(cell)
                    line = line + '{:>6}'.format(uptime[bssid])
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

    def _format_cell(self, cell):
        return '{}  {:<32}  {:<5}  {:>3}  {:>4}  {:>3}%  {:>3}  {:>5}  {:<8}'.\
        format(
            cell['Address'], cell['Name'], cell['Frequency'],
            cell['Channel'], cell['Encryption'], cell['Quality'],
            cell['Signal Level'], cell['Noise Level'], cell['Mode']
        )

if __name__ == "__main__":
    from settings import ArgumentHandler

    argument_handler = ArgumentHandler()
    argument_handler.get_arguments()

    sur = SiteSurvey()
    sur.scan(argument_handler)
