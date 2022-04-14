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
        self.title = "🔌"

    @rumps.timer(1)
    def on_tick(self, sender):
        ports = sorted(apps_by_port().items())
        proc_data = get_proc_data_by_pid()
        for port, app_data in ports:
            app_name = app_data[0]['COMMAND']
            app_proc_data = proc_data[app_data[0]['PID']]
            icon_f = f"icons/{app_name.lower()}.png"
            if port not in menu_by_port:
                menu_by_port[port] = (rumps.MenuItem(
                    title=f"{port} - {app_name}",
                    callback=functools.partial(self.click_app, port),
                    icon=icon_f if os.path.exists(icon_f) else None
                ), [
                    rumps.MenuItem("PID: " + app_proc_data['PID']),
                    rumps.MenuItem("CPU Usage: " + app_proc_data['%CPU'] + "%"),
                    rumps.MenuItem("Memory Usage: " + app_proc_data['%MEM'] + "%"),
                    rumps.MenuItem("Command: " + app_proc_data['COMMAND']),
                    rumps.MenuItem("Terminate", callback=functools.partial(self.terminate, port)),
                    rumps.MenuItem("Open Browser", callback=functools.partial(self.open, port)),
                ])

        try:
            self.menu = menu_by_port.values()
        except Exception as e:
            pass


    def click_app(self, port, sender):
        print("Click", port, sender)

    def terminate(self, port, sender):
        print("Terminate", port, sender)
        apps = apps_by_port()[port]
        for app in apps:
            print("killing %s..." % app['PID'])
            os.kill(int(app['PID']), signal.SIGSTOP)

    def open(self, port, sender):
        print("Open", port, sender)
        webbrowser.open("http://localhost:%s" % port)

if __name__ == '__main__':
    print('starting...')
    app = PortsApp()
    app.run()
