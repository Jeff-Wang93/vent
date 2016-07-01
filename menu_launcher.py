#!/usr/bin/env python2.7

import ConfigParser
import curses
import os
import sys
import termios
import tty


from subprocess import call, check_output, PIPE, Popen

screen = curses.initscr()
curses.noecho()
curses.cbreak()
curses.start_color()
screen.keypad(1)

curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_WHITE)
h = curses.color_pair(1)
n = curses.A_NORMAL

MENU = "menu"
COMMAND = "command"
EXITMENU = "exitmenu"
INFO = "info"
INFO2 = "info2"
SETTING = "setting"
INPUT = "input"
DISPLAY = "display"

# path that exists on the iso
collectors_dir = "/var/lib/docker/data/collectors"
core_dir = "/var/lib/docker/data/core"
plugins_dir = "/var/lib/docker/data/plugins/"
template_dir = "/var/lib/docker/data/templates/"
vis_dir = "/var/lib/docker/data/visualization"

def update_images():
    images = check_output(" docker images | awk \"{print \$1}\" | grep / ", shell=True).split("\n")
    for image in images:
        image = image.split("  ")[0]
        if "core/" in image or "visualization/" in image or "collectors/" in image:
            if not os.path.isdir("/var/lib/docker/data/"+image):
                os.system("docker rmi "+image)
        else:
            if not os.path.isdir("/var/lib/docker/data/plugins/"+image):
                os.system("docker rmi "+image)

# Allows for acceptance of single char before terminating
def getch():
    fd = sys.stdin.fileno()
    settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, settings)
    return ch

# Will wait for user input before clearing stdout
def confirm():
    while getch():
        break

"""
Retrieves all plugins by namespace; e.g. - features/tcpdump || features/hexparser
Note returns a dict of format: {'namespace': [p1, p2, p3, ...], 'namespace2': [p1, p2, p3, ...]}
!! TODO - Namespace conflicts are possible and might result in some issues here.
"""
def get_installed_plugins():
    p = {}
    try:
        # Get all namespaces
        namespaces = [ namespace for namespace in os.listdir(plugins_dir) if os.path.isdir(os.path.join(plugins_dir, namespace)) ]

        # For each namespace, retrieve all plugins and index by namespace
        for namespace in namespaces:
            p[namespace] = [ plugin for plugin in os.listdir(plugins_dir+namespace) if os.path.isdir(os.path.join(plugins_dir+namespace, plugin)) ]
    except:
        with open("/tmp/error.log", "a+") as myfile:
            myfile.write("Error in get_installed_plugins: ", sys.exc_info())
        myfile.close()
        pass

    return p

# Retrieves installed collectors by category: active, passive, or both for all
def get_installed_collectors(c_type):
    c = []
    try:
        # Get all collectors
        collectors = [ collector for collector in os.listdir(collectors_dir) if os.path.isdir(os.path.join(collectors_dir, collector)) ]

        # Filter by passive/active/all
        if c_type == "passive":
            c = [ collector for collector in collectors if "passive-" in collector ]
        elif c_type == "active":
            c = [ collector for collector in collectors if "active-" in collector ]
        elif c_type == "all":
            c = collectors
        else:
            with open("/tmp/error.log", "a+") as myfile:
                myfile.write("Error in get_installed_collectors: ", "Invalid collector parameter: ", c_type)
            myfile.close()
    except:
        with open("/tmp/error.log", "a+") as myfile:
            myfile.write("Error in get_installed_collectors: ", sys.exc_info())
        myfile.close()
        pass

# Retrieves plugins that have been enabled in config
def get_enabled_plugins():
    mode_enabled = {}
    core_enabled = {}
    collector_enabled = {}
    vis_enabled = {}
    template_enabled = {}
    p = {}

    return p

"""
Takes in a dict of all installed plugins (see get_installed_plugins())
and a dict of all enabled_plugins (see get_enabled_plugins()).
Returns a MENU dict of plugins that have not been built.
"""
def get_unbuilt_plugins(installed_plugins, enabled_plugins):
    # TODO
    return

