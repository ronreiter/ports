import functools
import os
import signal
import webbrowser
from typing import Sequence

import rumps
import subprocess

rumps.debug_mode(True)


def get_proc_data_by_pid():
    proc_data = {}
    output = subprocess.check_output(["ps", "aux"]).decode("utf8").strip().split("\n")
    headers = output[0].split()
    lines = [{x[0]:x[1].replace("\\x20", " ") for x in zip(headers, l.split(maxsplit=len(headers)-1))} for l in output[1:]]
    for line in lines:
        proc_data[line['PID']] = line
    return proc_data

def get_ports() -> Sequence[dict[str]]:
    output = subprocess.check_output("lsof -iTCP -sTCP:LISTEN -n -P -R +c 100".split()).decode("utf8").strip().split("\n")
    headers = output[0].split()
    lines = [{x[0]:x[1].replace("\\x20", " ") for x in zip(headers, l.split())} for l in output[1:]]
    return lines


def apps_by_port():
    retval = {}
    for app in get_ports():
        port = int(app['NAME'].split(":")[1])
        if port not in retval:
            retval[port] = []
        retval[port].append(app)
    return retval


menu_by_port = {}

class PortsApp(rumps.App):
    def __init__(self):
        super().__init__("Ports")
        self.port_to_title = {}
        self.icon = 'icons/port-white.png'

    @rumps.timer(1)
    def on_tick(self, sender):
        ports = sorted(apps_by_port().items())
        proc_data = get_proc_data_by_pid()
        for port, app_data in ports:
            app_name = app_data[0]['COMMAND']
            self.port_to_title[port] = f"{port} - {app_name}"
            app_proc_data = proc_data[app_data[0]['PID']]
            icon_f = f"icons/{app_name.lower()}.png"
            if self.port_to_title[port] not in self.menu:
                print("found app in port %s" % port)
                menu_by_port[port] = (rumps.MenuItem(
                    title=self.port_to_title[port],
                    callback=functools.partial(self.click_app, port),
                    icon=icon_f if os.path.exists(icon_f) else "icons/port-white.png"
                ), [
                    rumps.MenuItem("PID: " + app_proc_data['PID']),
                    # rumps.MenuItem("CPU Usage: " + app_proc_data['%CPU'] + "%"),
                    # rumps.MenuItem("Memory Usage: " + app_proc_data['%MEM'] + "%"),
                    rumps.MenuItem("Command: " + app_proc_data['COMMAND']),
                    rumps.MenuItem("Terminate %s" % app_name, callback=functools.partial(self.terminate, port)),
                    rumps.MenuItem("Open Browser - %s" % app_name, callback=functools.partial(self.open, port)),
                ])
                self.menu.update([menu_by_port[port]])

        for port_to_remove in set(menu_by_port.keys()) - set([x[0] for x in ports]):
            if self.port_to_title[port_to_remove] in self.menu:
                del self.menu[self.port_to_title[port_to_remove]]



    def click_app(self, port, sender):
        print("Click", port, sender)
        webbrowser.open("http://localhost:%s" % port)

    def terminate(self, port, sender):
        print("Terminate", port, sender)
        apps = apps_by_port()[port]
        for app in apps:
            print("killing %s..." % app['PID'])
            os.kill(int(app['PID']), signal.SIGKILL)
            rumps.notification("Killed Process", None, "Killed process %s" % app['PID'])

    def open(self, port, sender):
        print("Open", port, sender)
        webbrowser.open("http://localhost:%s" % port)

if __name__ == '__main__':
    print('starting...')
    app = PortsApp()
    app.run()
