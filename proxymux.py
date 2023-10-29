#!/usr/bin/env python
import logging
import multiprocessing as mp
import os
import tkinter as tk

# RLIMIT_AS: The maximum area (in bytes) of address space which may be taken by the process.
# soft, hard = resource.getrlimit(resource.RLIMIT_AS)
# resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024*2, hard)) # 2GBi

from config import name_to_port_dict, init_selected_name, init_forwarded_to_port_num
from latency_test import auto_redir
import importlib

import proxymux_map

import urwid

from config import name_to_port_dict, init_selected_name

init_selected_port = name_to_port_dict[init_selected_name]
selected_port = init_selected_port

forwarded_to_port_num = init_forwarded_to_port_num

screen = urwid.raw_display.Screen()
title_raw_text = 'Proxy MUX'
title = urwid.Text(title_raw_text)
edit_prompt = urwid.Text('edit port forward destination: ')
def update_title():
    title.set_text(f'{title_raw_text}: {selected_port} -> {forwarded_to_port_num}')

proxy_processes = []
chart_radio_buttons = []
mode_radio_buttons = []
main_proxy_process = None


def set_mode(port, is_foreground_chart):
    screen.set_terminal_properties(port)
    screen.reset_default_terminal_palette()


def restart_proxy_process():
    global main_proxy_process
    main_proxy_process.kill()
    if selected_port == 0:
        main_proxy_process = mp.Process(target=auto_redir)
    else:
        main_proxy_process = mp.Process(target=proxymux_map.redirect_remote_to_local,
                                        args=(forwarded_to_port_num, selected_port))
    main_proxy_process.start()
    update_title()


def on_mode_change(rb, state, args):
    global selected_port
    new_port = args[0]
    assert new_port in name_to_port_dict.values(), f'{new_port} not in `name_to_port_dict` dict_values'
    if new_port != selected_port:
        selected_port = new_port
        logging.info(f'fsource port changed to {selected_port}')
        restart_proxy_process()
    # if this radio button is checked
    # if state:
    #     is_foreground_chart = chart_radio_buttons[0].state
    #     set_mode(port, is_foreground_chart)


def fcs(widget):
    # wrap widgets that can take focus
    return urwid.AttrMap(widget, None, "focus")


def mode_rb(text, port, state=False):
    # mode radio buttons
    rb = urwid.RadioButton(mode_radio_buttons, text, state)
    urwid.connect_signal(rb, "change", on_mode_change, user_arg=[port])
    return fcs(rb)


def on_chart_change(rb, state):
    # handle foreground check box state change
    set_mode(screen.port, state)


def unhandled_input(key):
    if key in ("Q", "q", "esc"):
        raise urwid.ExitMainLoop()


class PortNumEditor(urwid.Edit):
    def keypress(self, size, key):
        if key != 'enter':
            return super().keypress(size, key)
        else:
            global forwarded_to_port_num
            try:
                to_change = int(self.edit_text)
                if to_change != forwarded_to_port_num:
                    forwarded_to_port_num = to_change
                    restart_proxy_process()
                    logging.info(f'port number forwarded to changed to {forwarded_to_port_num}')
            except:
                logging.error(
                    f'cannot using {self.edit_text} as port number forwarded to, will use {init_forwarded_to_port_num} as fallback')
                restart_proxy_process()
                logging.info(f'port number forwarded to changed to {forwarded_to_port_num}')


def main():
    global main_proxy_process
    logging.basicConfig(level=logging.ERROR)

    main_proxy_process = mp.Process(target=proxymux_map.redirect_remote_to_local,
                                    args=(forwarded_to_port_num, init_selected_port))
    main_proxy_process.start()
    update_title()

    palette = [
        ("header", "black,underline", "light gray", "standout,underline", "black,underline", "#88a"),
        ("panel", "light gray", "dark blue", "", "#ffd", "#00a"),
        ("focus", "light gray", "dark cyan", "standout", "#ff8", "#806"),
    ]
    screen.register_palette(palette)
    lb = urwid.SimpleListWalker([])

    edit = PortNumEditor("", f'{init_forwarded_to_port_num}')
    # urwid.connect_signal(edit, "change", edit_change_event)
    # edit_change_event(edit, f'{init_forwarded_to_port_num}')
    edit = urwid.AttrMap(edit, "edit")

    lb.extend(
        [
            urwid.AttrMap(title, "header"),
            urwid.AttrMap(
                urwid.Columns(
                    [
                        urwid.Pile([
                            mode_rb(f'{name}: {port_num}',
                                    port_num,
                                    (True if name == init_selected_name else False)
                                    )
                            for name, port_num in name_to_port_dict.items()
                        ]),
                        # urwid.Pile(
                        #     [
                        #         fcs(urwid.RadioButton(chart_radio_buttons, "Foreground port", True, on_chart_change)),
                        #         fcs(urwid.RadioButton(chart_radio_buttons, "Background port")),
                        #         urwid.Divider(),
                        #         fcs(urwid.Button("Exit", click_exit)),
                        #     ]
                        # ),
                    ]
                ),
                "panel",
            ),
            urwid.AttrMap(urwid.Columns(
                    [
                        edit_prompt, edit
                    ]
                ), "header"),
        ]
    )

    try:
        urwid.MainLoop(urwid.ListBox(lb), screen=screen, unhandled_input=unhandled_input).run()
    except KeyboardInterrupt as e:
        print('KeyboardInterrupt')
        for p in proxy_processes:
            p.kill()
        raise urwid.ExitMainLoop()


if __name__ == '__main__':
    main()
