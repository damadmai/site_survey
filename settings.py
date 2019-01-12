import argparse

class ArgumentHandler():
    def __init__(self):
        self._args = None
        self.fields = {
            's': 'Name',
            'r': 'Quality',
            'c': 'Channel',
            'f': 'Frequency',
            'e': 'Encryption',
            'b': 'Address',
            'p': 'Signal Level',
            'f': 'Noise Level',
            'b': 'Bit Rates',
            'm': 'Mode',
        }

    @property
    def intf(self):
        return self._args.interface

    @property
    def ssid(self):
        return self._args.ssid

    @property
    def remote(self):
        return self._args.remote

    @property
    def user(self):
        return self._args.user

    @property
    def password(self):
        return self._args.password

    @property
    def address(self):
        return self._args.address

    @property
    def openonly(self):
        return self._args.openonly

    @property
    def order(self):
        return self.fields[self._args.order]

    @property
    def invert(self):
        return self._args.invert

    def get_arguments(self):
        p = argparse.ArgumentParser()

        p.add_argument('-i', '--interface', type=str, default='ath0', help='Network interface')
        p.add_argument('-s', '--ssid', type=str, help='Regular expression for SSID highlighting')
        p.add_argument('-r', '--remote', action='store_true', help='If set attempt SSH connection to specified host')
        p.add_argument('-u', '--user', type=str, default='ubnt', help='SSH user')
        p.add_argument('-p', '--password', type=str, default='ubnt', help='SSH password')
        p.add_argument('-a', '--address', type=str, default='192.168.1.20', help='SSH host address')
        p.add_argument('-n', '--openonly', action='store_true', help='Only show unencrypted open nets')
        p.add_argument('-o', '--order', type=str, default='r', choices=list(self.fields.keys()), help='Specify field for ordering, Quality is default, options: {}'.format(self.fields))
        p.add_argument('-v', '--invert', action='store_true', help='Invert sorting order')
        self._args = p.parse_args()

