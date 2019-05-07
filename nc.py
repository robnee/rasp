import os
import re
import sys
import units
import math
import raspinfo
import rasp

VERSION = '4.2'
press_oride = False


# Todo: make this a named_tuple
"""
typedef struct Mnemonics
   {
      char  * Tag ;
      char  * Dfu ;
      int     Ndx ;
      int    Type ;
      int    Unit ;
   }  MneData ;
"""

MNEMONICS = {
      "none": (None, None, None, None),
      "home": (None, "HOME", "STRING", None),
      "homedir": (None, "HOME", "STRING", None),
      "rasphome": (None, "HOME", "STRING", None),
      "raspdir": (None, "HOME", "STRING", None),
      "units": (None, "UNITS", "STRING", None),
      "mode": (None, "MODE", "STRING", None),
      "quiet": (None, "QUIET", "INTEGER", None),
      "summary": (None, "QUIET", "INTEGER", None),
      "verbose": (None, "VERBOSE", "INTEGER", None),
      "detail": (None, "VERBOSE", "INTEGER", None),
      "launch": (None, "LAUNCH", None, None),
      "quit": (None, "QUIT", None, None),
      "done": (None, "QUIT", None, None),
      "exit": (None, "QUIT", None, None),
      "debug": (None, "DEBUG", "INTEGER", None),
      "dump": (None, "DUMP", None, None),
      "title": (None, "TITLE", None, None),

      "dtime": ("sec", "DTIME", "DOUBLE", "TIME"),
      "printtime": ("sec", "PRINTTIME", "DOUBLE", "time"),
      "printcommand": (None, "PRINTCMD", "STRING", None),

      "sitealtitude": ("ft", "SITEALT", "DOUBLE", "length"),
      "finalaltitude": ("ft", "FINALALT", "DOUBLE", "length"),
      "coasttime": ("sec", "COASTTIME", "DOUBLE", "time"),
      "sitetemperature": ("F", "SITETEMP", "DOUBLE", "temp"),
      "sitepressure": ("inHg", "SITEPRESS", "DOUBLE", "press"),
      "raillength": ("in", "RAILLENGTH", "DOUBLE", "length"),
      "rodlength": ("in", "RAILLENGTH", "DOUBLE", "length"),
      "enginefile": (None, "ENGINEFILE", "FILENAME", "EXISTS"),
      "motorfile": (None, "ENGINEFILE", "FILENAME", "EXISTS"),

      "numstages": (None, "NUMSTAGES", "INTEGER", None),
      "nosetype": (None, "NOSETYPE", "STRING", None),
      "stage": (None, "STAGE", "INTEGER", None),
      "stagedelay": ("sec", "STAGEDELAY", "DOUBLE", "time"),
      "diameter": ("in", "DIAMETER", "DOUBLE", "length"),
      "numfins": (None, "NUMFINS", "INTEGER", None),
      "finthickness": ("in", "FINTHICKNESS", "DOUBLE", "length"),
      "finspan": ("in", "FINSPAN", "DOUBLE", "length"),
      "drymass": ("oz", "DRYMASS", "DOUBLE", "mass"),
      "dmass": ("oz", "DRYMASS", "DOUBLE", "mass"),
      "mass": ("oz", "DRYMASS", "DOUBLE", "mass"),
      "launchmass": ("oz", "LAUNCHMASS", "DOUBLE", "mass"),
      "lmass": ("oz", "LAUNCHMASS", "DOUBLE", "mass"),
      "cd": (None, "CD", "DOUBLE", None),
      "motorname": (None, "MOTORNAME", "STRING", None),
      "enginename": (None, "MOTORNAME", "STRING", None),
      "nummotor": (None, "NUMMOTOR", "INTEGER", None),
      "numengine": (None, "NUMMOTOR", "INTEGER", None),
      "destination": (None, "DESTINATION", "STRING", None),
      "outfile": (None, "OUTFILE", "FILENAME", None),
      "outputfile": (None, "OUTFILE", "FILENAME", None),
      "theta": ("deg", "THETA", "DOUBLE" "angle"),
      "launchangle": ("deg", "THETA", "DOUBLE", "angle"),
}


class Dbl:
    def __init__(self, inp, unit):
        self.inp = inp
        self.unit = unit
    
    def __float__(self):
        return float(self.inp)

    def __str__(self):
        return " ".join((self.inp, self.unit))

    def conv_unit(self, unit):
        return units.conv_unit(float(self.inp), self.unit, unit)


class StageBat:
    def __init__(self):
        self.stagedelay = Dbl("0.00", "sec")
        self.diameter = Dbl("0.00", "in")
        self.numfins = 0
        self.finthickness = Dbl("0.00", "in")
        self.finspan = Dbl("0.00", "in")
        self.drymass = Dbl("0.00", "oz")
        self.launchmass = Dbl("0.00", "oz")
        self.cd = Dbl("0.75", "")
        self.motorname = ""
        self.nummotor = 1