# Displays status of all running, not running/built, not built, and disabled plugins
def get_plugin_status():
    running = []
    nrbuilt = []
    notbuilt = []
    disabled = []
    installed = {}
    p = {}

    try:
        # Retrieves running or restarting docker containers and returns a list of "containeridimagename"; i.e. - running
        running = check_output(" { docker ps -a -f status=running & docker ps -a -f status=restarting; } | grep '/' | awk \"{print \$2\$1}\" ", shell=True).split("\n")

        # Retrieves docker containers with status exited, paused, dead, created as "containeridimagename"; i.e. - not running
        nrbuilt = check_output(" { docker ps -a -f status=created & docker ps -a -f status=exited & docker ps -a -f status=paused & docker ps -a -f status=dead; } | grep '/' | awk \"{print \$2\$1}\" ", shell=True).split("\n")
        # !! TODO - Append get_installed_plugins("all"), convert to dict first?
        installed = get_installed_plugins()
        enabled = get_enabled_plugins()

        # with open("/tmp/installed.log", "a+") as myfile:
        #     for namespace in installed:
        #         myfile.write("Namespace: "+namespace+" = [")
        #         for plugin in installed[namespace]:
        #             myfile.write(plugin+", ")
        #         myfile.write("]")
        # myfile.close()

        # !! TODO - Enabled/Disabled Plugins
        # !! TODO - Not built plugins
        p['title'] = 'Plugin Status'
        p['subtitle'] = 'Choose a category...'
        p_running = [ {'title': x, 'type': 'INFO', 'command': '' } for x in running if x != ""]
        p_nrbuilt = [ {'title': x, 'type': 'INFO', 'command': '' } for x in nrbuilt if x != ""]
        p['options'] = [ { 'title': "Running", 'subtitle': "Currently running...", 'type': MENU, 'options': p_running },
                         { 'title': "Not Running/Built", 'subtitle': "Built but not currently running...", 'type': MENU, 'options': p_nrbuilt }
                        ]
    except:
        pass

    return p

# Retrieves all installed plugin repos; e.g - vent-network
def get_installed_plugin_repos(m_type, command):
    try:
        p = {}
        p['type'] = MENU
        if command=="remove":
            command1 = "python2.7 /data/plugin_parser.py remove_plugins "
            p['title'] = 'Remove Plugins'
            p['subtitle'] = 'Please select a plugin to remove...'
            p['options'] = [ {'title': name, 'type': m_type, 'command': '' } for name in os.listdir("/var/lib/docker/data/plugin_repos") if os.path.isdir(os.path.join('/var/lib/docker/data/plugin_repos', name)) ]
            for d in p['options']:
                with open("/var/lib/docker/data/plugin_repos/"+d['title']+"/.git/config", "r") as myfile:
                    repo_name = ""
                    while not "url" in repo_name:
                        repo_name = myfile.readline()
                    repo_name = repo_name.split("url = ")[-1]
                    d['command'] = command1+repo_name
        elif command=="update":
            command1 = "python2.7 /data/plugin_parser.py remove_plugins "
            command2 = " && python2.7 /data/plugin_parser.py add_plugins "
            p['title'] = 'Update Plugins'
            p['subtitle'] = 'Please select a plugin to update...'
            p['options'] = [ {'title': name, 'type': m_type, 'command': '' } for name in os.listdir("/var/lib/docker/data/plugin_repos") if os.path.isdir(os.path.join('/var/lib/docker/data/plugin_repos', name)) ]
            for d in p['options']:
                with open("/var/lib/docker/data/plugin_repos/"+d['title']+"/.git/config", "r") as myfile:
                    repo_name = ""
                    while not "url" in repo_name:
                        repo_name = myfile.readline()
                    repo_name = repo_name.split("url = ")[-1]
                    d['command'] = command1+repo_name+command2+repo_name
        else:
            p['title'] = 'Installed Plugins'
            p['subtitle'] = 'Installed Plugins:'
            p['options'] = [ {'title': name, 'type': m_type, 'command': '' } for name in os.listdir("/var/lib/docker/data/plugin_repos") if os.path.isdir(os.path.join('/var/lib/docker/data/plugin_repos', name)) ]
        return p

    except:
        pass

