r"""
RASP89 - Rocket Altitude Simulation Program
Based on the simple BASIC program written by
Harry Stine in 1979, modified and converted
into C by Mark A. Storin, Sept/Oct 1989.
Rev 2 by Kent Hoult, June 1990.
Definitions moved to rasp.h by kjh June, 1995

10-20-89 modified to allow multiple stages up to 3.
07-01-90 modified to use linear segment engine thrust tables from data file
         smaller time increments, and crude supersonic transition drag.
6/7/93   Modified to support staging delays.
         Made changes to the supersonic transition drag equations.
         Migrated lots of global variables to local (with meaninful names)
         Rev #3  Stu Barrett
12/29/93 Added support for VAX/VMS - Rusty Whitman
02/15/94 Decrease air density with altitude/temp - added air_density()
         Make output gnuplot compatible
         Rev 3.2  - Mark C. Spiegl (spiegl@rtsg.mot.com)
06-15-95 Changed Data Entry Routines to default to previous values
         Added entry from batch file ( see vul.ovi )
         Added Usr Defined Coast Time Past Apogee
         Added Barometric Pressure --> Rho0 = f ( T, P ) Calc
         Added Launch Pad Elevation
         Added Fin Number, Thickness & Span to compute Effective
            Cross Sectional Area
         Added cd to stage structure
         Changed air_density() data table, added interpolation between
            table entries and now pass launch pad elevation.
         Consume propellant mass as a fraction of Impulse / Total Impulse
         Added M,C&B Drag Divergence Calc.

            Sharp Noses:
                  /
                 |                                 2
                 | Cd0 * ( 1.0 + 35.5 * ( M - 0.9 ) )   ( 0.9 <= M <= 1.05 )
            Cd = |
                 |        /               -5.2 * ( M - 1.05 )\
                 | Cd0 * |( 1.27 + 0.53 * e                   | ( M > 1.05 )
                 |        \                                  /
                  \

            Round Noses:
                  /
                 |                                 1.1
                 | Cd0 * ( 1.0 + 4.88 * ( M - 0.9 ) )   ( 0.9 <= M <= 1.2 )
            Cd = |
                 |        /              -5.75 * ( M - 1.2 ) \
                 | Cd0 * |( 2.0 + 0.30 * e                    | ( M > 1.2 )
                 |        \                                  /
                  \

         Added Nose Type ( O,C,E,P,B,X ) to Input For The Above
         Changed Drag Output to display Drag in Newtons
         Changed displayed Mass to Grams
         Cleaned up output
         Fixed divide by zero error for boosted dart
         Made rasp.h, n.h. units.h and parse.h
         Rev 4.0  - Konrad J. Hambrick (konrad@netcom.com, konrad@ys.com)

08-30-98 Added Processing for RASPHOME env varb.  RASPHOME can include
         multiple paths delimited by the separator in the traditional
         PATH env varb.  ( i.e. unix == ':' ; DOS == ';' ; VMS == ????? )
         RASP looks for rasp.eng in:   1. Paths in RASPHOME
                                       2. In RASP's executable path
                                       3. In the paths of PATH itself.
         ( somebody please fix VMS ;-)
         ( added module pathproc.c and pathproc.h )
         Rev 4.1 -- Konrad J. Hambrick (konrad@netcom.com, konrad@ys.com)

10-21-98 Fixed redundant fclose() in n.c::ToDaMoonAlice()
         Thanks to Jeff Taylor
         Rev 4.1b -- Konrad J. Hambrick (konrad@netcom.com, konrad@ys.com)

04-22-00 Cleaned up possible buffer overflow candidates ( strcpy / sprintf )
         Fixed bug in PathProc () -- changed return type to int ( instead
         of char * ).  From time-to-time, gdb showed the target buffer was
         initialized to a NULL pointer :-(
         Changed functions in pathproc.c to require a target buffer length
         in order to eliminate buffer overflows.
         Rev 4.2 -- Konrad J. Hambrick (konrad@netcom.com konrad@kjh-com.com)

/* kjh added this structure to make engine processing faster    */
/* what we're gonna do is:  when the engine file is referenced, */
/* open the file, read , ftell () and look for valid lines,     */
/* of a valid line is found, save ftell () in motor.offset.     */
/*                                                              */
/* When a particular motor is referenced, search this list then */
/* when found, use fseek() to jump forward to the header line.  */
/*                                                              */
/* Saved for later ...                                          */

struct motor {
    char  code[32];        /* engine name                                  */
    int   dia;             /* engine diameter    (millimeters)             */
    int   len;             /* engine length      (millimeters)             */
    char  delay[32];       /* ejection delays available raw string data    */
    double  pmass ;        /* pro mass                                     */
    double  mmass ;        /* pro mass                                     */
    char  mfg[32];         /* manufacturer info                            */
    unsigned long offset ; /* byte index into .eng file                    */
};

struct engine {
    double t2;             /* thrust duration    (seconds)                 */
    double m2;             /* propellant wt.     (kilograms)               */
    double wt;             /* initial engine wt. (kilograms)               */
    double thrust[MAXT];   /* thrust curve     (Time-sec,Thrust-Newtons)   */
    double navg;           /* average thrust     (newtons)                 */
    double ntot;           /* total impulse      (newton-seconds)          */
    double npeak;          /* peak thrust        (newtons)                 */
    int   dia;             /* engine diameter    (millimeters)             */
    int   len;             /* engine length      (millimeters)             */
    int   delay[8];        /* ejection delays available (sec)              */
    char  mfg[32];         /* manufacturer info                            */
    char  code[32];        /* engine name                                  */
};

struct nose_cone {
    char    * name ;    /* Verbose Nose Cone Name */
    int       form ;    /* M,C&B Formula to Apply */
};

   int nexteng,      /* next free engine index */
       destnum,      /* index into array of devices for output - dest */
       stagenum;     /* number of stages */
"""

