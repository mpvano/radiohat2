from tkinter import *
from tkinter import ttk
from time import sleep
from ctypes import *


class VSWRMeter:

    def __init__(self, root):

        root.title("Status")
        root.geometry('280x100+0+0')
        mainframe = ttk.Frame(root, padding="10 10 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        self.Power = StringVar()
        ttk.Label(mainframe, text="Power:").grid(column=1, row=1, sticky=W)
        ttk.Label(mainframe, textvariable=self.Power).grid(column=2, row=1, sticky=(W, E))
        
        self.VSWR = StringVar()
        ttk.Label(mainframe, text="VSWR:").grid(column=1, row=2, sticky=W)
        ttk.Label(mainframe, textvariable=self.VSWR).grid(column=2, row=2, sticky=(W, E))

        self.Batt = StringVar()
        ttk.Label(mainframe, text="Battery:").grid(column=1, row=3, sticky=W)
        ttk.Label(mainframe, textvariable=self.Batt).grid(column=2, row=3, sticky=(W, E))

        for child in mainframe.winfo_children(): 
            child.grid_configure(padx=5, pady=5)

        self.vswrdac = CDLL('libradiohat.so')
        self.vswrdac.initVSWR()
        self.readForwardOnly = self.vswrdac.readForwardOnly
        self.readVSWROnly = self.vswrdac.readVSWROnly
        self.readADCRaw = self.vswrdac.readADCRaw
        self.readForwardOnly.restype = c_float
        self.readVSWROnly.restype = c_float
        self.readADCRaw.restype = c_float

        mainframe.focus()
        timer = root.after(200, self.calculate)
        
    def calculate(self):
        try:
            self.Power.set(str(round(self.readForwardOnly(),1)) + ' Watts')
            sleep(0.01)
            self.VSWR.set(str(round(self.readVSWROnly(),2)) + ':1')
            sleep(0.01)
            self.Batt.set(str(round(10 * self.readADCRaw(1,0),2)) + ' Volts')
            timer = root.after(200, self.calculate )
        except ValueError:
            pass

root = Tk()
VSWRMeter(root)
root.mainloop()