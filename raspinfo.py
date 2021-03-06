""" raspinfo
parse and display eng (engine) files
"""

import sys
import math
import argparse
from collections import namedtuple

VERSION = '5.0'
ENG_NAME = "rasp.eng"  # name of engine database file
CH1 = '#'

engine_info = {
    "t2": ("thrust duration", "seconds"),
    "m2": ("propellant wt", "kilograms"),
    "wt": ("initial engine wt", "kilograms"),
    "thrust": ("thrust curve", "Newtons"),
    "navg": ("average thrust", "newtons"),
    "ntot": ("total impulse", "newton-seconds"),
    "npeak": ("peak thrust", "newtons"),
    "dia": ("engine diameter", "millimeters"),
    "len": ("engine length", "millimeters"),
    "delay": ("ejection delays available", "sec"),
    "mfg": ("manufacturer info", None),
    "code": ("engine name", None),
}

Thrust = namedtuple('Thrust', 't thrust')


class Engine:
    def __init__(self, mfg, code, m2, diam, dlen, wt, delay):
        self.mfg = mfg
        self.code = code
        self.diam = math.ceil(float(diam))
        self.dlen = math.ceil(float(dlen))
        self.m2 = float(m2)
        self.wt = float(wt)
        self.delay = delay
        self.thrust = []

    def add_thrust(self, t, thrust):
        self.thrust.append(Thrust(float(t), float(thrust)))
     
    def get_thrust(self, t):
        """ get thrust with respect to t """

        if t >= 0.0:
            prev_t = 0.0
            prev_thrust = 0.0
            for node in self.thrust:
                if round(t, 3) <= round(node.t, 3):
                    factor = (t - prev_t) / (node.t - prev_t)
                    return prev_thrust + factor * (node.thrust - prev_thrust)

                prev_t, prev_thrust = node

        return 0.0

    def t2(self):
        return self.thrust[-1].t if self.thrust else None
        
    def ntot(self):
        t1, f1, tot = 0, 0, 0
        for t2, f2 in self.thrust:
            tot += (t2 - t1) * (f1 + f2) / 2
            t1, f1 = t2, f2

        return tot
        
    def npeak(self):
        return max([p.thrust for p in self.thrust])
    
    def navg(self):
        return self.ntot() / self.t2()
        
        
def parse_commandline():
    global args, parser

    parser = argparse.ArgumentParser(prog='raspinfo', description=f'Dump RASP engine info (v{VERSION})')
    parser.add_argument('-c', '--csv', dest='fmt', action='store_const', const='csv',
                        default='txt', help='output CSV format')
    parser.add_argument('-q', '--quiet', action='store_true', help="be quiet about it")
    parser.add_argument('--version', action='version', version=f'v{VERSION}')
    parser.add_argument('engfile', default=ENG_NAME, nargs='?', action='store', help='engine filename')

    args = parser.parse_args()


def load_engine(engine_file):
    eng_info = {}
    parsing_thrust = False
    with open(engine_file) as fp:
        for linenum, line in enumerate(fp.readlines(), start=1):
            if line.startswith(';'):
                continue

            if not parsing_thrust:
                try:
                    code, diam, dlen, sdelay, m2, wt, mfg = line.strip().split()
                except ValueError as e:
                    print("\n*** Error - Bad line in %s\n%s\n*** [%s]" %
                          (engine_file, e, line))
                    sys.exit(0)
               
                delay = []
                for v in sdelay.strip().split('-'):
                    delay.append(int(v))
                    
                motor = Engine(mfg, code, m2, diam, dlen, wt, delay)

                parsing_thrust = True
            else:
                t, thrust = [float(v) for v in line.strip().split()]
                motor.add_thrust(t, thrust)
                if t > 0 and thrust == 0:
                    eng_info[code] = motor
                    motor = None

                    parsing_thrust = False

    return eng_info


def find_motor(eng_file, mcode):
    eng_info = load_engine(eng_file)

    return eng_info[mcode.upper()]


def get_motor(eng_file, prompt="Motor code"):
    while True:
        s = input(prompt)

        words = s.split()

        if len(words) == 3 and words[0].lower() == "file":
            _, filename, mcode = words
        else:
            filename = eng_file
            mcode = words[0]

        motor = find_motor(filename, mcode)
        if motor:
            return motor