import os
import sys
import math

import nc
import argparse
import raspinfo
import pathproc
from collections import defaultdict

VERSION = "4.1b"

# TODO: Use units.py
# Conversion constants
IN2M = 0.0254
GM2LB = 0.00220462
OZ2KG = 0.028349523
M2FT = 3.280840
IN2PASCAL = 3386.39

ROD = 60 * IN2M    # Length of launch rod in meters (60")
MACH0_8 = 265.168  # Mach 0.8 in Meters/sec  870 ft/sec
MACH1 = 331.460    # Mach 1.0 in Meters/sec  1086 ft/sec
MACH1_2 = 397.752  # Mach 1.2 in Meters/sec  1305 ft/sec

# kjh moved this from air.c to rasp.c
TEMP_CORRECTION = 1

G = 9.806650
DELTA_T = 0.001    # Time interval - 1ms
DT_DH = 0.006499   # degK per meter
DT_DF = 0.001981   # degK per foot
TEMP0 = 273.15     # Temp of air at Std Density at Sea Level
S_L_RHO = 1.29290  # Density of Air at STP ( 0C )
STD_ATM = 29.92    # Standard Pressure

LAUNCHALT = 0.00
MAXALT = 118415    # Where the Stratosphere begins (ft)
SPACEALT = 43610   # q&d fix

# Define the 1st character on non-data output lines. This forces output to be gnuplot compatible.

# kjh added Mach Correction for Temp
GAMMA = 1.40109                     # specific heat ratio of air
GAS_CONST_AIR = 286.90124           # ( J / Kg*K )
MACH_CONST = GAMMA * GAS_CONST_AIR

CH1 = '#'
DFILE = 'rasp.eng'

NOSES = {
    "undefined": 1,
    "ogive": 1,
    "conic": 1,
    "elliptic": 2,
    "parabolic": 2,
    "blunt": 2,
}


class Fins:
    def __init__(self):
        self.num = 0         # Number of Fins / Stage
        self.thickness = 0   # Max Thickness of Fin Stock
        self.span = 0        # Max Span of Fins from BT
    
    def area(self):
        return self.num * self.thickness * IN2M * self.span * IN2M


class Stage:
    def __init__(self):
        self.number = 1      # stage number from boosters to sustainer
        self.engnum = 1      # number of engines in stage
        self.drop_stage = 0  # When stage is dropped (includes previous stage)
        self.weight = 0      # stage wt w/o engine
        self.maxd = 0        # max diameter of stage
        self.cd = 0          # kjh added cd per stage
        self.fins = Fins()
        self.stage_delay = 0


