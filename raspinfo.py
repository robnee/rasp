""" raspinfo
parse and display eng (engine) files
"""

import math
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
    "delay":( "ejection delays available", "sec"),
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

    e_info = {}
    with open(engine_file) as fp:
        for line in fp.readlines():
            if line.startswith(';'):
                continue
            print(line, 'ord:', ord(line[0]), line.startswith(':'))
        try:
            code, diam, dlen, delay, m2, wt, mfg = line.strip().split()
        except ValueError as e:
            print("\n*** Error - Bad line in %s\n%s\n*** [%s]" % (engine_file, e, line))
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
        e_info['diam'] = mah.ceil(ddiam)
        e_info['dlen'] = math.ceil(dlen)
        e_info['m2'] = m2
        e_info['wt'] = wt
        e_info['mf'] = mfg
        e_info['thrust'] = []

        t = 0
        for line in fp.readlines():
            if line.startswith(';'):
                continue

            t, thrust = [float(v) for v in line.strip().split()]
            if t > 0 and thrust > 0:
                e_info['thrust'].append((t, thrust))
            elif t > 0 and thrust == 0:
                e_info['t2'] = t
                break
                
        if 't2' not in e_info:
            print('unexpected EOF')
            sys.exit(1)
  
        t1, f1, sum, peak = 0, 0, 0, 0
        for t2, f2 in e_info['thrust']:
            if f2 > peak:
                peak = f2
                
            sum += (t2 - t1) * (f1, f2) / 2
            t1, f1 = t2, f2
    
            if t1 <= 0 and f1 <= 0:
                break

        e_info['ntot'] = sum
        e_info['npeak'] = peak
        e_info['navg'] = sum / t1
        
        c = sdelay
        for v in e_info['delay'].strip().split('-'):
            e_info['delay'].append(int(v))
            
        eng_info[code] = e_info
        
    return eng_info
    

"""
void print_engine_info(int e)
{
  int d;

  char Avg [ 8 ] ;
  char Tot [ 8 ] ;
  char Max [ 8 ] ;
  char MM  [ 8 ] ;
  char PM  [ 8 ] ;
  char Mfg [ 6 ] ;

  strncpy ( Mfg, e_info[e].mfg, 5 ) ;

  Mfg [5] = '\0' ;

  if ( e_info[e].wt >= 100.0 )
     sprintf ( MM, "%6.2lf", e_info[e].wt );
  else if ( e_info[e].wt >= 10.0 )
     sprintf ( MM, "%6.3lf", e_info[e].wt );
  else if ( e_info[e].wt >= 1.0 )
     sprintf ( MM, "%6.4lf", e_info[e].wt );
  else
     sprintf ( MM, "%6.4lf", e_info[e].wt );

  if ( e_info[e].m2 >= 100.0 )
     sprintf ( PM, "%6.2lf", e_info[e].m2 );
  else if ( e_info[e].m2 >= 10.0 )
     sprintf ( PM, "%6.3lf", e_info[e].m2 );
  else if ( e_info[e].m2 >= 1.0 )
     sprintf ( PM, "%6.4lf", e_info[e].m2 );
  else
     sprintf ( PM, "%6.4lf", e_info[e].m2 );

  if ( e_info[e].navg >= 1000 )
     sprintf ( Avg, "%6.0lf", e_info[e].navg );
  else if ( e_info[e].navg >= 100 )
     sprintf ( Avg, "%6.1lf", e_info[e].navg );
  else if ( e_info[e].navg >= 10 )
     sprintf ( Avg, "%6.2lf", e_info[e].navg );
  else 
     sprintf ( Avg, "%6.3lf", e_info[e].navg );

  if ( e_info[e].ntot >= 1000 )
     sprintf ( Tot, "%6.0lf", e_info[e].ntot );
  else if ( e_info[e].ntot >= 100 )
     sprintf ( Tot, "%6.1lf", e_info[e].ntot );
  else if ( e_info[e].ntot >= 10 )
     sprintf ( Tot, "%6.2lf", e_info[e].ntot );
  else 
     sprintf ( Tot, "%6.3lf", e_info[e].ntot );

  if ( e_info[e].npeak >= 1000 )
     sprintf ( Max, "%6.0lf", e_info[e].npeak );
  else if ( e_info[e].npeak >= 100 )
     sprintf ( Max, "%6.1lf", e_info[e].npeak );
  else if ( e_info[e].npeak >= 10 )
     sprintf ( Max, "%6.2lf", e_info[e].npeak );
  else 
     sprintf ( Max, "%6.3lf", e_info[e].npeak );

   if ( DoCSV )
   {
  printf("\"%s\",\"%s\",%s,%s,%.2lf,%s,%s,%s,\"%dx%d\"",
             e_info[e].code, Mfg,
             Tot, Avg, 
             e_info[e].t2,
             Max, MM, PM,
             e_info[e].dia, e_info[e].len ) ;

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
             Max, MM, PM,
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
    print(eng)

"""
    if args.csv:
        print_engine_header()
    
    print_engine_info()
"""


if __name__ == '__main__':
    main()