def run_plugins(action):
    modes = []
    try:
        config = ConfigParser.RawConfigParser()
        config.read(template_dir+'modes.template')
        plugin_array = config.options("plugins")
        plugins = {}
        for plug in plugin_array:
            plugins[plug] = config.get("plugins", plug)

        for plugin in plugins:
            if plugin == "core" or plugin == "visualization":
                p = {}
                try:
                    config = ConfigParser.RawConfigParser()
                    config.read(template_dir+plugin+'.template')
                    plugin_name = config.get("info", "name")
                    p['title'] = plugin_name
                    p['type'] = INFO2
                    p['command'] = 'python2.7 /data/template_parser.py '+plugin+' '+action
                    modes.append(p)
                except:
                    # if no name is provided, it doesn't get listed
                    pass
        try:
            config = ConfigParser.RawConfigParser()
            config.read(template_dir+'core.template')
            try:
                passive = config.get("local-collection", "passive")
                if passive == "on":
                    p = {}
                    p['title'] = "Local Passive Collection"
                    p['type'] = INFO2
                    p['command'] = 'python2.7 /data/template_parser.py passive '+action
                    modes.append(p)
            except:
                pass
            try:
                active = config.get("local-collection", "active")
                if active == "on":
                    p = {}
                    p['title'] = "Local Active Collection"
                    p['type'] = INFO2
                    p['command'] = 'python2.7 /data/template_parser.py active '+action
                    modes.append(p)
            except:
                pass
        except:
            pass
        if len(modes) > 1:
            p = {}
            p['title'] = "All"
            p['type'] = INFO2
            p['command'] = 'python2.7 /data/template_parser.py all '+action
            modes.append(p)
    except:
        print "unable to get the configuration of modes from the templates.\n"

    # make sure that vent-management is running
    result = check_output('/bin/sh /data/bootlocal.sh'.split())
    print result

    return modes

def update_plugins():
    modes = []
    try:
        for f in os.listdir(template_dir):
            if f.endswith(".template"):
                p = {}
                p['title'] = f
                p['type'] = SETTING
                p['command'] = 'python2.7 /data/suplemon/suplemon.py '+template_dir+f
                modes.append(p)
    except:
        print "unable to get the configuration templates.\n"
    return modes

def get_param(prompt_string):
    curses.echo()
    screen.clear()
    screen.border(0)
    screen.addstr(2, 2, prompt_string)
    screen.refresh()
    input = screen.getstr(10, 10, 150)
    curses.noecho()
    return input

def runmenu(menu, parent):
    if parent is None:
        lastoption = "Exit"
    else:
        lastoption = "Return to %s menu" % parent['title']

    optioncount = len(menu['options'])

    pos=0
    oldpos=None
    x = None

    while x != ord('\n'):
        if pos != oldpos:
            oldpos = pos
            screen.border(0)
            screen.addstr(2,2, menu['title'], curses.A_STANDOUT)
            screen.addstr(4,2, menu['subtitle'], curses.A_BOLD)

            for index in range(optioncount):
                textstyle = n
                if pos==index:
                    textstyle = h
                if menu['options'][index]['type'] == INFO:
                    if "|" in menu['options'][index]['command']:
                        cmds = menu['options'][index]['command'].split("|")
                        i = 0
                        while i < len(cmds):
                            c = cmds[i].split()
                            if i == 0:
                                cmd = Popen(c, stdout=PIPE)
                            elif i == len(cmds)-1:
                                result = check_output(c, stdin=cmd.stdout)
                                cmd.wait()
                            else:
                                cmd = Popen(c, stdin=cmd.stdout, stdout=PIPE)
                                cmd.wait()
                            i += 1
                    else:
                        result = check_output((menu['options'][index]['command']).split())
                    screen.addstr(5+index,4, "%s - %s" % (menu['options'][index]['title'], result), textstyle)
                elif menu['options'][index]['type'] == INFO2:
                    screen.addstr(5+index,4, "%s" % (menu['options'][index]['title']), textstyle)
                else:
                    screen.addstr(5+index,4, "%d - %s" % (index+1, menu['options'][index]['title']), textstyle)
            textstyle = n
            if pos==optioncount:
                textstyle = h
            screen.addstr(6+optioncount,4, "%d - %s" % (optioncount+1, lastoption), textstyle)
            screen.refresh()

        x = screen.getch()

        # !! TODO hack for now, long term should probably take multiple character numbers and update on return
        num_options = optioncount
        if optioncount > 8:
            num_options = 8

        if x == 258: # down arrow
            if pos < optioncount:
                pos += 1
            else:
                pos = 0
        elif x == 259: # up arrow
            if pos > 0:
                pos += -1
            else:
                pos = optioncount
        elif x >= ord('1') and x <= ord(str(num_options+1)):
            pos = x - ord('0') - 1
    return pos