class Rocket:
    def __init__(self, name=None):
        self.name = name
        self.nose = None
        self.stages = []

    def maxd(self, first=0):
        return max(s.maxd for s in self.stages[first:])
    
    def cd(self, first=0):
        return max(s.cd for s in self.stages[first:])


class Flight:
    def __init__(self):
        self.rocket = Rocket('dummy')
        self.fname = None
        self.rname = None
        self.ename = None
        self.e_info = []

        self.verbose = False
        self.base_temp = 0.0
        self.faren_temp = 0.0
        self.site_alt = 0.0
        self.baro_press = 0.0
        self.rod = 0.0
        self.coast_base = 0.0

        self.temp_correction = False

    def rocket_wt(self):
        # sum the result of stage_wt for each stage number
        return sum([self.stage_wt(i) for i in range(len(self.rocket.stages))])

    def stage_wt(self, num):
        # todo: num is zero-based
        stage = self.rocket.stages[num]
        return stage.weight + self.e_info[num]['wt'] * stage.engnum

    def dump_header(self, fp):
        print(CH1, file=fp)

        print("%c Rocket Name: %s" % (CH1, self.rname), file=fp)
        print("%c Motor File:  %s" % (CH1, self.ename), file=fp)

        wt = self.rocket_wt()
        for i, stage in enumerate(self.rocket.stages):
            print(CH1, file=fp)
            print("%c%5s  %-16s  %8s  %8s  %8s  %9s" % (
              CH1, "Stage", "Engine", "Bare", "Launch", "AirFrame", "Effective"), file=fp)

            print("%c%5s  %-16s  %8s  %8s  %8s  %9s  %5s" % (
              CH1, "Num", "(Qt) Type", "Weight", "Weight", "Diameter",
              "Diameter", "Cd"), file=fp)

            print("%c%5s  %-16s  %8s  %8s  %8s  %9s  %5s" % (
              CH1, "=====", "================", "========", "========",
              "========", "=========", "====="), file=fp)

            print("%c%5d  (%1d) %-12s  %8.2f  %8.2f  %8.3f  %9.3f  %5.3f" % (
              CH1, stage.number, stage.engnum, self.e_info[i]['code'],
              stage.weight / OZ2KG, self.rocket_wt() / OZ2KG, stage.maxd,
              stage.maxd + math.sqrt(stage.fins.area() / (IN2M * IN2M * math.pi)) / 2,
              stage.cd), file=fp)

            wt -= self.stage_wt(i)

            raspinfo.print_engine_header(fp)
            raspinfo.print_engine_info(self.e_info[i], fp)

        if self.verbose:
            print(CH1, file=fp)
            print("%c%4s %10s %10s %10s %11s %10s %10s" % (
                CH1, "Time", "Altitude", "Velocity", "Accel",
                "Weight", "Thrust", "Drag"), file=fp)
            print("%c%4s %10s %10s %10s %11s %10s %10s" % (
                CH1, "(Sec)", "(Feet)", "(Feet/Sec)", "(Ft/Sec^2)",
                "(Grams)", "(Newtons)", "(Newtons)"), file=fp)
            print("%c%4s %10s %10s %10s %11s %10s %10s" % (
                CH1, "-----", "---------", "---------", "---------",
                "-----------", "---------", "---------"), file=fp)


