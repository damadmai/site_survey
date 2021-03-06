#!/usr/bin/env python3

import re
import subprocess
import threading
import time

import iw_parse


class SiteSurveyError(Exception):
    pass


class SiteSurvey:
    def __init__(self):
        self._controlmaster = None
        self._cm_options = [
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ControlMaster=auto',
            '-o', 'ControlPath=~/.ssh/.%C',
        ]

    def __del__(self):
        self.disconnect()

    def connect(self, s):
        if not self._controlmaster:
            self._controlmaster = subprocess.Popen(['sshpass',
                    '-p', s.password, 'ssh'] + self._cm_options + [
                    '-o', 'LogLevel=error', '-MNn', '-l',
                    s.user, s.address, '-p', s.port])

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
            event = threading.Event()
            while True:
                bssids = set()
                screen = []
                timer = threading.Timer(s.time, event.set)
                timer.start()
                screen.append('\033c')
                if s.remote:
                    try:
                        res = subprocess.check_output(['ssh'] +
                                self._cm_options + [
                                '-l', s.user, s.address, '-p', s.port,
                                'iwlist', s.intf, 'scan'])
                    except subprocess.CalledProcessError:
                        raise SiteSurveyError('Could not connect via SSH')
                else:
                    res = iw_parse.call_iwlist(s.intf)
                if not res:
                    raise SiteSurveyError('Scan failed, maybe wrong interface')
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
                if s.order in ['Frequency', 'Channel', 'Quality', 'Signal Level', 'Noise Level']:
                    key = lambda k: float(k[s.order])
                else:
                    key = lambda k: k[s.order]
                cells_sorted = sorted(list(cells_all.values()), key=key, reverse=s.invert)
                for cell in cells_sorted:
                    if s.openonly and cell['Encryption'] != 'Open':
                        continue
                    bssid = cell['Address']
                    line = self._format_cell(cell)
                    line = line + '{:>6}'.format(int(uptime[bssid] * s.time))
                    if not bssid in bssids:
                        line = '\033[33m' + line + '\033[0m'
                    if s.ssid and s.ssid in line:
                        line = '\033[36m' + line + '\033[0m'
                    screen.append(line)
                for bssid in (uptime.keys() - bssids):
                    uptime[bssid] = 0

                print('\n'.join(screen))
                event.wait()
                event.clear()
        except SiteSurveyError as ex:
            print('Error: {}'.format(ex))
        except KeyboardInterrupt:
            print('')
            timer.cancel()
            event.set()
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