def processmenu(menu, parent=None):
    optioncount = len(menu['options'])
    exitmenu = False
    while not exitmenu:
        getin = runmenu(menu, parent)
        if getin == optioncount:
            exitmenu = True
        elif menu['options'][getin]['type'] == COMMAND:
            curses.def_prog_mode()
            os.system('reset')
            screen.clear()
            if "&&" in menu['options'][getin]['command']:
                commands = menu['options'][getin]['command'].split("&&")
                for c in commands:
                    success = os.system(c)
                    if success == 0:
                        continue
                    else:
                        print "FAILED command: " + c
                        break
            else:
                os.system(menu['options'][getin]['command'])
            screen.clear()
            curses.reset_prog_mode()
            curses.curs_set(1)
            curses.curs_set(0)
        elif menu['options'][getin]['type'] == INFO2:
            curses.def_prog_mode()
            os.system('reset')
            screen.clear()
            if "&&" in menu['options'][getin]['command']:
                commands = menu['options'][getin]['command'].split("&&")
                for c in commands:
                    success = os.system(c)
                    if success == 0:
                        continue
                    else:
                        print "FAILED command: " + c
                        break
            else:
                os.system(menu['options'][getin]['command'])
            if menu['title'] == "Remove Plugins":
                update_images()
                confirm()
                exitmenu = True
            elif menu['title'] == "Update Plugins":
                update_images()
                os.system("/bin/sh /data/build_images.sh")
                confirm()
            screen.clear()
            curses.reset_prog_mode()
            curses.curs_set(1)
            curses.curs_set(0)
        # !! TODO
        elif menu['options'][getin]['type'] == INFO:
            pass
        elif menu['options'][getin]['type'] == DISPLAY:
            pass
        # !! TODO
        elif menu['options'][getin]['type'] == SETTING:
            curses.def_prog_mode()
            os.system('reset')
            screen.clear()
            os.system(menu['options'][getin]['command'])
            screen.clear()
            curses.reset_prog_mode()
            curses.curs_set(1)
            curses.curs_set(0)
        elif menu['options'][getin]['type'] == INPUT:
            if menu['options'][getin]['title'] == "Add Plugins":
                plugin_url = get_param("Enter the HTTPS Git URL that contains the new plugins, e.g. https://github.com/CyberReboot/vent-plugins.git")
                curses.def_prog_mode()
                os.system('reset')
                screen.clear()
                if not "https://" in plugin_url:
                    os.system("echo No plugins added, url is not formatted correctly.")
                    os.system("echo Please use a git url, e.g. https://github.com/CyberReboot/vent-plugins.git")
                else:
                    os.system("python2.7 /data/plugin_parser.py add_plugins "+plugin_url)                    
                confirm()
                screen.clear()
                os.execl(sys.executable, sys.executable, *sys.argv)
        elif menu['options'][getin]['type'] == MENU:
            if menu['options'][getin]['title'] == "Remove Plugins":
                screen.clear()
                installed_plugins = get_installed_plugin_repos(INFO2, "remove")
                processmenu(installed_plugins, menu)
                screen.clear()
            elif menu['options'][getin]['title'] == "Show Installed Plugins":
                screen.clear()
                installed_plugins = get_installed_plugin_repos(DISPLAY, "")
                processmenu(installed_plugins, menu)
                screen.clear()
            elif menu['options'][getin]['title'] == "Update Plugins":
                screen.clear()
                installed_plugins = get_installed_plugin_repos(INFO2, "update")
                processmenu(installed_plugins, menu)
                screen.clear()
            elif menu['options'][getin]['title'] == "Status":
                screen.clear()
                plugins = get_plugin_status()
                processmenu(plugins, menu)
                screen.clear()
            else:
                screen.clear()
                processmenu(menu['options'][getin], menu)
                screen.clear()
        elif menu['options'][getin]['type'] == EXITMENU:
            exitmenu = True