class Results:
    def __init__(self):
        self.rod = 0.0
        self.drag_bias = 0
        self.t_rod = 0.0  # launch rod info
        self.v_rod = 0.0
        self.max_accel = 0.0
        self.t_max_accel = 0.0
        self.min_accel = 0.0
        self.t_min_accel = 0.0
        self.avg_vel = 0.0
        self.max_vel = 0.0
        self.t_max_vel = 0.0
        self.max_alt = 0.0  # kjh added to save max alt
        self.t_max_alt = 0.0  # kjh added to save time to max alt
        self.mach1_0 = 0.0
        self.rho_0 = 0.0
        self.baro_press = 0.0
        self.base_temp = 0.0
        self.site_alt = 0.0
        self.vcoff = 0.00
        self.acoff = 0.00
        self.tcoff = 0.00        # kjh added for cutoff data

        # how to keep the per-stage stats?
        self.events = []
        self.start_burn = 0  # Start of engine (includes previous stage)
        self.end_burn = 0    # End of engine burn  (includes previous stage)
        self.end_stage = 0   # End of stage (includes previous stage)

        self.tee = []
        self.acc = []
        self.mass = []

    def add_event(self, time, desc):
        self.events.append((time, desc))

    def display(self, fp, verbose=False):
        for i, tee in enumerate(self.tee):
            if i % 10 == 0:
                print_alt = self.alt[i] * M2FT
                print_vel = self.vel[i] * M2FT
                print_accel = self.acc[i] * M2FT
                print_mass = self.mass[i] * 1000  # I want my Mass in Grams

                if verbose:
                    print(" %4.1lf %10.1lf %10.1lf %10.1lf %11.2lf %10.3lf %10.3lf" % (
                          tee, print_alt, print_vel, print_accel,
                          print_mass, self.thrust[i], self.drag[i]), file=fp)

        # TODO: add this
        # fprintf(stream, "%cStage %d Ignition at %5.2f sec.\n", ch1, this_stage + 1, t)

        print(CH1, file=fp)
        print("%cMaximum altitude attained = %.1lf feet (%.1lf meters)" % (
              CH1, self.max_alt * M2FT, self.max_alt), file=fp)
        print("%cTime to peak altitude =     %.2lf seconds" % (CH1, self.t_max_alt), file=fp)
        print("%cMaximum velocity =          %.1lf feet/sec at %.2lf sec" % (
                CH1, self.max_vel * M2FT, self.t_max_vel), file=fp)
        print("%cCutoff velocity =           %.1lf feet/sec at %.1lf feet ( %.2lf sec )" % (
               CH1, self.vcoff * M2FT, self.acoff * M2FT, self.tcoff), file=fp)
        print("%cMaximum acceleration =      %.1lf feet/sec^2 at %.2lf sec" % (
               CH1, self.max_accel * M2FT, self.t_max_accel), file=fp)
        print("%cMinimum acceleration =      %.1lf feet/sec^2 at %.2lf sec" % (
               CH1, self.min_accel * M2FT, self.t_min_accel), file=fp)
        print("%cLaunch rod time =  %.2lf,  rod len   = %.1lf,       velocity  = %.1lf" % (
               CH1, self.t_rod, self.rod * M2FT, self.v_rod), file=fp)
        print("%cSite Altitude =   %5.0lf,  site temp = %.1lf F" % (
               CH1, self.site_alt * M2FT, ((self.base_temp - 273.15) * 9 / 5) + 32), file=fp)
        print("%cBarometer     =   %.2f,  air density = %.4lf,  Mach vel  = %.1lf" % (
              CH1, self.baro_press, self.rho_0, self.mach1_0 * M2FT),
              file=fp)


def get_str(prompt, default):
    entry = input(f"{prompt} [{default}]  ")
    entry = entry.strip()

    if not entry:
        return default

    return entry


def get_int(prompt, default):
    while True:
        entry = get_str(prompt, default)

        try:
            return int(entry)
        except ValueError:
            print("Bad Value")


def get_float(prompt, default):
    while True:
        entry = get_str(prompt, default)

        try:
            return float(entry)
        except ValueError:
            print("Bad Value")


def standard_press(alt):
    return STD_ATM * math.exp(5.256 * math.log(1 - (0.00000688 * alt * M2FT)))