class RocketBat:
    def __init__(self):
        self.title = "None"
        self.units = "FPS"
        self.mode = 1
        
        # self.home = eng_home    # v4.1

        self.dtime = Dbl("0.01", "sec")
        self.printtime = Dbl("0.1", "sec")
        self.printcmd = "lp -dL1"
        self.sitealt = Dbl("0.00", "ft")
        
        # AddBatDbl (& BatStru->sitetemp, "59.0", "F", 288.15)
        
        self.sitetemp = Dbl("59.0", "F")
        self.sitepress = None
        self.finalalt = Dbl("0.00", "ft")
        self.coasttime = Dbl("0.00", "sec")
        
        # self.raillength, "5.00", "ft", 1.523999995)
        
        self.raillength = Dbl("5.00", "ft")
        self.enginefile = "rasp.eng"
        self.destination = "screen"
        self.outfile = ""
        self.theta = Dbl("0.00", "deg")
        self.nosetype = "ogive"

        self.stages = []
        self.set_stages(1)

    def set_stages(self, num):
        while len(self.stages) < num:
            self.stages.append(StageBat())

    def dump(self):
        print("\nRASP Batch Dump\n")
        print("BatStru->title       = %s", self.title)
        print("BatStru->units       = %s", self.units)
        print("BatStru->mode        = %d", self.mode)
        print("BatStru->home        = %s", "NONE")  # self.home)
        print("BatStru->dtime,      = %s", str(self.dtime))
        print("BatStru->printtime   = %s", str(self.printtime))
        print("BatStru->printcmd    = %s", self.printcmd)
        print()
        print("BatStru->sitealt     = %s", str(self.sitealt))
        print("BatStru->sitetemp    = %s", str(self.sitetemp))
        print("BatStru->sitepress   = %s", str(self.sitepress))
        print("BatStru->raillength  = %s", str(self.raillength))
        print("BatStru->theta       = %s", str(self.theta.inp))
        print("BatStru->finalalt    = %s", str(self.finalalt))
        print("BatStru->coasttime   = %s", str(self.coasttime))
        print("BatStru->enginefile  = %s", self.enginefile)
        print("BatStru->destination = %s", self.destination)
        print("BatStru->outfile     = %s", self.outfile)
        print("BatStru->nosetype    = %s", self.nosetype)
        print("BatStru->numstages   = %d", len(self.stages))

        for j, stage in enumerate(self.stages):
            print()
            print("   *** stage [%d] data ***\n" % j)
            print("   diameter [%d]     = %s" % (j, stage.diameter))
            print("   numfins [%d]      = %d" % (j, stage.numfins))
            print("   finthickness [%d] = %s" % (j, stage.finthickness))
            print("   finspan [%d]      = %s" % (j, stage.finspan))
            print("   cd [%d]           = %s" % (j, stage.cd))
            print("   drymass [%d]      = %s" % (j, stage.drymass))
            print("   nummotor [%d]     = %d" % (j, stage.nummotor))
            print("   motorname [%d]    = %s" % (j, stage.motorname))
            print("   stagedelay [%d]   = %s" % (j, stage.stagedelay))
            print("   launchmass [%d]   = %s" % (j, stage.launchmass))


def to_da_moon_alice(rkt):

    flight = rasp.Flight()

    flight.rname = rkt.title
    flight.ename = rkt.enginefile
    flight.verbose = rkt.mode > 0
    flight.site_alt = rkt.sitealt
    flight.coast_base = rkt.coasttime
    flight.base_temp = rkt.sitetemp
    flight.rod = rkt.raillength

    if rkt.sitepress:
        flight.baro_press = rkt.sitepress / rasp.IN2PASCAL
    else:
        flight.baro_press = rasp.standard_press(rkt.site_alt)

    rocket = flight.rocket = rasp.Rocket()

    rocket.nose = rasp.find_nose(rkt.nosetype)

    for i, stg in enumerate(rocket.stages):
        flight.e_info.append(raspinfo.find_motor(stg.motorname))

        rocket.stages.append(rasp.Stage())
        stage = rocket.stages[-1]
        stage.engnum = stg.nummotor
        stage.weight = stg.drymass
        stage.maxd = stg.diameter / rasp.IN2M
        stage.cd = stg.cd

        # TODO: why are span and area in diff units?
        stage.fins = rasp.Fins()
        stage.fins.num = stg.numfins
        stage.fins.thickness = stg.finthickness / rasp.IN2M
        stage.fins.span = stg.finspan / rasp.IN2M
        stage.fins.area = stage.fins.num * stage.fins.thickness * rasp.IN2M \
            * stage.fins.span * rasp.IN2M

    print("Launching", flight.rname)

    fname = None
    if sys.platform == "Windows":
        if rkt.destination == "printer":
            fname = "CON"
        else:
            fname = "PRN"
    elif sys.platform == "Linux":
        if rkt.destination == "printer":
            fname = "/dev/lp"
        else:
            fname = "/dev/tty"

    if rkt.outfile:
        fname = rkt.outfile

    with open(fname, "w") as fp:
        rasp.dump_header(fp, flight)
        rasp.calc(flight)