def build_menu_dict():
    menu_data = {
      'title': "Vent", 'type': MENU, 'subtitle': "Please select an option...",
      'options':[
        { 'title': "Mode", 'type': MENU, 'subtitle': 'Please select an option...',
          'options': [
            { 'title': "Start", 'type': MENU, 'subtitle': '',
              'options': run_plugins("start")
            },
            { 'title': "Stop", 'type': MENU, 'subtitle': '',
              'options': run_plugins("stop")
            },
            { 'title': "Clean (Stop and Remove Containers)", 'type': MENU, 'subtitle': '',
              'options': run_plugins("clean")
            },
            { 'title': "Status", 'type': MENU, 'subtitle': '',
              'command': ''
            },
            { 'title': "Configure", 'type': MENU, 'subtitle': '',
              'options': update_plugins()
            }
          ]
        },
        { 'title': "Plugins", 'type': MENU, 'subtitle': 'Please select an option...',
          'options': [
            { 'title': "Add Plugins", 'type': INPUT, 'command': '' },
            { 'title': "Remove Plugins", 'type': MENU, 'command': '' },
            { 'title': "Show Installed Plugins", 'type': MENU, 'command': '' },
            { 'title': "Update Plugins", 'type': MENU, 'command': '' },
          ]
        },
        { 'title': "System Info", 'type': MENU, 'subtitle': '',
          'options': [
            #{ 'title': "Visualization Endpoint Status", 'type': INFO, 'command': '/bin/sh /var/lib/docker/data/visualization/get_url.sh' },
            { 'title': "Container Stats", 'type': COMMAND, 'command': "docker ps | awk '{print $NF}' | grep -v NAMES | xargs docker stats" },
            { 'title': "", 'type': INFO, 'command': 'echo'},
            { 'title': "RabbitMQ Management Status", 'type': INFO, 'command': 'python2.7 /data/service_urls/get_urls.py aaa-rabbitmq mgmt' },
            { 'title': "RQ Dashboard Status", 'type': INFO, 'command': 'python2.7 /data/service_urls/get_urls.py rq-dashboard mgmt' },
            { 'title': "Elasticsearch Head Status", 'type': INFO, 'command': 'python2.7 /data/service_urls/get_urls.py elasticsearch head' },
            { 'title': "Elasticsearch Marvel Status", 'type': INFO, 'command': 'python2.7 /data/service_urls/get_urls.py elasticsearch marvel' },
            { 'title': "Containers Running", 'type': INFO, 'command': 'docker ps | sed 1d | wc -l' },
            { 'title': "Uptime", 'type': INFO, 'command': 'uptime' },
          ]
        },
        { 'title': "Build", 'type': MENU, 'subtitle': '',
          'options': [
            { 'title': "Build new plugins and core", 'type': INFO2, 'command': '/bin/sh /data/build_images.sh' },
            { 'title': "Force rebuild all plugins and core", 'type': INFO2, 'command': '/bin/sh /data/build_images.sh --no-cache' },
          ]
        },
        { 'title': "Help", 'type': COMMAND, 'command': 'less /data/help' },
        { 'title': "Shell Access", 'type': COMMAND, 'command': 'cat /etc/motd; /bin/sh /etc/profile.d/boot2docker.sh; /bin/sh' },
        { 'title': "Reboot", 'type': COMMAND, 'command': 'sudo reboot' },
        { 'title': "Shutdown", 'type': COMMAND, 'command': 'sudo shutdown -h now' },
      ]
    }
    return menu_data

def main():
    menu_data = build_menu_dict()
    processmenu(menu_data)
    curses.endwin()
    os.system('clear')

if __name__ == "__main__":
    # make sure that vent-management is running
    result = check_output('/bin/sh /data/bootlocal.sh'.split())
    print result
    main()