def choices(defaults):
    flight = Flight()

    flight.rname = get_str("Rocket Name", defaults['rname'])
 
    stagenum = get_int("Number of Stages", 1)

    flight.rocket = rocket = Rocket()

    for num in range(stagenum):
        flight.e_info.append(raspinfo.get_motor(defaults['ename']))

        stage = Stage()
        rocket.stages.append(stage)
        stage.number = num + 1

        prompt = f"Number of engines" + f" in Stage {num + 1}" if num > 0 else ""

        stage.engnum = get_int(prompt, defaults['engnum'])
 
        if num == 0:
            rocket.nose = get_nose("Nose (<O>give,<C>onic,<E>lliptic,<P>arabolic,<B>lunt)",
                                   defaults['nose'])
        if stagenum > 1:
            prompt = f"Weight of Stage {num + 1} w/o Engine in Ounces"
        else:
            prompt = f"Weight of Rocket w/o Engine in Ounces"

        # Remember the weight from run to run
        stage.weight = get_float(prompt, 0)

        if stagenum > 1:
            prompt = f"Maximum Diameter of Stage {num + 1} in Inches"
        else:
            prompt = f"Maximum Body Diameter in Inches"
 
        stage.maxd = get_float(prompt, defaults['maxd'])
 
        if stagenum > 1:
            prompt = f"Number of Fins on Stage {num + 1}"
        else:
            prompt = f"Number of Fins"

        fins = stage.fins = Fins()
        fins.num = get_int(prompt, defaults['fins_num'])
 
        if fins.num == 0:
            fins.thickness = 0.0
            fins.span = 0.0
        else:
            if stagenum > 1:
                prompt = f"Max Thickness of Fins on Stage {num + 1} (Inches) "
            else:
                prompt = f"Max Thickness of Fins (Inches) "
 
            fins.thickness = get_float(prompt, defaults['fins_thickness'])
 
            if stagenum > 1:
                prompt = f"Max Span of Fins on Stage {num + 1} (Inches -- From BT, Out) "
            else:
                prompt = f"Max Span of Fins (Inches -- From BT, Out) "

            fins.span = get_float(prompt, defaults['fins_span'])

        if stagenum > 1:
            prompt = f"Drag Coefficient of Rocket From Stage {num + 1}, Up "
        else:
            prompt = f"Drag Coefficient "

        stage.cd = get_float(prompt, defaults['cd'])
 
        if num + 1 < stagenum:
            prompt = f"Staging Delay for Stage {num + 2} in Seconds"
            stage.stage_delay = get_float(prompt, defaults['stage_delay'])
        else:
            stage.stage_delay = 0

    # Environmental Data
    flight.site_alt = get_float("Launch Site Altitude in Feet", defaults['site_alt'] * M2FT) / M2FT
    flight.faren_temp = get_float("Air Temp in DegF", defaults['faren_temp'])
 
    flight.base_temp = (flight.faren_temp - 32) * 5 / 9 + 273.15  # convert to degK
 
    baro_press = standard_press(flight.site_alt)
    flight.baro_press = get_float("Barometric Pressure at Launch Site", baro_press)
 
    flight.rod = get_float("Launch Rod Length ( inch )", defaults['rod'] / IN2M) * IN2M

    flight.coast_base = get_float("Coast Time (Enter 0.00 for Apogee)", defaults['coast_base'])
 
    destnum = get_int("Send Data to:\n\t(1) Screen\n\t(2) Printer\n\t(3) Disk file\nEnter #", 1)

    if destnum == 1:
        if sys.platform == 'Win32':
            flight.fname = "CON"
        elif sys.platform == "Linux":
            flight.fname = "/dev/tty"
        elif sys.platform == 'VMS':
            flight.fname = "TT:"
    elif destnum == 2:
        if sys.platform == 'Win32':
            flight.fname = "PRN"
        elif sys.platform == "Linux":
            flight.fname = "/dev/lp"
        elif sys.platform == 'VMS':
            flight.fname = "LP:"
    else:
        bname = get_str("Enter File Base Name", None)
        fname = '.'.join([bname, flight.e_info[0].code])
        flight.fname = get_str("Enter File Name", fname)

    return flight