def batch_flite(batch_file):
    # v4.2 subtle bug processing home directory ... I was writing a / at
    # the tail of * ArgBuf [2] -- Possibly on top of sombody else's data
    # space !  Adding a work buffer for doing the deed.

    if not batch_file:
        print("\nno batch file!")
        return

    try:
        with open(batch_file, "r") as fp:

            rasp_bat = RocketBat()
            stage = rasp_bat.stages[0]

            for line in fp.readlines():
                args = line.split()
                if args:
                    dfu, cmd, typ, measure = MNEMONICS[args[0].lower()]

                    itmp, dtmp, stmp = 0, 0.0, ""
                    if cmd == "TITLE":
                        if len(args) > 1:
                            rasp_bat.title = re.split(r'\s+', line, maxsplit=1)
                    elif cmd == "LAUNCH":
                        to_da_moon_alice(rasp_bat)
                    elif cmd == "QUIT":
                        return
                    elif cmd == "DUMP":
                        rasp_bat.dump()
                    elif typ == "DOUBLE":
                        if len(args) > 2:
                            src_unit = dfu
                        else:
                            src_unit = args[2]

                        # convert the units to SI
                        dtmp = units.conv_unit(measure, float(args[1]), src_unit)
                    elif typ == "INTEGER":
                        if len(args) > 1:
                            itmp = int(args[1])
                        else:
                            itmp = 0
                    else:
                        if len(args) > 1:
                            stmp = args[1]
                        else:
                            stmp = None

                    if cmd == "UNITS":
                        rasp_bat.units = stmp

                    elif cmd == "HOME":
                        if stmp[-1] != os.sep:
                            rasp_bat.home = stmp + os.sep
                        else:
                            rasp_bat.home = stmp

                    elif cmd == "MODE":
                        if len(args) > 1:
                            if args[1].lower() in ('quiet', 'summa'):
                                rasp_bat.mode = 0
                            elif args[1].lower() in ('verbose',):
                                rasp_bat.mode = 1
                            elif args[1].lower() in ('debug',):
                                rasp_bat.mode = 2
                    elif cmd == "QUIET":
                        rasp_bat.mode = 0
                    elif cmd == "VERBOSE":
                        rasp_bat.mode = 1
                    elif cmd == "DEBUG":
                        rasp_bat.mode = 2

                    elif cmd == "SITEPRESS":
                        rasp_bat.sitepress = dtmp
                    elif cmd == "FINALALT":
                        rasp_bat.finalalt = dtmp
                    elif cmd == "COASTTIME":
                        rasp_bat.coasttime = dtmp
                    elif cmd == "RAILLENGTH":
                        rasp_bat.raillength = dtmp
                    elif cmd == "ENGINEFILE":
                        rasp_bat.enginefile = stmp
                    elif cmd == "DESTINATION":
                        rasp_bat.destination = stmp
                    elif cmd == "OUTFILE":
                        rasp_bat.outfile = stmp
                    elif cmd == "THETA":
                        rasp_bat.theta = dtmp
                    elif cmd == "NUMSTAGES":
                        rasp_bat.set_stages(itmp)
                    elif cmd == "NOSETYPE":
                        rasp_bat.nosetype = stmp
                    elif cmd == "STAGE":
                        if itmp > 0:
                            rasp_bat.set_stages(itmp)
                            stage = rasp_bat.stages[itmp]
                    elif cmd == "STAGEDELAY":
                        stage.stagedelay = dtmp
                    elif cmd == "DIAMETER":
                        stage.diameter = dtmp
                    elif cmd == "NUMFINS":
                        stage.numfins = itmp
                    elif cmd == "FINTHICKNESS":
                        stage.finthickness = dtmp
                    elif cmd == "FINSPAN":
                        stage.finspan = dtmp
                    elif cmd == "DRYMASS":
                        stage.drymass = dtmp
                    elif cmd == "LAUNCHMASS":
                        stage.launchmass = dtmp
                    elif cmd == "CD":
                        stage.cd = dtmp
                    elif cmd == "MOTORNAME":
                        stage.motorname = stmp
                    elif cmd == "NUMMOTOR":
                        stage.nummotor = itmp

    except OSError as e:
        print(e.strerror, e.filename)


def main():
    print("\nRASP - Rocket Altitude Simulation Program V%s\n" % VERSION)

    print(sys.argv)
    if sys.argv:
        batch_flite(sys.argv)


if __name__ == '__main__':
    main()
