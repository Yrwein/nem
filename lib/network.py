
import re
import subprocess
import threading


class AccessPoint:
    def __init__(self, ssid, quality):
        self.ssid = ssid
        self.quality = quality


def output(cmd):
    op = subprocess.check_output(cmd, shell=True)
    if op:
        return op.strip()


def card_info():
    return output('lspci | grep -i "wifi\|wlan\|wireless"')


def iface_name():
    return output('ls /sys/class/net | cat | grep wl')


def iface_up(iface_name):
    subprocess.call('ifconfig {} up'.format(iface_name), shell=True)


def access_points(iface_name):
    access_points = []
    ssid = None
    quality = None
    ap_search = output('iwlist ' + iface_name + ' scan')
    for line in ap_search.splitlines():
        line = line.strip()
        if line.startswith('Cell ') and ssid is not None and quality is not None:
            ap = AccessPoint(ssid, quality)
            access_points.append(ap)
        elif line.startswith('Cell '):
            ssid = None
            quality = None
        elif line.startswith('ESSID'):
            # format: ESSID:"UPC5774344"
            ssid_match = re.search(r'ESSID:"(.+)"', line)
            if ssid_match is not None:
                ssid = ssid_match.group(1)
            else:
                print('error parsing ssid: ' + line)
        elif line.startswith('Quality'):
            # format: Quality=64/70    Signal level=-46 dBm
            quality_match = re.search(r'Quality=(.+)/70', line)
            if quality_match is not None:
                quality = quality_match.group(1)
            else:
                print('error parsing quality: ' + line)
    if line.startswith('Cell ') and ssid is not None and quality is not None:
        ap = AccessPoint(ssid, quality)
        access_points.append(ap)
    return access_points


def generate_wpa_conf(ssid, passphrase, wpa_conf_filename):
    wpa_conf = output(' wpa_passphrase {} {}'.format(ssid, passphrase))
    with open(wpa_conf_filename, 'w') as wpa_conf_file:
        wpa_conf_file.write(wpa_conf)


def killall_wpa_supplicants():
    subprocess.call('killall -9 wpa_supplicant', shell=True)


def connect(iface_name, wpa_conf_filename):
    def wpa_connection_target(iface_name, wpa_conf_filename):
        subprocess.call('wpa_supplicant -i ' + iface_name + ' -c ' + wpa_conf_filename + ' -D wext', shell=True)
    wpa_connection = threading.Thread(target=wpa_connection_target, args=(iface_name, wpa_conf_filename))
    wpa_connection.start()


def dhcp(iface_name):
    subprocess.call('dhclient ' + iface_name, shell=True)


def dns():
    with open('/etc/resolv.conf', 'w') as resolv_conf:
        resolv_conf.write('nameserver 8.8.8.8')


def test():
    subprocess.call('ping google.com -c 4', shell=True)