def calc(flight):
    stage_time = 0.0                  # elapsed time for current stage
    burn_time = 0.0                   # Elapsed time for motor burn
    thrust_index = 0                  # index into engine table
    start_burn = 0
    coast_time = 0.00                 # kjh to coast after burnout
    drag = 0.0                        # kjh added to print Drag in Nt
    alt = LAUNCHALT
    vel = 0.0
    sum_o_thrust = 0.0                # kjh added to reduce pro mass ~ thrust
    old_thrust = 0.0                  # last engine thrust from table
    old_time = 0.0                    # last engine thrust time from table
    launched = False                  # indicates rocket has lifted off
    
    results = Results()

    results.mach1_0 = math.sqrt(MACH_CONST * flight.base_temp)
    results.baro_press = flight.baro_press
    results.base_temp = flight.base_temp
    results.site_alt = flight.site_alt

    # rho == Air Density for drag calc
    results.rho_0 = (flight.baro_press * IN2PASCAL) / (GAS_CONST_AIR * flight.base_temp)

    mass = flight.rocket_wt()

    stage = flight.rocket.stages[0]
    engine = flight.e_info[0]
     
    # figure start and stop times for motor burn and stage
    end_burn = engine['t2']
    end_stage = end_burn + stage.stage_delay

    # What is the effective Diameter and drag coeff
    stage_diam = flight.rocket.maxd()
    drag_coff = flight.rocket.cd()
        
    # c = r * M_PI * drag_coff * d * d * 0.125;
    # c = r * drag_constant

    # kjh wants to see thrust at t=0 if there is any ...
    results.tee = [0.0]
    results.alt = [LAUNCHALT]
    results.vel = [0.0]
    results.acc = [0.0]
    results.mass = [mass]
    t, thrust = engine['thrust'][0]
    if t == 0.0 and thrust != 0.0:
        results.acc = [(thrust - drag) / mass - G]
  
    # Launch Loop
    t = 0.000000
    while True:
        # Calculate decreasing air density

        # todo: r = air_density (alt,site_alt,base_temp);
        y = results.alt[-1]
        if y > SPACEALT:
            r = 0
        elif y > MAXALT:
            # r = 1.7187 * exp(-1.5757e-4 * y);
            r = 1.9788 * math.exp(-1.5757e-4 * y)
        else:
            r = results.rho_0 * math.exp(4.255 * math.log(1 - (y * 2.2566e-5)))

        if flight.temp_correction:
            dt = isa_temp(flight.base_temp, y)
            results.mach1_0 = math.sqrt(MACH_CONST * dt)

        # is this a result?
        d = stage_diam * IN2M
        drag_constant = 0.5 * drag_coff * ((math.pi * d * d * 0.25) + stage.fins.area())

        c = r * drag_constant

        t += DELTA_T
        stage_time += DELTA_T

        # handle staging, if needed
        if t > end_stage and stage.number < len(flight.rocket.stages):
            thrust_index = 0
            old_thrust = 0.0
            sum_o_thrust = 0.0
            old_time = 0.0

            # this gets the next stage due to offset between number and index
            stage = flight.rocket.stages[stage.number]
            engine = flight.e_info[stage.number]
            
            stage_wt = flight.stage_wt(stage.number - 1)
            mass -= stage_wt

            stage_time = burn_time = 0
            start_burn = t
            end_burn = start_burn + engine.t2
            end_stage = end_burn + stage.stage_delay
            results.add_event(t, 'start_burn stage {stage.number}')
            results.add_event(t, 'end_burn stage {stage.number}')

            # What is the effective Diameter and drag coeff of remaining stages
            stage_diam = flight.rocket.maxd(stage.number - 1)
            drag_coff = flight.rocket.cd(stage.number - 1)

            """
                 1
            c = --- * PI * d ^ 2 * R * k
                 8
            
                 1
              = --- * PI * r ^ 2 * R * k
                 2
            
                              m^2 * kg
              =  A * R * k   ----------
                              m^3
                 kg
              = ----
                 m
            """
            # c = r * M_PI * drag_coff * d * d * 0.125

            d = stage_diam * IN2M
            drag_constant = 0.5 * drag_coff * ((math.pi * d * d * 0.25) + stage.fins.area())

            c = r * drag_constant

            # TODO: move this to an event
            results.events.append((t, f"Stage {stage.number} ignition"))

        # Handle the powered phase of the boost
        if start_burn <= t <= end_burn:
            burn_time += DELTA_T  # add to burn time

            time_val, thrust_val = engine['thrust'][thrust_index]

            # see if we need to use the next thrust point
            # All times are relative to burn time for these calculations
            if burn_time > time_val:
                old_time = time_val
                old_thrust = thrust_val

                thrust_index += 1
                time_val, thrust_val = engine['thrust'][thrust_index]

            # Logic to smooth transition between thrust points.
            # Transitions are linear rather than discontinuous
            thrust = thrust_val - old_thrust
            thrust *= (burn_time - old_time) / (time_val - old_time)
            thrust += old_thrust
            thrust *= stage.engnum

            # kjh changed this to consume propellant at thrust rate
            sum_o_thrust += (thrust * DELTA_T)
            m1 = sum_o_thrust / (engine['ntot'] * stage.engnum)
            m1 *= engine['m2'] * stage.engnum

            # This is the Original Method
            #
            # m1 = (engine.m2 / engine.t2) * DELTA_T
            # stage_wt -= m1
            # mass = rocketwt -= m1
            #
            # fprintf ( stderr, "Sum ( %f ) = %10.2f  ;  Mass = %10.6f\n", burn_time, sum_o_thrust, m1 )

            mass -= m1
        else:
            thrust = 0.0

            if results.tcoff == 0.0 and stage == flight.rocket.stages[-1]:
                results.tcoff = t
                results.vcoff = results.vel[-1]
                results.acoff = results.alt[-1]

        """
        Crude approximations for MACH 1 Transition.
        the drag bias will be applied to the subsonic value.
        It will be equal to 1.0 for velocities less than MACH 0.8.
        From MACH 0.8 to MACH 1.0 it will increase linearly to 2.0 times
        the subsonic value.  From MACH 1.0 to MACH 1.2 it will decrease to
        1.5 times the subsonic value.  Above MACH 1.2 it will remain at
        a value of 1.5
        """

        # average last two vel values
        results.avg_vel = sum(results.vel[-2:]) / 2

        # kjh Added M,C&B Model for TransSonic Region
        results.drag_bias = drag_diverge(flight.rocket.nose, results.mach1_0, vel)

        """
        # kjh replaced this with DragDiverge
        if (vel < mach0_8)
            drag_bias = 1;
        elif vel < mach1_0)
            drag_bias = (1.0 + ((vel - mach0_8) / (mach1_0 - mach0_8)));
        elif vel < mach1_2)
            drag_bias = (2.0 - 0.5*((vel - mach1_0) / (mach1_2 - mach1_0)));
        else
            drag_bias = 1.5;
        """

        cc = c * results.drag_bias

        """
        /* Simple Newton calculations
        /* kjh changed for coasting after burnout
        
        /* cc                         = kg / m
        /* accel                      = m / sec^2

        /* kg  *    m *    m                m
        /* -------------------------  =  ------
        /*  m  *  sec *  sec *   kg       sec^2
        """

        # kjh added to compute drag and report it in N
        # drag = - ( cc * vel * vel ) ;
        drag = - (cc * results.avg_vel * results.avg_vel)  # kjh changed this 05-23-96

        if launched and results.vel[-1] <= 0:
            drag = - drag
            accel = (drag / mass) - G  # kjh added this */
        else:
            accel = ((thrust + drag) / mass) - G

        vel = vel + accel * DELTA_T
        alt = alt + vel * DELTA_T

        results.tee.append(t)
        results.acc.append(accel)
        results.vel.append(vel)
        results.alt.append(alt)
        results.mass.append(mass)

        # test for lift-off and apogee
        if vel > 0:
            launched = 1  # LIFT-OFF
        elif not launched and vel < 0:
            alt = vel = accel = 0  # can't fall off pad!
        elif launched and vel < 0:
            coast_time += DELTA_T  # time past burnout

            if (alt <= 0.0) or (coast_time > flight.coast_base):  # kjh to coast a while
                break  # apogee, all done

        if alt <= flight.rod and vel > 0:
            results.t_rod = t
            results.v_rod = vel * M2FT

        # do max evaluations
        if accel > results.max_accel:
            results.max_accel = accel
            results.t_max_accel = t

        elif accel < results.min_accel:
            results.min_accel = accel
            results.t_min_accel = t

        if vel > results.max_vel:
            results.max_vel = vel
            results.t_max_vel = t

        if alt > results.max_alt:
            results.max_alt = alt
            results.t_max_alt = t

    return results


