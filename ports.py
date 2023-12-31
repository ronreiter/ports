# TODOs:
# Make the app icon right
# make a website / README.md to download the ports app

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
        try:
            port = int(app['NAME'].replace('[::1]', '127.0.0.1').split(":")[1])
        except Exception as e:
            print(e)
            continue
        if port not in retval:
            retval[port] = []
        retval[port].append(app)
    return retval


menu_by_port = {}


class PortsApp(rumps.App):
    def __init__(self):
        super().__init__("Ports", icon='icons/port.png')
        self.port_to_title = {}
        self.app_icons = {}
        self.first_time = True

        self.menu = [rumps.MenuItem("About Ports", callback=self.about)]

    def about(self, sender):
        result = rumps.alert("About Ports", "Ports gives you full visibility and control for which "
                                   "ports are being opened and closed by which applications.\n"
                                   "Ports was developed by Ron Reiter.\n"
                                   "To contribute, please go to:\n"
                                   "https://github.com/ronreiter/ports", ok="Go to GitHub", cancel="Done")

        if result:
            webbrowser.open("https://github.com/ronreiter/ports")

    @rumps.timer(5)
    def on_tick(self, sender):
        ports = sorted(apps_by_port().items())
        proc_data = get_proc_data_by_pid()
        for port, app_data in ports:
            app_name = app_data[0]['COMMAND']
            app_proc_data = proc_data[app_data[0]['PID']]

            app_part = [x for x in app_proc_data['COMMAND'].split("/") if x.endswith(".app")]
            if app_part:
                self.port_to_title[port] = f"{port} - {app_name} ({app_part[0]})"
            else:
                self.port_to_title[port] = f"{port} - {app_name}"

            if app_name in self.app_icons:
                # use cached
                icon_f = self.app_icons[app_name]
            else:
                if ".app" in app_proc_data['COMMAND']:
                    res_dir = app_proc_data['COMMAND'].split(".app")[0] + ".app/Contents/Resources/"
                    icons_in_res_dir = [x for x in os.listdir(res_dir) if x.endswith(".icns")]
                    icon_f = res_dir + icons_in_res_dir[0] if icons_in_res_dir else None
                else:
                    icon_f = f"icons/{app_name.lower()}.png"

                self.app_icons[app_name] = icon_f

            if self.port_to_title[port] not in self.menu:
                if not self.first_time:
                    rumps.notification("Open Port Discovered", None, "Port %s was just opened by application %s" % (port, app_name))
                menu_by_port[port] = (rumps.MenuItem(
                    title=self.port_to_title[port],
                    callback=functools.partial(self.click_app, port),
                    icon=icon_f if os.path.exists(icon_f) else "icons/port-white.png"
                ), [
                    rumps.MenuItem("PID: " + app_proc_data['PID']),
                    rumps.MenuItem("Command: " + app_proc_data['COMMAND']),
                    rumps.MenuItem("Terminate %s" % app_name, callback=functools.partial(self.terminate, port)),
                    rumps.MenuItem("Open Browser: http://localhost:%s" % port, callback=functools.partial(self.open, port)),
                ])
                self.menu.update([menu_by_port[port]])

        for port_to_remove in set(menu_by_port.keys()) - set([x[0] for x in ports]):
            if self.port_to_title[port_to_remove] in self.menu:
                rumps.notification("Closed Port Discovered", None,
                   "Port %s was just closed" % port_to_remove)
                del self.menu[self.port_to_title[port_to_remove]]

        self.first_time = False

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
