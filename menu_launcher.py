#!/usr/bin/env python2.7

import ConfigParser
import curses
import os
import sys

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
SETTING = "setting"

# path that exists on the iso
template_dir = "/data/templates/"
plugins_dir = "/data/plugins/"

def update_plugins():
    modes = []
    try:
        config = ConfigParser.RawConfigParser()
        config.read(template_dir+'modes.template')
        plugin_array = config.options("plugins")
        plugins = {}
        for plug in plugin_array:
            plugins[plug] = config.get("plugins", plug)

        for plugin in plugins:
            p = {}
            try:
                config = ConfigParser.RawConfigParser()
                config.read(template_dir+plugin+'.template')
                plugin_name = config.get("info", "name")
                p['title'] = plugin_name
                p['type'] = MENU
                p['subtitle'] = 'Please select a tool to configure...'
                p['options'] = []
                if plugins[plugin] == 'all':
                    tools = [ name for name in os.listdir(plugins_dir+plugin) if os.path.isdir(os.path.join(plugins_dir+plugin, name)) ]
                    for tool in tools:
                        t = {}
                        t['title'] = tool
                        t['type'] = SETTING
                        t['command'] = ''
                        p['options'].append(t)
                else:
                    for tool in plugins[plugin].split(","):
                        t = {}
                        t['title'] = tool
                        t['type'] = SETTING
                        t['command'] = ''
                        p['options'].append(t)
                modes.append(p)
            except:
                # if no name is provided, it doesn't get listed
                pass
    except:
        print "unable to get the configuration of modes from the templates.\n"
    return modes

# !! TODO read in template file using configparser

menu_data = {
  'title': "Vent", 'type': MENU, 'subtitle': "Please select an option...",
  'options':[
    { 'title': "Mode", 'type': MENU, 'subtitle': 'Please select a mode to run vent in...',
      'options': update_plugins()
    },
    { 'title': "Vent Settings", 'type': MENU, 'subtitle': 'Please select a vent setting to change...',
      'options': [
        { 'title': "Data", 'type': SETTING, 'command': '' },
      ]
    },
    { 'title': "Host Settings", 'type': MENU, 'subtitle': 'Please select a host setting to change...',
      'options': [
        { 'title': "Hostname", 'type': SETTING, 'command': '' },
        { 'title': "IP Address", 'type': SETTING, 'command': '' },
        { 'title': "SSH Keys", 'type': SETTING, 'command': '' },
      ]
    },
    { 'title': "System Info", 'type': MENU, 'subtitle': '',
      'options': [
        { 'title': "Containers Running", 'type': INFO, 'command': 'docker ps | sed 1d | wc -l' },
        { 'title': "Uptime", 'type': INFO, 'command': 'uptime' },
      ]
    },
    { 'title': "Build Plugins", 'type': MENU, 'subtitle': '',
      'options': [
        { 'title': "Build new plugins", 'type': INFO, 'command': '' },
        { 'title': "Force rebuild all", 'type': INFO, 'command': '' },
      ]
    },
    { 'title': "Shell Access", 'type': COMMAND, 'command': 'cat /etc/motd; /bin/sh /etc/profile.d/boot2docker.sh; /bin/sh' },
    { 'title': "Reboot", 'type': COMMAND, 'command': 'sudo reboot' },
  ]
}

def runmenu(menu, parent):
    if parent is None:
        lastoption = "Exit"
    else:
        lastoption = "Return to %s menu" % parent['title']

    optioncount = len(menu['options'])

    pos=0
    oldpos=None
    x = None

    while x !=ord('\n'):
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
                else:
                    screen.addstr(5+index,4, "%d - %s" % (index+1, menu['options'][index]['title']), textstyle)
            textstyle = n
            if pos==optioncount:
                textstyle = h
            screen.addstr(6+optioncount,4, "%d - %s" % (optioncount+1, lastoption), textstyle)
            screen.refresh()

        x = screen.getch()

        if x >= ord('1') and x <= ord(str(optioncount+1)):
            pos = x - ord('0') - 1
        elif x == 258: # down arrow
            if pos < optioncount:
                pos += 1
            else:
                pos = 0
        elif x == 259: # up arrow
            if pos > 0:
                pos += -1
            else:
                pos = optioncount
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
            os.system(menu['options'][getin]['command'])
            screen.clear()
            curses.reset_prog_mode()
            curses.curs_set(1)
            curses.curs_set(0)
        # !! TODO
        elif menu['options'][getin]['type'] == INFO:
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
        elif menu['options'][getin]['type'] == MENU:
            screen.clear()
            processmenu(menu['options'][getin], menu)
            screen.clear()
        elif menu['options'][getin]['type'] == EXITMENU:
            exitmenu = True

processmenu(menu_data)
curses.endwin()
os.system('clear')
