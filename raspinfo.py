""" raspinfo
parse and display eng (engine) files
"""

import sys
import math
import json
import argparse
from collections import namedtuple

VERSION = '5.0'
ENG_NAME = "rasp.eng"  # name of engine database file

LPP = 56

Pages = 0
Lines = LPP

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

Engine = namedtuple('Engine', ' '.join(engine_info.keys()))


def parse_commandline():
    global args, parser

    parser = argparse.ArgumentParser(prog='raspinfo', description=f'Dump RASP engine info (v{VERSION})')
    parser.add_argument('-c', '--csv', action='store_true', help='output CSV format')
    parser.add_argument('-q', '--quiet', action='store_true', help="be quiet about it")
    parser.add_argument('--version', action='version', version=f'v{VERSION}')
    parser.add_argument('engfile', default=ENG_NAME, nargs='?', action='store', help='engine filename')

    args = parser.parse_args()


def load_engine(engine_file):

    eng_info = {}
    parsing_thrust = False
    with open(engine_file) as fp:
        for line in fp.readlines():
            if line.startswith(';'):
                continue

            if not parsing_thrust:
                try:
                    code, diam, dlen, sdelay, m2, wt, mfg = line.strip().split()
                except ValueError as e:
                    print("\n*** Error - Bad line in %s\n%s\n*** [%s]" %
                          (engine_file, e, line))
                    print("    Motor Code:  %s" % code)
                    print("    Diameter:    %d" % diam)
                    print("    Length:      %d" % dlen)
                    print("    Delays:      %s" % sdelay)
                    print("    ProMass:     %lf" % m2)
                    print("    MotMass:     %lf" % wt)
                    print("    Mfg Notes:   %s" % mfg)

                    sys.exit(0)

                e_info = {}
                e_info['code'] = code
                e_info['diam'] = math.ceil(float(diam))
                e_info['dlen'] = math.ceil(float(dlen))
                e_info['m2'] = m2
                e_info['wt'] = wt
                e_info['mf'] = mfg
                e_info['thrust'] = []

                parsing_thrust = True
            else:
                t, thrust = [float(v) for v in line.strip().split()]
                if t > 0 and thrust > 0:
                    e_info['thrust'].append((t, thrust))
                elif t > 0 and thrust == 0:
                    e_info['t2'] = t

                    t1, f1, ntot, npeak = 0, 0, 0, 0
                    for t2, f2 in e_info['thrust']:
                        npeak = max(npeak, float(f2))
                        ntot += (float(t2) - t1) * (f1 + float(f2)) / 2
                        t1, f1 = float(t2), float(f2)

                        if t1 <= 0 and f1 <= 0:
                            break

                    e_info['ntot'] = ntot
                    e_info['npeak'] = npeak
                    e_info['navg'] = ntot / t1
                    e_info['delay'] = []

                    for v in sdelay.strip().split('-'):
                        e_info['delay'].append(int(v))

                    eng_info[code] = e_info

                    parsing_thrust = False

    return eng_info
    

def print_engine_info(e):
    if e['wt'] >= 100.0:
        mm = "%6.2lf" % e['wt']
    elif e['wt'] >= 10.0:
        mm = "%6.3lf" % e['wt']
    else:
        mm = "%6.4lf" % e['wt']

    if e['m2'] >= 100.0:
        pm = "%6.2lf" % e['m2']
    elif e['m2'] >= 10.0:
        pm = "%6.3lf" % e['m2']
    else:
        pm = "%6.4lf" % e['m2']

    if e['navg'] >= 1000:
        avg = "%6.0lf" % e['navg']
    elif e['navg'] >= 100:
        avg = "%6.1lf" % e['navg']
    elif e['navg'] >= 10:
        avg = "%6.2lf" % e['navg']
    else:
        avg = "%6.3lf" % e['navg']

    if e['ntot'] >= 1000:
        tot = "%6.0lf" % e['ntot']
    elif e['ntot'] >= 100:
        tot = "%6.1lf" % e['ntot']
    elif e['ntot'] >= 10:
        tot = "%6.2lf" % e['ntot']
    else:
        tot = "%6.3lf" % e['ntot']

    if e['npeak'] >= 1000:
        mx = "%6.0lf" % e['npeak']
    elif e['npeak'] >= 100:
        mx = "%6.1lf" % e['npeak']
    elif e['npeak'] >= 10:
        mx = "%6.2lf" % e['npeak']
    else:
        mx = "%6.3lf" % e['npeak']

    if args.csv:
        print("\"%s\",\"%s\",%s,%s,%.2lf,%s,%s,%s,\"%dx%d\"",
         e['code'], Mfg, tot, avg, e['t2'],
         mx, mm, pm, e['dia'], e['dlen'])

"""

    for(d = 0; e_info[e].delay[d] >= 0; d++)
    if ( d == 0 )
      printf(",\"%d", e_info[e].delay[d]);
    else
      printf("-%d", e_info[e].delay[d]);
    
    printf("\"\n");
    }
    else
    {
    printf("%-9s %-5s  %6s %6s %5.2lf  %6s  %6s  %6s %dx%d",
         e_info[e].code, Mfg,
         Tot, Avg, 
         e_info[e].t2,
         Max, mm, PM,
         e_info[e].dia, e_info[e].len ) ;

for(d = 0; e_info[e].delay[d] >= 0; d++)
if ( d == 0 )
  printf(" %d", e_info[e].delay[d]);
else
  printf("-%d", e_info[e].delay[d]);

printf("\n");
}
}

int print_engine_header( ) 
{

int L = 4 ;  /* set to header line count */

if ( Pages++ > 0 )
{
if ( DoPages == 0 ) 
 return ( L ) ;
else
 printf ( "\f\n" ) ;
}

if ( DoCSV )
{
printf("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n",
     "", "", 
     "Total", "Avg", 
     "Burn", 
     "Peak", "Motor", "Pro",
     "\",\"" ) ;

printf("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n",
     "Motor", "Motor", 
     "Impulse", "Thrust", 
     "Time", 
     "Thrust", "Mass", "Mass",
     "\",\"" ) ;

printf("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n",
     "Desig", "Mfg", 
     "(Nsec)", "(N)", 
     "(sec)", 
     "(N)", "(Kg)", "(Kg)",
     "D x L\",\"Delays" ) ;
}
else
{
printf("%-9s %-5s  %6s %6s %5s  %6s  %6s  %6s %s %d\n",
     "", "", 
     "Total", "Avg", 
     "Burn", 
     "Peak", "Motor", "Pro",
     "       Page ", Pages ) ;

printf("%-9s %-5s %7s %6s %5s  %6s  %6s  %6s %s\n",
     " Motor", "Motor", 
     "Impulse", "Thrust", 
     "Time", 
     "Thrust", "Mass", "Mass",
     "" ) ;

printf("%-9s %-5s  %6s %6s %5s  %6s  %6s  %6s %s\n",
     " Desig", "Mfg", 
     "(Nsec)", "(N)", 
     "(sec)", 
     "(N)", "(Kg)", "(Kg)",
     "D x L  Delays" ) ;

printf("%-9s %-5s %7s %6s %5s  %6s  %6s  %6s %s\n",
     "=========", "=====", 
     "=======", "======", 
     "=====", 
     "======", "======", "======",
     "=================" );
}
return ( L ) ;
}
""" 


def main():
    parse_commandline()

    eng = load_engine(args.engfile)
    print(json.dumps(eng, indent=2))

    # if args.csv:
    #     print_engine_header()
    #
    # print_engine_info()


if __name__ == '__main__':
    main()
