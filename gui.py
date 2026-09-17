import tkinter as tk
from tkinter import ttk, colorchooser
from controller import Vm

class Gui:
    def __init__(self, root):
        self.vm = Vm()
        self.busy = False
        root.title("Цветовые модели: RGB / CMYK / HLS")
        root.geometry("560x560")

        self.preview = tk.Canvas(root, height=60, bg="#ff0000", highlightthickness=1, highlightbackground="#888")
        self.preview.pack(fill="x", padx=10, pady=10)

        self.warn = tk.Label(root, text="", fg="#b35c00")
        self.warn.pack(fill="x", padx=10)

        tk.Button(root, text="Выбрать из палитры...", command=self.open_palette).pack(padx=10, pady=(0, 10), anchor="w")

        self.rgb = self.block(root, "RGB", [("R", 0, 255, 1), ("G", 0, 255, 1), ("B", 0, 255, 1)], self.on_rgb)
        self.cmyk = self.block(root, "CMYK", [("C", 0, 1, 0.01), ("M", 0, 1, 0.01), ("Y", 0, 1, 0.01), ("K", 0, 1, 0.01)], self.on_cmyk)
        self.hls = self.block(root, "HLS", [("H", 0, 360, 1), ("L", 0, 1, 0.01), ("S", 0, 1, 0.01)], self.on_hls)

        self.refresh()

    def block(self, root, title, specs, cb):
        f = ttk.LabelFrame(root, text=title)
        f.pack(fill="x", padx=10, pady=5)
        widgets = {}
        for name, lo, hi, step in specs:
            row = tk.Frame(f)
            row.pack(fill="x", padx=5, pady=2)
            tk.Label(row, text=name, width=2).pack(side="left")
            var = tk.StringVar()
            ent = tk.Entry(row, textvariable=var, width=8)
            ent.pack(side="left")
            ent.bind("<Return>", lambda e, c=cb: c())
            sld = tk.Scale(row, from_=lo, to=hi, resolution=step, orient="horizontal", showvalue=False, command=lambda v, c=cb: c())
            sld.pack(side="left", fill="x", expand=True, padx=5)
            widgets[name] = (var, sld)
        return widgets

    def read(self, widgets, keys):
        return [widgets[k][1].get() for k in keys]

    def write(self, widgets, keys, values):
        for k, v in zip(keys, values):
            var, sld = widgets[k]
            var.set(f"{v:.3f}" if isinstance(v, float) else str(v))
            sld.set(v)

    def on_rgb(self):
        if self.busy: return
        self.vm.set_rgb(*self.read(self.rgb, "RGB"))
        self.refresh(skip="rgb")

    def on_cmyk(self):
        if self.busy: return
        self.vm.set_cmyk(*self.read(self.cmyk, "CMYK"))
        self.refresh(skip="cmyk")

    def on_hls(self):
        if self.busy: return
        self.vm.set_hls(*self.read(self.hls, "HLS"))
        self.refresh(skip="hls")

    def open_palette(self):
        _, hexval = colorchooser.askcolor(color="#%02x%02x%02x" % (self.vm.r, self.vm.g, self.vm.b))
        if hexval:
            r, g, b = int(hexval[1:3], 16), int(hexval[3:5], 16), int(hexval[5:7], 16)
            self.vm.set_rgb(r, g, b)
            self.refresh()

    def refresh(self, skip=None):
        self.busy = True
        d = self.vm.report()
        r, g, b = d["rgb"]
        c, m, y, k = d["cmyk"]
        h, l, s = d["hls"]
        if skip != "rgb": self.write(self.rgb, "RGB", (r, g, b))
        if skip != "cmyk": self.write(self.cmyk, "CMYK", (c, m, y, k))
        if skip != "hls": self.write(self.hls, "HLS", (h, l, s))
        self.preview.config(bg="#%02x%02x%02x" % (r, g, b))
        self.warn.config(text="некорректное значение обрезано/округлено" if d["warn"] else "")
        self.busy = False

def run():
    root = tk.Tk()
    Gui(root)
    root.mainloop()