def display_flight(flight, fp):
    for stage in range(len(flight.rocket.stages)):
        print("%cStage Weight [%d]:  %9.4f" % (CH1, stage + 1, flight.totalwt(stage)), file=fp)


def parse_commandline():
    global args, parser

    parser = argparse.ArgumentParser(prog='raspinfo', description=f'Dump RASP engine info (v{VERSION})')
    parser.add_argument('-d', '--debug', action='store_true', help='debug output')
    parser.add_argument('-q', '--quiet', action='store_true', help="be quiet about it")
    parser.add_argument('--version', action='version', version=f'v{VERSION}')
    parser.add_argument('raspfiles', nargs='*', help="rasp batch files")

    args = parser.parse_args()


def main():
    print("\nRASP - Rocket Altitude Simulation Program V", VERSION)

    parse_commandline()
    
    # v4.1 do the Home bit
    rasp_home = os.environ["RASPHOME"] if "RASPHOME" in os.environ else None

    # is the full path available?
    prog_name = pathproc.base_name(sys.argv[0])
    if prog_name == sys.argv[0]:
        # search for __main__
        prog_name = pathproc.whereis(sys.argv[0])
    else:
        prog_name = sys.argv[0]  # fqpn in sys.argv[0]

    ename = pathproc.whereis(DFILE, rasp_home, prog_name)
    eng_home = pathproc.dir_name(ename)

    if args.debug:
        print("RASP Home = ", rasp_home)
        print("Eng Home  = ", eng_home)
        print("Prog Name = ", prog_name)
        print("Eng File  = ", ename)

    # default values for choices
    defaults = defaultdict()
    defaults['faren_temp'] = 59
    defaults['site_alt'] = LAUNCHALT / M2FT
    defaults['baro_press'] = STD_ATM
    defaults['rod'] = ROD

    # this is the batch mode block ( see n.c )
    if args.raspfiles:
        for rasp in args.raspfiles:
            nc.batch_flite(rasp)
    else:
        while True:
            flight = choices(defaults)

            with open(flight.fname) as fp:
                flight.dump_header(fp)
                results = calc(flight)

            ans = input("\nDo Another One? ")
            if ans == "y" or ans == "Y":
                print()
            else:
                break


