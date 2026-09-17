from controller import Vm

PALETTE = {
    "1": ("красный", 255, 0, 0),
    "2": ("зеленый", 0, 255, 0),
    "3": ("синий", 0, 0, 255),
    "4": ("желтый", 255, 255, 0),
    "5": ("голубой", 0, 255, 255),
    "6": ("пурпурный", 255, 0, 255),
    "7": ("белый", 255, 255, 255),
    "8": ("черный", 0, 0, 0),
    "9": ("серый", 128, 128, 128),
}

def show(vm):
    d = vm.report()
    r, g, b = d["rgb"]
    c, mm, y, k = d["cmyk"]
    h, l, s = d["hls"]
    print(f"RGB : R={r} G={g} B={b}")
    print(f"CMYK: C={c:.3f} M={mm:.3f} Y={y:.3f} K={k:.3f}")
    print(f"HLS : H={h:.1f} L={l:.3f} S={s:.3f}")
    if d["warn"]:
        print("(!) значение выходило за допустимый диапазон, выполнено обрезание/округление")

def ask_float(name):
    return float(input(f"{name} = ").strip())

def menu():
    print("""
1 - задать RGB
2 - задать CMYK
3 - задать HLS
4 - выбрать из палитры
5 - изменить одну компоненту ползунком (+/-)
0 - выход
""")

def edit_rgb(vm):
    vm.set_rgb(ask_float("R"), ask_float("G"), ask_float("B"))

def edit_cmyk(vm):
    vm.set_cmyk(ask_float("C 0..1"), ask_float("M 0..1"), ask_float("Y 0..1"), ask_float("K 0..1"))

def edit_hls(vm):
    vm.set_hls(ask_float("H 0..360"), ask_float("L 0..1"), ask_float("S 0..1"))

def pick_palette(vm):
    for k, (name, *_ ) in PALETTE.items():
        print(f"{k} - {name}")
    ch = input("номер: ").strip()
    if ch in PALETTE:
        _, r, g, b = PALETTE[ch]
        vm.set_rgb(r, g, b)

def slider(vm):
    fields = {
        "1": ("R", lambda: vm.r, lambda v: vm.set_rgb(v, vm.g, vm.b), 1, 0, 255),
        "2": ("G", lambda: vm.g, lambda v: vm.set_rgb(vm.r, v, vm.b), 1, 0, 255),
        "3": ("B", lambda: vm.b, lambda v: vm.set_rgb(vm.r, vm.g, v), 1, 0, 255),
        "4": ("H", lambda: vm.h, lambda v: vm.set_hls(v, vm.l, vm.s), 5, 0, 360),
        "5": ("L", lambda: vm.l, lambda v: vm.set_hls(vm.h, v, vm.s), 0.02, 0, 1),
        "6": ("S", lambda: vm.s, lambda v: vm.set_hls(vm.h, vm.l, v), 0.02, 0, 1),
        "7": ("K", lambda: vm.k, lambda v: vm.set_cmyk(vm.c, vm.mm, vm.y, v), 0.02, 0, 1),
    }
    for k, (name, *_ ) in fields.items():
        print(f"{k} - {name}")
    ch = input("компонента: ").strip()
    if ch not in fields:
        return
    name, get, setv, step, lo, hi = fields[ch]
    print("+ увеличить, - уменьшить, q выход")
    while True:
        cur = get()
        print(f"{name} = {cur:.2f}")
        a = input("> ").strip()
        if a == "q":
            break
        cur = cur + step if a == "+" else cur - step if a == "-" else cur
        cur = max(lo, min(hi, cur))
        setv(cur)
        show(vm)

def run():
    vm = Vm()
    show(vm)
    while True:
        menu()
        ch = input("выбор: ").strip()
        if ch == "0":
            break
        try:
            if ch == "1": edit_rgb(vm)
            elif ch == "2": edit_cmyk(vm)
            elif ch == "3": edit_hls(vm)
            elif ch == "4": pick_palette(vm)
            elif ch == "5": slider(vm)
            else:
                print("нет такого пункта")
                continue
        except ValueError:
            print("некорректный ввод")
            continue
        show(vm)
