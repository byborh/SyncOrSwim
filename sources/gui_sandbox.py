import tkinter as tk

class Example(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        menubutton = tk.Menubutton(self, text="Choose wisely",
                                   indicatoron=True, borderwidth=1, relief="raised")
        menu = tk.Menu(menubutton, tearoff=True)
        menubutton.configure(menu=menu)
        menubutton.pack(padx=10, pady=10)

        self.choices = {}
        def update_all():
            if self.choices['all'].get():
                for choice in self.choices:
                    self.choices[choice].set(1)
            else:
                for choice in self.choices:
                    self.choices[choice].set(0)
        def update_one():
            all = True
            for choice in self.choices:
                if choice != "all":
                    all *= self.choices[choice].get()
            if all:
                self.choices['all'].set(1)
            else:
                self.choices['all'].set(0)
        self.choices['all'] = tk.IntVar(value=0)
        menu.add_checkbutton(label='all', variable=self.choices['all'],
                             onvalue=1, offvalue=0,
                             command=update_all)
        for choice in ([f"e{x}" for x in range(10)]):
            self.choices[choice] = tk.IntVar(value=0)
            menu.add_checkbutton(label=choice, variable=self.choices[choice],
                                 onvalue=1, offvalue=0,
                                 command=update_one)
    def printValues(self):
        for name, var in self.choices.items():
            print(f"{name}: {var.get()}")

if __name__ == "__main__":
    root = tk.Tk()
    Example(root).pack(fill="both", expand=True)
    root.mainloop()