def print_engine_info(e, fp, fmt='txt'):
    if e.wt >= 100.0:
        mm = "%6.2lf" % e.wt
    elif e.wt >= 10.0:
        mm = "%6.3lf" % e.wt
    else:
        mm = "%6.4lf" % e.wt

    if e.m2 >= 100.0:
        pm = "%6.2lf" % e.m2
    elif e.m2 >= 10.0:
        pm = "%6.3lf" % e.m2
    else:
        pm = "%6.4lf" % e.m2

    if e.navg() >= 1000:
        avg = "%6.0lf" % e.navg()
    elif e.navg() >= 100:
        avg = "%6.1lf" % e.navg()
    elif e.navg() >= 10:
        avg = "%6.2lf" % e.navg()
    else:
        avg = "%6.3lf" % e.navg()

    if e.ntot() >= 1000:
        tot = "%6.0lf" % e.ntot()
    elif e.ntot() >= 100:
        tot = "%6.1lf" % e.ntot()
    elif e.ntot() >= 10:
        tot = "%6.2lf" % e.ntot()
    else:
        tot = "%6.3lf" % e.ntot()

    if e.npeak() >= 1000:
        mx = "%6.0lf" % e.npeak()
    elif e.npeak() >= 100:
        mx = "%6.1lf" % e.npeak()
    elif e.npeak() >= 10:
        mx = "%6.2lf" % e.npeak()
    else:
        mx = "%6.3lf" % e.npeak()

    dxl = "%dx%d" % (e.diam, e.dlen)
    if fmt == 'csv':
        print("\"%s\",\"%s\",%s,%s,%.2lf,%s,%s,%s,\"%s\",\"%s\"" %
              (e.code, e.mfg[:5], tot, avg, e.t2(), mx, mm, pm, dxl,
               '-'.join(str(d) for d in e.delay)), file=fp)
    else:
        print("%c %-9s  %-5s  %7s  %6s  %5.2lf  %6s  %6s  %6s %7s %s" %
              (CH1, e.code, e.mfg[:5], tot, avg, e.t2(), mx, mm, pm, dxl,
               '-'.join(str(d) for d in e.delay)), file=fp)


def print_engine_header(fp, fmt='txt'):
    if fmt == 'csv':
        print("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"" % (
             "", "", "Total", "Avg", "Burn",
             "Peak", "Motor", "Prop", "\",\""), file=fp)
        
        print("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"" % (
             "Motor", "Motor", "Impulse", "Thrust",
             "Time", "Thrust", "Mass", "Mass", "\",\""), file=fp)
        
        print("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"" % (
             "Desig", "Mfg", "(Nsec)", "(N)", "(sec)",
             "(N)", "(Kg)", "(Kg)", "D x L\",\"Delays"), file=fp)
    else:
        print(CH1, file=fp)
        print("%c %-9s  %-5s  %7s  %6s  %5s  %6s  %6s  %6s %s" % (
             CH1, "", "", "Total", "Avg", "Burn",
             "Peak", "Motor", "Prop", ""), file=fp)
        
        print("%c %-9s  %-5s  %7s  %6s  %5s  %6s  %6s  %6s %s" % (
             CH1, "Motor", "Motor", "Impulse", "Thrust",
             "Time", "Thrust", "Mass", "Mass", ""), file=fp)
        
        print("%c %-9s  %-5s  %7s  %6s  %5s  %6s  %6s  %6s %s" % (
             CH1, "Desig", "Mfg", "(Nsec)", "(N)", "(sec)",
             "(N)", "(Kg)", "(Kg)", "D x L   Delays"), file=fp)
        
        print("%c %-9s  %-5s  %7s  %6s  %5s  %6s  %6s  %6s %7s %s" % (
             CH1, "=========", "=====", "=======", "======",
             "=====", "======", "======", "======",
             "=======", "=========="), file=fp)


def main():
    parse_commandline()
    print(args)

    eng = load_engine(args.engfile)
    # print(json.dumps(eng, indent=2))

    print_engine_header(sys.stdout, fmt=args.fmt)
    for k in sorted(eng.keys()):
        print_engine_info(eng[k], sys.stdout, fmt=args.fmt)

    e = eng['D12']
    print(e.t2(), e.thrust)
    for t in range(0, round(e.t2() * 10) + 1):
        print(f"{t/10:3.1f} {e.get_thrust(t/10.0):.2f}")


if __name__ == '__main__':
    main()
