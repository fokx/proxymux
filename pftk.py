#!/i/venv/bin/python
# -*- coding: utf-8 -*-
import logging
import multiprocessing as mp
import os
import tkinter as tk

from config import name_to_port_dict, init_selected_name

from latency_test import auto_redir
import importlib

import proxymux_map

# RLIMIT_AS: The maximum area (in bytes) of address space which may be taken by the process.
# soft, hard = resource.getrlimit(resource.RLIMIT_AS)
# resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024*2, hard)) # 2GBi

def show_text_and_restart_redir_fn():
    label.config(text='Forward {} to {} '.format(var.get(), 3999))
    port = var.get()
    if port not in name_to_port_dict.values():
        port = name_to_port_dict[init_selected_name]
    if len(main_proxy_process) == 0:
        if port == 0:
            p = mp.Process(target=auto_redir)
        else:
            p = mp.Process(target=proxymux_map.redirect_remote_to_local, args=(3999, port))
        main_proxy_process.append(p)
        p.start()
    else:
        p = main_proxy_process.pop()
        p.terminate()
        if port == 0:
            p = mp.Process(target=auto_redir)
        else:
            p = mp.Process(target=proxymux_map.redirect_remote_to_local, args=(3999, port))
        main_proxy_process.append(p)
        p.start()


root = tk.Tk()
root.tk.call('tk', 'scaling', 2.0)
root.title('MUX')
# root.minsize(width=500, height=500)
root.geometry('400x600')
var = tk.IntVar()
for k, v in name_to_port_dict.items():
    btn = tk.Radiobutton(root, text='{}:{}'.format(k, v), variable=var, value=v, command=show_text_and_restart_redir_fn)
    btn.configure()
    btn.pack(anchor=tk.W)
    # set default selection
    if k == init_selected_name:
        var.set(v)
label = tk.Label(root)
label.pack()
main_proxy_process = []  # max len: 1
root.geometry()
show_text_and_restart_redir_fn()
# def quit(event):
#    root.quit()
# root.bind('<Control-c>', quit)
try:
    root.mainloop()
except:
    root.quit()
    root.destroy()
    os.system('pkill -f port_forward')
    os.system('pkill -f pftk')
