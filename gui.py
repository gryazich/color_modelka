import tkinter as tk
from tkinter import ttk, colorchooser
from controller import Vm

class Gui:
    def __init__(self, root):
        self.vm = Vm()
        self.root = root
        self.snap = {"RGB": {}, "CMYK": {}, "HLS": {}}  # точные значения блоков (до сдвига)
        self.expected = {}  # (блок, имя) -> что стоит на ползунке после программной записи
        root.title("Цветовые модели: RGB / CMYK / HLS")
        root.geometry("560x560")

        self.preview = tk.Canvas(root, height=60, bg="#ff0000", highlightthickness=1, highlightbackground="#888")
        self.preview.pack(fill="x", padx=10, pady=10)

        self.warn = tk.Label(root, text="", fg="#b35c00")
        self.warn.pack(fill="x", padx=10)

        tk.Button(root, text="выбрать из палитры", command=self.open_palette).pack(padx=10, pady=(0, 10), anchor="w")

        self.rgb = self.block(root, "RGB", [("R", 0, 255, 1), ("G", 0, 255, 1), ("B", 0, 255, 1)], self.vm.set_rgb)
        self.cmyk = self.block(root, "CMYK", [("C", 0, 1, 0.01), ("M", 0, 1, 0.01), ("Y", 0, 1, 0.01), ("K", 0, 1, 0.01)], self.vm.set_cmyk)
        self.hls = self.block(root, "HLS", [("H", 0, 360, 1), ("L", 0, 1, 0.01), ("S", 0, 1, 0.01)], self.vm.set_hls)

        self.refresh()

    def block(self, root, title, specs, setter):
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
            sld = tk.Scale(row, from_=lo, to=hi, resolution=step, orient="horizontal", showvalue=False,
                           command=lambda v, t=title, n=name, st=setter: self.on_move(t, n, float(v), st))
            ent.bind("<Return>", lambda e, t=title, n=name, v=var, lo=lo, hi=hi, st=setter: self.apply_entry(t, n, v, lo, hi, st))
            ent.bind("<FocusOut>", lambda e, t=title, n=name, v=var, lo=lo, hi=hi, st=setter: self.apply_entry(t, n, v, lo, hi, st))
            sld.pack(side="left", fill="x", expand=True, padx=5)
            widgets[name] = (var, sld)
        self.widgets_by_title = getattr(self, "widgets_by_title", {})
        self.widgets_by_title[title] = widgets
        return widgets

    def apply_entry(self, title, name, var, lo, hi, setter):
        try:
            v = float(var.get())
        except ValueError:
            return
        v = max(lo, min(hi, v))
        if abs(v - self.snap[title].get(name, v)) < 1e-9:
            return
        sld = self.widgets_by_title[title][name][1]
        sld.set(v)
        self.expected[(title, name)] = float(sld.get())
        self.apply(title, name, v, setter)

    def on_move(self, title, name, value, setter):
        # Эхо от программного sld.set(): значение совпадает с тем, что мы сами записали -> игнорируем
        if abs(value - self.expected.get((title, name), float("nan"))) < 1e-9:
            return
        self.expected[(title, name)] = value
        self.apply(title, name, value, setter)

    def apply(self, title, name, value, setter):
        keys = list(self.widgets_by_title[title])
        vals = dict(self.snap[title])   # остальные ползунки блока берём как были ДО сдвига
        vals[name] = value
        self.snap[title] = vals
        self.widgets_by_title[title][name][0].set(f"{value:.3f}" if isinstance(value, float) and value != int(value) else str(int(value)))
        setter(*[vals[k] for k in keys])
        self.refresh(skip=title)

    def write(self, title, values):
        widgets = self.widgets_by_title[title]
        for k, v in zip(widgets, values):
            var, sld = widgets[k]
            var.set(f"{v:.3f}" if isinstance(v, float) else str(v))
            sld.set(v)
            self.expected[(title, k)] = float(sld.get())  # что реально встало на ползунок
            self.snap[title][k] = v                        # точное значение, без округления ползунка

    def open_palette(self):
        _, hexval = colorchooser.askcolor(color="#%02x%02x%02x" % (self.vm.r, self.vm.g, self.vm.b))
        if hexval:
            r, g, b = int(hexval[1:3], 16), int(hexval[3:5], 16), int(hexval[5:7], 16)
            self.vm.set_rgb(r, g, b)
            self.refresh()

    def refresh(self, skip=None):
        d = self.vm.report()
        r, g, b = d["rgb"]
        c, m, y, k = d["cmyk"]
        h, l, s = d["hls"]
        if skip != "RGB": self.write("RGB", (r, g, b))
        if skip != "CMYK": self.write("CMYK", (c, m, y, k))
        if skip != "HLS": self.write("HLS", (h, l, s))
        self.preview.config(bg="#%02x%02x%02x" % (r, g, b))
        self.warn.config(text="некорректное значение обрезано/округлено" if d["warn"] else "")

def run():
    root = tk.Tk()
    Gui(root)
    root.mainloop()
