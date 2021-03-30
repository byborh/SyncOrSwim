import tkinter as tk
import traceback
import colprint
from tkinter import messagebox

def alertonfail(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            colprint.printerr("Something went wrong")
            for l in traceback.format_exc().splitlines():
                colprint.printerr(">>>", end=" ")
                print(l)
            messagebox.showerror(title="Error", message="Something went wrong")
    return wrapper

class CallbackOptionMenu(tk.Frame):
    def __init__(self, parent, title, choices):
        ''' choices : [(text 1, callback 1), ... , (text n, callback n)] '''
        tk.Frame.__init__(self, parent)

        self.menubutton = tk.Menubutton(self, text=title, indicatoron=False, borderwidth=1, relief="raised")
        self.menu = tk.Menu(self.menubutton, tearoff=False)
        self.menubutton.configure(menu=self.menu)
        self.menubutton.pack()
        self.set_choices(choices)

    def set_choices(self, choices):
        self.menu.delete(0,'end')
        for choice in choices:
            label,command = choice
            self.menu.add_command(label=label, command=command)

    def add_choice(self, choice):
        label,command = choice
        self.menu.add_command(label=label, command=command)

    def change_state(self, choice, state):
        index = self.menu.index(choice)
        self.menu.entryconfig(index, state=state)

class MultiListbox(tk.Frame):
    def __init__(self, parent, choices):
        tk.Frame.__init__(self, parent)
        self.listbox  = tk.Listbox(self, height=5, selectmode=tk.MULTIPLE)
        self.listbox.configure(exportselection=False) # Prevent selection loss when defocusing
        self.btn_all  = tk.Button(self, text="All" , command=self.select_all)
        self.btn_none = tk.Button(self, text="None", command=self.select_none)
        self.listbox.grid(row=0, column=0, columnspan=2)
        self.btn_all.grid(row=1, column=0, sticky="nswe" )
        self.btn_none.grid(row=1, column=1, sticky="nswe")
        self.set_choices(choices)
    def set_choices(self, choices):
        self.listbox.delete(0, tk.END)
        for i,choice in enumerate(choices):
            self.listbox.insert(i, choice)
    def get(self):
        # A bit weird because of legacy reasons; TODO: remove weirdness
        items = self.listbox.get(0, tk.END)
        selection = self.listbox.curselection()
        dict = {ch:tk.IntVar(value=(i in selection)) for i,ch in enumerate(items)}
        return dict
    def set(self, list):
        for i in range(self.listbox.size()):
            if self.listbox.get(i) in list:
                self.listbox.selection_set(i)
            else:
                self.listbox.selection_clear(i)
    def select_all(self):
        self.listbox.selection_set(0, tk.END)
    def select_none(self):
        self.listbox.selection_clear(0, tk.END)

class RefListbox(tk.Frame):
    def __init__(self, parent, choices):
        tk.Frame.__init__(self, parent)
        self.listbox = tk.Listbox(self, height=5, selectmode=tk.BROWSE)
        self.listbox.configure(exportselection=False) # Prevent selection loss when defocusing
        self.listbox.grid(row=0, column=0, columnspan=2)
        self.set_choices(choices)
    def get(self):
        # Returns the selected item as a string for legacy reasons
        idx   = self.listbox.curselection()
        if not idx:
            self.listbox.selection_set(0)
            idx = 0
        else:
            idx = idx[0]
        return self.listbox.get(idx)
    def set_choices(self, choices):
        self.listbox.delete(0, tk.END)
        self.listbox.insert(0, "Auto")
        for i,choice in enumerate(choices):
            self.listbox.insert(i+1, choice)
