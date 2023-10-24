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
proxymux_map = importlib.import_module("proxymux-map")

import urwid

from config import name_to_port_dict, init_selected_name

init_selected_port = name_to_port_dict[init_selected_name]
selected_port = init_selected_port

forwarded_to_port_num = init_forwarded_to_port_num

screen = urwid.raw_display.Screen()

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
        main_proxy_process = mp.Process(target=proxymux_map.redirect_remote_to_local, args=(forwarded_to_port_num, selected_port))
    main_proxy_process.start()


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


def click_exit(button):
    raise urwid.ExitMainLoop()


def unhandled_input(key):
    if key in ("Q", "q", "esc"):
        raise urwid.ExitMainLoop()


def main():
    global main_proxy_process
    logging.basicConfig(level=logging.ERROR)

    main_proxy_process = mp.Process(target=proxymux_map.redirect_remote_to_local, args=(forwarded_to_port_num, init_selected_port))
    main_proxy_process.start()

    palette = [
        ("header", "black,underline", "light gray", "standout,underline", "black,underline", "#88a"),
        ("panel", "light gray", "dark blue", "", "#ffd", "#00a"),
        ("focus", "light gray", "dark cyan", "standout", "#ff8", "#806"),
    ]
    screen.register_palette(palette)
    lb = urwid.SimpleListWalker([])

    def edit_change_event(widget, text):
        global forwarded_to_port_num
        try:
            to_change = int(text)
            if to_change != forwarded_to_port_num:
                forwarded_to_port_num = to_change
                restart_proxy_process()
                logging.info(f'port number forwarded to changed to {forwarded_to_port_num}')
        except:
            logging.error(
                f'cannot using {text} as port number forwarded to, will use {init_forwarded_to_port_num} as fallback')
            restart_proxy_process()
            logging.info(f'port number forwarded to changed to {forwarded_to_port_num}')

    def create_edit(label, text, fn):
        w = urwid.Edit(label, text)
        urwid.connect_signal(w, "change", fn)
        fn(w, text)
        w = urwid.AttrMap(w, "edit")
        return w

    edit = create_edit("", f'{init_forwarded_to_port_num}', edit_change_event)

    lb.extend(
        [
            urwid.AttrMap(urwid.Text("Proxy MUX"), "header"),
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
            urwid.AttrMap(edit, "header"),
        ]
    )

    try:
        urwid.MainLoop(urwid.ListBox(lb), screen=screen, unhandled_input=unhandled_input).run()
    except KeyboardInterrupt as e:
        print('KeyboardInterrupt')
        for p in proxy_processes:
            p.terminate()
        raise urwid.ExitMainLoop()


if __name__ == '__main__':
    main()