def find_nose(nose):
    for name, shape in NOSES.items():
        if name.startswith(nose.lower()):
            return name

    return None


def get_nose(prompt, default):
    got_one = None

    while not got_one:
        entry_str = input(f"{prompt} [{default.capitalize()}]:  ")
        if not entry_str:
            return default
            
        got_one = find_nose(entry_str)

    return got_one


def drag_diverge(nose_type, mach_1, velocity):

    mach_number = velocity / mach_1

    if mach_number <= 0.9 or mach_number <= 0.0:
        return 1.0

    if NOSES[nose_type] == 2:  # Rounded Noses
        if mach_number <= 1.2:
            diverge = 1.0 + 4.88 * (mach_number - 0.9) ** 1.1
        elif mach_number < 2.0:
            diverge = 2.0 + 0.30 * math.exp(-5.75 * (mach_number - 1.2))
        else:
            diverge = 2.0
    else:  # Sharp Noses
        if mach_number <= 1.05:
            diverge = mach_number - 0.9
            diverge *= diverge
            diverge = 1.0 + 35.5 * diverge
        elif mach_number < 2.0:
            diverge = 1.27 + 0.53 * math.exp(-5.2 * (mach_number - 1.05))
        else:
            diverge = 1.27
          
    return diverge


def isa_temp(base_temp, alt):
    if alt <= 11000:
        dt = base_temp - alt * 0.0065
    elif alt <= 20000:
        dt = 216.65
    elif alt <= 32000:
        dt = 228.65 + (alt - 32000) * 0.0010
    elif alt <= 47000:
        dt = 228.65 + (alt - 47000) * 0.0028
    elif alt <= 51000:
        dt = 270.65
    elif alt <= 71000:
        dt = 214.65 - (alt - 71000) * 0.0028
    elif alt <= 84852:
        dt = 186.95 - (alt - 84852) * 0.0020
    else:
        dt = 186.95

    if dt < 0:
        dt = 0.0

    return dt
