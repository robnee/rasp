"""
 * RASP89 - Rocket Altitude Simulation Program
 * Based on the simple BASIC program written by
 * Harry Stine in 1979, modified and converted
 * into C by Mark A. Storin, Sept/Oct 1989.
 * Rev 2 by Kent Hoult, June 1990.
 * Definitions moved to rasp.h by kjh June, 1995
 *
 * 10-20-89 modified to allow multiple stages up to 3.
 * 07-01-90 modified to use linear segment engine thrust tables from data file
 *          smaller time increments, and crude supersonic transition drag.
 * 6/7/93   Modified to support staging delays.
 *          Made changes to the supersonic transition drag equations.
 *          Migrated lots of global variables to local (with meaninful names)
 *          Rev #3  Stu Barrett
 * 12/29/93 Added support for VAX/VMS - Rusty Whitman
 * 02/15/94 Decrease air density with altitude/temp - added air_density()
 *          Make output gnuplot compatible
 *          Rev 3.2  - Mark C. Spiegl (spiegl@rtsg.mot.com)
 * 06-15-95 Changed Data Entry Routines to default to previous values
 *          Added entry from batch file ( see vul.ovi )
 *          Added Usr Defined Coast Time Past Apogee
 *          Added Barometric Pressure --> Rho0 = f ( T, P ) Calc
 *          Added Launch Pad Elevation
 *          Added Fin Number, Thickness & Span to compute Effective
 *             Cross Sectional Area
 *          Added cd to stage structure
 *          Changed air_density() data table, added interpolation between
 *             table entries and now pass launch pad elevation.
 *          Consume propellant mass as a fraction of Impulse / Total Impulse
 *          Added M,C&B Drag Divergence Calc.
 *
 *             Sharp Noses:
 *                   /
 *                  |                                 2
 *                  | Cd0 * ( 1.0 + 35.5 * ( M - 0.9 ) )   ( 0.9 <= M <= 1.05 )
 *             Cd = |
 *                  |        /               -5.2 * ( M - 1.05 )\
 *                  | Cd0 * |( 1.27 + 0.53 * e                   | ( M > 1.05 )
 *                  |        \                                  /
 *                   \
 *
 *             Round Noses:
 *                   /
 *                  |                                 1.1
 *                  | Cd0 * ( 1.0 + 4.88 * ( M - 0.9 ) )   ( 0.9 <= M <= 1.2 )
 *             Cd = |
 *                  |        /              -5.75 * ( M - 1.2 ) \
 *                  | Cd0 * |( 2.0 + 0.30 * e                    | ( M > 1.2 )
 *                  |        \                                  /
 *                   \
 *
 *          Added Nose Type ( O,C,E,P,B,X ) to Input For The Above
 *          Changed Drag Output to display Drag in Newtons
 *          Changed displayed Mass to Grams
 *          Cleaned up output
 *          Fixed divide by zero error for boosted dart
 *          Made rasp.h, n.h. units.h and parse.h
 *          Rev 4.0  - Konrad J. Hambrick (konrad@netcom.com, konrad@ys.com)
 *
 * 08-30-98 Added Processing for RASPHOME env varb.  RASPHOME can include
 *          multiple paths delimited by the separator in the traditional
 *          PATH env varb.  ( i.e. unix == ':' ; DOS == ';' ; VMS == ????? )
 *          RASP looks for rasp.eng in:   1. Paths in RASPHOME
 *                                        2. In RASP's executable path
 *                                        3. In the paths of PATH itself.
 *          ( somebody please fix VMS ;-)
 *          ( added module pathproc.c and pathproc.h )
 *          Rev 4.1 -- Konrad J. Hambrick (konrad@netcom.com, konrad@ys.com)
 *
 * 10-21-98 Fixed redundant fclose() in n.c::ToDaMoonAlice()
 *          Thanks to Jeff Taylor
 *          Rev 4.1b -- Konrad J. Hambrick (konrad@netcom.com, konrad@ys.com)
 *
 * 04-22-00 Cleaned up possible buffer overflow candidates ( strcpy / sprintf )
 *          Fixed bug in PathProc () -- changed return type to int ( instead
 *          of char * ).  From time-to-time, gdb showed the target buffer was
 *          initialized to a NULL pointer :-(
 *          Changed functions in pathproc.c to require a target buffer length
 *          in order to eliminate buffer overflows.
 *          Rev 4.2 -- Konrad J. Hambrick (konrad@netcom.com konrad@kjh-com.com)
 */
"""

import math
import raspinfo

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

#define MAXINTLEN    6
#define MAXLONGLEN   11
#define MAXDBLLEN    17
#define MAXSTRLEN    256

#define DFILE "rasp.eng"

NOSES = [
    ("undefined", 1),
    ("ogive", 1),
    ("conic", 1),
    ("elliptic", 2),
    ("parabolic", 2),
    ("blunt", 2),
]


class Fins:
    def __init__(self):
        self.num = 0         # Number of Fins / Stage
        self.thickness = 0   # Max Thickness of Fin Stock
        self.span = 0        # Max Span of Fins from BT
        self.area = 0        # Computed Once to run faster


class Stage:
    def __init__(self):
        self.engnum = 0      # number of engines in stage
        self.start_burn = 0  # Start of engine (includes previous stage)
        self.end_burn = 0    # End of engine burn  (includes previous stage)
        self.end_stage = 0   # End of stage (includes previous stage)
        self.drop_stage = 0  # When stage is dropped (includes previous stage)
        self.weight = 0      # stage wt w/o engine
        self.maxd = 0        # max diameter of stage
        self.cd = 0          # kjh added cd per stage
        self.fins = Fins()
        self.o_wt = 0        # kjh added to remember weight run-to-run


class Rocket:
    def __init__(self):
        self.nose = None
        self.stages = []


class Flight:
    def __init__(self):
        self.rocket = None
        self.rname = None
        self.ename = None
        self.e_info = None  #

        self.verbose = False
        self.rocketwt = 0.0
        self.drag_coff = 0.0
        self.base_temp = 0.0
        self.faren_temp = 0.0
        self.mach1_0 = 0.0
        self.site_alt = 0.0
        self.baro_press = 0.0
        self.rho_0 = 0.0
        self.rod = 0.0
        self.coast_base = 0.0


"""

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

#define RASP_BUF_LEN    1024
#define RASP_FILE_LEN   PATH_MAX + NAME_MAX + 2    /* from pathproc.h v4.1 */

struct motor_entry {
   char MEnt [ RASP_BUF_LEN + 1 ] ;
} ;


# Define the 1st character on non-data output lines. This forces
# output to be gnuplot compatible.
#ifdef VMS
   char ch1 = '!';
#else
   char ch1 = '#';
#endif

   /*
    * Global Variables
    */

   char FloatChars [] = { "0123456789.EeFfGg+-" };

   int nexteng,      /* next free engine index */
       destnum,      /* index into array of devices for output - dest */
       stagenum;     /* number of stages */

   char Mcode [ RASP_BUF_LEN + 1 ];  /* array to hold engine code */

   char rname [ RASP_BUF_LEN + 1 ];  /* rocket name */
   char oname [ RASP_BUF_LEN + 1 ];  /* old rocket name */
   char bname [ RASP_FILE_LEN + 1 ]; /* output file base name for simulation */
   char fname [ RASP_FILE_LEN + 1 ]; /* output file name for simulation */
   char ename [ RASP_FILE_LEN + 1 ]; /* Holds Motor File Name */

   char PrgName [ RASP_FILE_LEN + 1 ];  /* v4.1 -- program Name */
   char EngHome [ RASP_FILE_LEN + 1 ];  /* v4.1 -- Engine  Home */
   char * RaspHome ;                    /* v4.1 -- getenv ( "RASPHOME" ) */

   FILE *stream,  *efile;

   int verbose;

   char DELIM [] = {" ,()" };

"""


def find_nose(nose):
    return NOSES[nose]


def dump_header(fp, flight):
    print(CH1, file=fp)

    print("%c Rocket Name: %s" % (CH1, flight.rname), file=fp)
    print("%c Motor File:  %s" % (CH1, flight.ename), file=fp)

    wt = flight.rocketwt
    for i, stage in enumerate(flight.rocket.stages):
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
          CH1, i + 1, stage.engnum, flight.e_info[i].code,
          stage.weight / OZ2KG, flight.rocketwt / OZ2KG, stage.maxd,
          stage.maxd + math.sqrt(stage.fins.area / (IN2M * IN2M * math.pi)) / 2,
          stage.cd), file=fp)

        wt -= stage.weight + flight.e_info[i].wt * stage.engnum

        raspinfo.print_engine_info(flight.e_info[i])

    if flight.verbose:
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


"""


/*************************************************************************/
void choices()
/*************************************************************************/
{
   int i;
   double wt;
   double stage_delay = 0;

   /* kjh Changed it */


   GetStr ( "Rocket Name", rname, RASP_BUF_LEN ) ;

   if ( strcmp ( rname, oname ) != 0 )
   {
      strncpy ( oname, rname, RASP_BUF_LEN );
      bname [ 0 ] = '\0' ;
   }

   stagenum = GetInt ( "Number of Stages", stagenum ) ;

   for (i = 0; i < stagenum; i++)
   {

      stages[i].engcnum = getmotor ( i + 1 );

      /* kjh Changed it */

      if (stagenum > 1)
          sprintf ( PROMPT, "Number of Engines in Stage %d", i+1 );
      else
          sprintf ( PROMPT,  "Number of engines" );

      stages[i].engnum = GetInt ( PROMPT, stages[i].engnum );

      /* kjh Added it */

      if ( i == 0 )
         Nose = GetNose ( "Nose ( <O>give,<C>onic,<E>lliptic,<P>arabolic,<B>lunt )", Nose );

      /* kjh Changed it */

      if (stagenum > 1)
         sprintf ( PROMPT, "Weight of Stage %d w/o Engine in Ounces", i+1 ) ;
      else
         sprintf ( PROMPT, "Weight of Rocket w/o Engine in Ounces" ) ;

      o_wt[i] = GetDbl ( PROMPT, o_wt[i] );

      stages[i].weight = o_wt[i] * OZ2KG;

      /* kjh Changed it */

      if (stagenum > 1)
          sprintf ( PROMPT, "Maximum Diameter of Stage %d in Inches", i + 1 );
      else
          sprintf ( PROMPT, "Maximum Body Diameter in Inches" ) ;

      stages[i].maxd = GetDbl ( PROMPT, stages[i].maxd );

      /* kjh Added it */

      if (stagenum > 1)
          sprintf ( PROMPT, "Number of Fins on Stage %d", i + 1 );
      else
          sprintf ( PROMPT, "Number of Fins" ) ;

      fins[i].num = GetInt ( PROMPT, fins[i].num );

      /* kjh Added it */

      if ( fins[i].num == 0 )
      {
         fins[i].thickness = 0.0;
         fins[i].span = 0.0 ;
      }
      else
      {
         if (stagenum > 1)
             sprintf ( PROMPT, "Max Thickness of Fins on Stage %d (Inches) ", i + 1 );
         else
             sprintf ( PROMPT, "Max Thickness of Fins (Inches) " ) ;

         fins[i].thickness = GetDbl ( PROMPT, fins[i].thickness );

         /* kjh Added it */

         if (stagenum > 1)
         {
             sprintf ( PROMPT,
                       "Max Span of Fins on Stage %d (Inches -- From BT, Out) ",
                       i + 1 );
         }
         else
         {
             sprintf ( PROMPT, "Max Span of Fins (Inches -- From BT, Out) " ) ;
         }

         fins[i].span = GetDbl ( PROMPT, fins[i].span );
      }

      fins[i].area = fins[i].num * fins[i].thickness * fins[i].span
                                 * IN2M              * IN2M;

      /* kjh Added it */

      if (stagenum > 1)
      {
          sprintf ( PROMPT,
                    "Drag Coefficient of Rocket From Stage %d, Up ", i + 1 );
      }
      else
      {
          sprintf ( PROMPT, "Drag Coefficient " ) ;
      }

      stages[i].cd = GetDbl ( PROMPT, stages[i].cd );

      if (i + 1 < stagenum)
      {

          /* kjh Changed it */

         sprintf ( PROMPT, "Staging Delay for Stage %d in Seconds", i + 2 ) ;
         stage_delay = GetDbl ( PROMPT, stage_delay ) ;
      }

      /* figure start and stop times for motor burn  and stage */

      if (i == 0)
         stages[i].start_burn = 0;
      else
         stages[i].start_burn = stages[i-1].end_stage;

      stages[i].end_burn = stages[i].start_burn + e_info[stages[i].engcnum].t2;
      stages[i].end_stage = stages[i].end_burn + stage_delay;

      /* figure weight for stage and total rocket */

      stages[i].totalw = stages[i].weight +
                         (e_info[stages[i].engcnum].wt * stages[i].engnum);

      rocketwt += stages[i].totalw;

   }

   /* Environmental Data */

   /* kjh added it */

   site_alt *= M2FT ;

   site_alt = GetDbl ("Launch Site Altitude in Feet", site_alt );

   site_alt /= M2FT ;

   /* kjh Changed it */

   faren_temp = GetDbl ("Air Temp in DegF", faren_temp );

   base_temp = (faren_temp - 32) * 5/9 + 273.15;  /* convert to degK */

   mach1_0 = sqrt ( MACH_CONST * base_temp ) ;

   /* kjh added it */

   baro_press = 1 - ( 0.00000688 * site_alt * M2FT ) ;
   baro_press =  STD_ATM * exp ( 5.256 * log ( baro_press )) ;

   baro_press  = GetDbl ("Barometric Pressure at Launch Site", baro_press );

   Rho_0 = ( baro_press * IN2PASCAL ) / ( GAS_CONST_AIR * base_temp ) ;

   /* kjh added it */

   Rod = Rod / IN2M ;
   Rod = GetDbl ("Launch Rod Length ( inch )", Rod ) ;
   Rod = Rod * IN2M ;

   /* kjh Changed it */

   coast_base = GetDbl ( "Coast Time (Enter 0.00 for Apogee)", coast_base );

   /* destnum = 1;        kjh changed this */

   do
   {

      /* kjh changed it */

      destnum = GetInt ( "Send Data to:\n\t(1) Screen\n\t(2) Printer\n\t(3) Disk file\nEnter #", destnum );

#ifdef MSDOS

      if ( destnum == 1 )
         strncpy ( fname, "CON", RASP_FILE_LEN );
      elif destnum == 2 )
         strncpy ( fname, "PRN", RASP_FILE_LEN );

#endif

#ifdef UNIX

      if ( destnum == 1 )
         strncpy ( fname, "/dev/tty", RASP_FILE_LEN ) ;
      elif destnum == 2 )
         strncpy ( fname, "/dev/lp", RASP_FILE_LEN );

#endif

#ifdef VMS

      if ( destnum == 1 )
         strncpy ( fname, "TT:", RASP_FILE_LEN );
      elif destnum == 2 )
         strncpy ( fname, "LP:", RASP_FILE_LEN );

#endif

      else
      {
         /* kjh added this */

         for ( i = 0 ; i < strlen ( Mcode ) ; i++ )
             if ( isupper ( Mcode[i] ))
                Mcode[i] = tolower ( Mcode[i] );

          if ( strlen ( bname ) == 0 )
            GetStr ( "Enter File Base Name", bname, RASP_BUF_LEN ) ;

          /* v4.2 user input here -- candidate for buffer overflow ... */

#ifdef HAS_SNPRINTF
          snprintf ( fname, RASP_FILE_LEN, "%s.%s", bname, Mcode ) ;
#else
          sprintf ( fname, "%s.%s", bname, Mcode ) ;
#endif

          /* kjh changed this */

          GetStr ( "Enter File Name", fname ,RASP_BUF_LEN ) ;
      }

      if ((stream = fopen(fname,"w")) == NULL)
         fprintf ( stderr, "%s cannot be opened.\n",fname);

   } while (stream == NULL);

   wt = rocketwt;

   dumpheader ( wt ) ;
}

"""


def calc(flight):
    thrust_index = 0                  # index into engine table
    stage_engcnum = 0                 # engcnum for current stage
    this_stage = 0                    # current stage
    stage_time = 0.0                  # elapsed time for current stage
    burn_time = 0.0                   # Elapsed time for motor burn
    stage_wt = 0.0                    # current wt of this_stage
    stage_diam = 0.0                  # max diam at current time
    t_rod = 0.0                       # launch rod info
    v_rod = 0.0
    cc = 0
    drag_bias = 0
    thrust = 0.0                      # Thrust
    vel = 0.0                         # Velocity
    accel = 0.0                       # Acceleration
    alt = LAUNCHALT                   # Altitude
    print_vel = False
    print_alt = False
    print_accel = False
    print_mass = False                # used for printing

    mass = 0.0
    t = 0.000000
    max_accel = 0.0
    t_max_accel = 0.0
    min_accel = 0.0
    t_min_accel = 0.0
    max_vel = 0.0
    t_max_vel = 0.0
    max_alt = 0.0                     # kjh added to save max alt
    max_t = 0.0                       # kjh added to save time to max alt
    drag = 0.0                        # kjh added to print Drag in Nt

    old_vel = 0.0                     # kjh added to avg vel in interval
    avg_vel = 0.0                     # kjh ditto

    sum_o_thrust = 0.0                # kjh added to reduce pro mass ~ thrust

    old_thrust = 0.0                  # last engine thrust  from table
    old_time = 0.0                    # last engine thrust time  from table

    print_index = 0                   # used for print loop
    launched = 0                      # indicates rocket has lifted off

    delta_t = 0.001                   # Time interval - 1us
    ten_over_delta_t = 100
    r = Rho_0                         # rho == Air Density for drag calc

# double air_density()                # kjh put this inline

    drag_constant = 0.0               # compute once-per-stage
    coast_time = 0.00                 # kjh to coast after burnout

    vcoff = 0.00
    acoff = 0.00
    tcoff = 0.00                      # kjh added for cutoff data

    dT = 0                            # change in temp vs altitude

    stage_wt = stages[this_stage].totalw

    stage_engcnum = stages[this_stage].engcnum
    mass = rocketwt

   
#  for ( j=0 ; j < stagenum ; j++ )
#     fprintf ( stream, "%cStage Weight [%d]:  %9.4f\n", ch1, j, stages[j].totalw );

   # What is the effective Diameter

    prev_stage = None
    for stage in flight.rocket.stages:
        stage_diam = stage.maxd
        drag_coff = stage.cd          # kjh Added This

        if prev_stage:
            if stage_diam < prev_stage.maxd:
                stage_diam = prev_stage.maxd

            if drag_coff < prev_stage.cd:        # kjh added this too
                drag_coff = prev_stage.cd


    d = stage_diam * IN2M

    # c = r * M_PI * drag_coff * d * d * 0.125;

    drag_constant = 0.5 * drag_coff * ((M_PI * d * d * 0.25) + fins[this_stage].area)

    c = r * drag_constant

    # kjh wants to see thrust at t=0 if there is any ...

    if e_info[0].thrust[0] == 0.0:       # .thrust [ evens ] = Time
        thrust = e_info[0].thrust[1]     # .thrust [ odds ] = Thrust

        if thrust != 0.0:
            accel  = (( thrust - drag ) / mass) - G
        else:
            accel = 0.0

        print_alt = alt * M2FT
        print_vel = vel * M2FT
        print_accel = accel * M2FT
        print_mass = mass * 1000         # I want my Mass in Grams
"""
/*    if (verbose)
         fprintf(stream," %4.1lf %10.1lf %10.1lf %10.1lf %11.2lf %10.3lf %10.3lf %6.4f\n",
                t, print_alt, print_vel, print_accel, print_mass, thrust, drag, r );
 */
      if (verbose)
         fprintf(stream," %4.1lf %10.1lf %10.1lf %10.1lf %11.2lf %10.3lf %10.3lf\n",
                t, print_alt, print_vel, print_accel, print_mass, thrust, drag );

      print_index = 0;
      thrust = 0 ;
   }

   /* Launch Loop */

   for(;;)
   {
      /* Calculate decreasing air density */

/*    r = air_density (alt,site_alt,base_temp);  */

/*    y = alt+site_alt ;                         */
      y = alt ;

      if ( y > SPACEALT )
         r = 0 ;
      elif y > MAXALT )
      {
         /* r = 1.7187 * exp ( -1.5757e-4 * y ) ; */
         r = 1.9788 * exp ( -1.5757e-4 * y ) ;
      }
      else
      {
         r = Rho_0 * exp ( 4.255 * log ( 1 - ( y * 2.2566e-5 ))) ;
      }

#ifdef TEMP_CORRECTION

       dT = ISAtemp ( base_temp, y ) ;

      mach1_0 = sqrt ( MACH_CONST * dT );

#endif

      /* c = r * M_PI * drag_coff * d * d * 0.125;      /* kjh changed this */

      c = r * drag_constant ;

      t += delta_t;
      stage_time += delta_t;

      /* handle staging, if needed */

      if ((t > stages[this_stage].end_stage) && (this_stage < stagenum-1))
      {
          thrust_index = 0;
          old_thrust = 0.0;
          sum_o_thrust = 0.0 ;
          old_time = 0.0;

/*        mass = rocketwt - stage_wt;         */
          mass = ( rocketwt -= stage_wt );   /* kjh 95-10-29 */

          this_stage++;
          stage_wt = stages[this_stage].totalw;

          stage_engcnum = stages[this_stage].engcnum;
          stage_time = burn_time = 0;

          for (j = this_stage; j < stagenum; j++)
          {
              stage_diam = stages[j].maxd;
              drag_coff  = stages[j].cd ;                /* kjh Added This */

              if (j > this_stage)
              {
                  if (stage_diam < stages[j-1].maxd)
                      stage_diam = stages[j-1].maxd;

                  if ( drag_coff < stages[j-1].cd )      /* kjh added this too */
                     drag_coff = stages[j-1].cd ;
              }
          }
          /*       1                                              */
          /*  c = --- * M_PI * d ^ 2 * R * k                        */
          /*       8                                              */
          /*                                                      */
          /*        1                                             */
          /*     = --- * PI * r ^ 2 * R * k                       */
          /*        2                                             */
          /*                                                      */
          /*                     m^2 * kg                         */
          /*     =  A * R * k   ----------                        */
          /*                     m^3                              */
          /*                                                      */
          /*        kg                                            */
          /*     = ----                                           */
          /*         m                                            */
          /*                                                      */

           d = stage_diam * IN2M;

           /*          c = r * M_PI * drag_coff * d * d * 0.125; */

           drag_constant = 0.5 * drag_coff * (( M_PI * d * d * 0.25 ) + fins[this_stage].area ) ;

           c = r * drag_constant;

          fprintf(stream,"%cStage %d Ignition at %5.2f sec.\n", ch1, this_stage+1, t );
      }

      /* Handle the powered phase of the boost */

      if ((t >= stages[this_stage].start_burn) &&
          (t <= stages[this_stage].end_burn))
      {

        burn_time +=  delta_t;               /* add to burn time */

        /* see if we need to use the next thrust point */
        /* All times are relative to burn time for these calculations */

        if (burn_time > e_info[stage_engcnum].thrust[thrust_index])
        {
            old_time = e_info[stage_engcnum].thrust[thrust_index];

            thrust_index++;

            old_thrust = e_info[stage_engcnum].thrust[thrust_index];

            thrust_index++;
        }
        /*

           Logic to smooth transision between thrust points.
           Transisions are linear rather than discontinuous.
        */

        thrust = e_info[stage_engcnum].thrust[thrust_index + 1] - old_thrust;

        thrust *=               (burn_time - old_time) /
                    ( e_info[stage_engcnum].thrust[thrust_index] - old_time );

        thrust += old_thrust;

        thrust *= stages[this_stage].engnum;

        /* kjh changed this to comsume propellant at thrust rate */

        sum_o_thrust += ( thrust * delta_t );

        m1 =                       sum_o_thrust /
              ( e_info[stage_engcnum].ntot * stages[this_stage].engnum );

        m1 *= e_info[stage_engcnum].m2 * stages[this_stage].engnum ;

        /*       This is the Original Method       */
        /*                                         */
        /*       m1 = (e_info[stage_engcnum].m2 / e_info[stage_engcnum].t2) * delta_t; */
        /*       stage_wt -= m1;                   */
        /*       mass = rocketwt -= m1;            */
        /*                                         */
        /*       fprintf ( stderr, "Sum ( %f ) = %10.2f  ;  Mass = %10.6f\n", burn_time, sum_o_thrust, m1 ); */

        mass = rocketwt - m1 ;

      }
      else
      {
        thrust = 0.0;

         if (( tcoff == 0.0 ) && ( this_stage == ( stagenum - 1 )))
         {
            vcoff = vel ;
            acoff = alt ;
            tcoff = t ;
         }
      }

       /*
       Crude approximations for MACH 1 Transition.
       the drag bias will be applied to the subsonic value.
       It will be equal to 1.0 for velocities less than MACH 0.8.
       From MACH 0.8 to MACH 1.0 it will increase linearly to 2.0 times
       the subsonic value.  From MACH 1.0 to MACH 1.2 it will decrease to
       1.5 times the subsonic value.  Above MACH 1.2 it will remain at
       a value of 1.5
       */

      avg_vel = ( old_vel + vel ) / 2 ;        /* kjh added this */

      /*    kjh Added M,C&B Model for TransSonic Region */

      drag_bias = DragDiverge ( Nose, mach1_0, vel ) ;

      /*    kjh replaced this with DragDiverge */

/*    if (vel < mach0_8)
        drag_bias = 1;
      elif vel < mach1_0)
        drag_bias = (1.0 + ((vel - mach0_8) / (mach1_0 - mach0_8)));
      elif vel < mach1_2)
        drag_bias = (2.0 - 0.5*((vel - mach1_0) / (mach1_2 - mach1_0)));
      else
        drag_bias = 1.5;
 */

      cc = c * drag_bias;

      /* Simple Newton calculations                      */
      /* kjh changed for coasting after burnout          */
      /*                                                 */
      /* cc                         = kg / m             */
      /* accel                      = m / sec^2          */
      /*                                                 */
      /* kg  *    m *    m                m              */
      /* -------------------------  =  ------            */
      /*  m  *  sec *  sec *   kg       sec^2            */

      /* kjh added to compute drag and report it in N    */

/*    drag = - ( cc * vel * vel ) ;                                         */
      drag = - ( cc * avg_vel * avg_vel ) ;    /* kjh changed this 05-23-96 */

      if (( launched ) && ( vel <= 0 ))
      {
         drag = - drag ;
         accel = ( drag / mass ) - G;             /* kjh added this */
      }
      else
         accel = (( thrust + drag ) / mass) - G;

      old_vel = vel ;                             /* kjh added this */

      vel = vel + accel * delta_t;

      alt = alt + vel * delta_t;

      /* test for lift-off and apogee */

      if ( vel > 0 )
          launched = 1;                 /* LIFT-OFF */

      elif !launched && ( vel < 0 ))
          alt = vel = accel = 0;        /* can't fall off pad! */

      elif launched && ( vel < 0 ))
      {
        coast_time += delta_t;       /* time past burnout  */

        if (( alt <= 0.0 ) || ( coast_time > coast_base )) /* kjh to coast a while */
        {
          break;                        /* apogee, all done */
        }
      }

      if ((alt <= Rod) && ( vel > 0 ))
      {
        t_rod = t;
        v_rod = vel * M2FT;
      }

      /* do max evaluations */

      if (accel > max_accel)
      {
         max_accel = accel;
         t_max_accel = t ;
      }
      elif accel < min_accel )
      {
         min_accel = accel;
         t_min_accel = t ;
      }

      if (vel > max_vel)
      {
         max_vel = vel;
         t_max_vel = t ;
      }

      if (alt > max_alt)
      {
         max_alt = alt;
         max_t = t;
      }

      /* See if we need to print out the current values */

      if ((++ print_index ) == ten_over_delta_t )
      {
         print_index = 0;
         print_alt = alt * M2FT;
         print_vel = vel * M2FT;
         print_accel = accel * M2FT;
         print_mass = mass * 1000 ;             /* Gimme my Mass in Grams */
      /*
         if (verbose)
            fprintf(stream," %4.1lf %10.1lf %10.1lf %10.2lf %11.2lf %10.3lf %10.3lf %10g %7.4f\n",
                t, print_alt, print_vel, print_accel, print_mass, thrust, drag, r, mach1_0 );
      */
         if (verbose)
            fprintf(stream," %4.1lf %10.1lf %10.1lf %10.2lf %11.2lf %10.3lf %10.3lf\n",
                t, print_alt, print_vel, print_accel, print_mass, thrust, drag );

      }
   }
   if (print_index != 0)
   {
      print_index = 0;
      print_alt = alt * M2FT;
      print_vel = vel * M2FT;
      print_accel = accel * M2FT;
      print_mass = mass * 1000 ;
   /*
      fprintf(stream," %5.2lf %9.1lf %10.1lf %10.2lf %11.2lf %10.3lf %10.3lf %6.4f\n",
                        t-delta_t, print_alt, print_vel, print_accel, print_mass, thrust, drag, r );
    */
      if ( verbose )
         fprintf(stream," %5.2lf %9.1lf %10.1lf %10.2lf %11.2lf %10.3lf %10.3lf\n",
                           t-delta_t, print_alt, print_vel, print_accel, print_mass, thrust, drag );
   }
   print_alt = max_alt * M2FT;              /* kjh changed for coasting */
   print_vel = vel * M2FT;
   print_accel = accel * M2FT;
   print_mass = mass / OZ2KG;
   fprintf(stream, "%c\n%cMaximum altitude attained = %.1lf feet (%.1lf meters).\n",
      ch1,ch1, print_alt, max_alt);
   fprintf(stream, "%cTime to peak altitude =     %.2lf seconds.\n", ch1, max_t);
   fprintf(stream, "%cMaximum velocity =          %.1lf feet/sec at %.2lf sec.\n",
       ch1, max_vel * M2FT, t_max_vel );
   fprintf(stream, "%cCutoff velocity =           %.1lf feet/sec at %.1lf feet ( %.2lf sec ).\n",
      ch1, vcoff*M2FT, acoff*M2FT, tcoff ) ;
   fprintf(stream, "%cMaximum acceleration =      %.1lf feet/sec^2 at %.2lf sec.\n",
      ch1, max_accel * M2FT, t_max_accel );
   fprintf(stream, "%cMinimum acceleration =      %.1lf feet/sec^2 at %.2lf sec.\n",
      ch1, min_accel * M2FT, t_min_accel );
   fprintf(stream, "%cLaunch rod time =  %.2lf,  rod len   = %.1lf,       velocity  = %.1lf\n",
           ch1, t_rod, Rod*M2FT, v_rod);
   fprintf(stream, "%cSite Altitude =   %5.0lf,  site temp = %.1lf F\n",
           ch1, site_alt*M2FT, (( base_temp - 273.15 ) * 9 / 5 ) + 32 ) ;
   fprintf(stream, "%cBarometer     =   %.2f,  air density = %.4lf,  Mach vel  = %.1lf\n",
           ch1, baro_press, Rho_0, M2FT * sqrt ( MACH_CONST * base_temp )) ;
   fclose(stream);
}
"""


def parse_commandline():
    global args, parser

    parser = argparse.ArgumentParser(prog='raspinfo', description=f'Dump RASP engine info (v{VERSION})')
    parser.add_argument('-d', '--debug', action='store_true', help='debug output')
    parser.add_argument('-q', '--quiet', action='store_true', help="be quiet about it")
    parser.add_argument('--version', action='version', version=f'v{VERSION}')
    parser.add_argument('engfile', default=ENG_NAME, nargs='?', action='store', help='engine filename')

    args = parser.parse_args()


def main():
    debug = True
    argp = True

    print("\nRASP - Rocket Altitude Simulation Program V", VERSION)

    if argc > argp:
        if ( * argv [argp] == '-' )
         if (( * ++ argv [argp] == 'q' ) || ( * argv [argp] == 'Q' ) ||
             (    * argv [argp] == 's' ) || ( * argv [argp] == 'S' ))
         {
            verbose = FALSE;
         }
         elif( * argv [argp] == 'd' ) || ( * argv [argp] == 'D' ))
         {
            DeBug = TRUE;
         }
         argp ++

    # v4.1 do the Home bit
    if (( p = getenv ( "RASPHOME" )) != (char *) NULL )
        RaspHome = strdup ( p ) ;
    else
        RaspHome = (char *) NULL ;

   (void) BaseName ( RASP_FILE_LEN, PrgName, argv [0] ) ;

   if ( strcmp ( PrgName, argv [0] ) == 0 )
      WhereIs ( RASP_FILE_LEN, PrgName, argv [0], NULL, NULL ) ;
   else
      strncpy ( PrgName, argv [0], RASP_FILE_LEN );/* fqpn in argv [0]   */

   WhereIs ( RASP_FILE_LEN, ename, DFILE, RaspHome, PrgName ) ;

   (void) DirName ( EngHome, ename ) ;             /* set homedir        */

    if debug:
        printf ( "RASP Home = %s\n", (RaspHome == (char *) NULL ) ? "" : RaspHome)
        printf ( "Eng Home  = %s\n", EngHome )
        printf ( "Prog Name = %s\n", PrgName )
        printf ( "Eng File  = %s\n", ename )

    # kjh initialized the stage info

    rname = ""
    oname = ""

    destnum = 1
    bname = ""
    stagenum = 1
    faren_temp = 59
    site_alt = LAUNCHALT / M2FT
    baro_press = STD_ATM
    Rod = ROD
    Nose = 1

    for stage in flight.rocket.stages:
        stage.engnum = 1  # of engines in stage

    # this is the batch mode block ( see n.c )
    if ( argc > argp ):
        while ( argc > argp )
            BatchFlite ( argv [argp++] ) ;

        return
    else:
        while True:
            rocketwt = 0
            nexteng = 0
            choices()
            calc()

        # kjh changed this

        strcpy ( ans, "Y" )

         GetStr ( "\nDo Another One", ans, 2 ) ;

         if (( strncmp ( ans,"y",1 ) == 0 ) || ( strncmp ( ans,"Y", 1 ) == 0 ))
            print()
            continue
         else:
            exit( 0 )


def get_nose(prompt, default):
    got_one = False
    temp = None

    # todo: huh?
    Proper ( Temp, Noses [ Default ].name ) ;

    while not got_one:
        entry_str = imput(prompt)
        if not entry_str:
            return default
            
        got_one = find_nose(entry_str)

   return got_one:


def drag_diverge(nose_type, mach_1, velocity):

    mach_number = velocity / mach_1

    if mach_number <=  0.9 or mach_number <= 0.0:
        return 1.0

    if Noses[nose_type].form == 2:  # Rounded Noses
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
    dT = 0

    if alt <= 11000:
        dT = base_temp - alt * 0.0065
    elif alt <= 20000:
        dT = 216.65
    elif alt <= 32000:
        dT = 228.65 + (alt - 32000) * 0.0010
    elif alt <= 47000:
        dT = 228.65 + (alt - 47000) * 0.0028
    elif alt <= 51000:
        dT = 270.65
    elif alt <= 71000:
        dT = 214.65 - (alt - 71000) * 0.0028
    elif alt <= 84852:
        dT = 186.95 - (alt - 84852) * 0.0020
    else:
        dT = 186.95

    if dT < 0:
        dT = 0.0

    return dT

"""
   H [ 0] = 0         ;  T [ 0] = 288.15  ; L [ 0] = -6.5
   H [ 1] = 11000     ;  T [ 1] = 216.65  ; L [ 1] = -6.5
   H [ 2] = 11000.1   ;  T [ 2] = 216.65  ; L [ 2] = 0
   H [ 3] = 20000     ;  T [ 3] = 216.65  ; L [ 3] = 0
   H [ 4] = 20000.1   ;  T [ 4] = 216.65  ; L [ 4] = 1.0
   H [ 5] = 32000     ;  T [ 5] = 228.65  ; L [ 5] = 1.0
   H [ 6] = 32000.1   ;  T [ 6] = 228.65  ; L [ 6] = 2.8
   H [ 7] = 47000     ;  T [ 7] = 270.65  ; L [ 7] = 2.8
   H [ 8] = 47000.1   ;  T [ 8] = 270.75  ; L [ 8] = 0.0
   H [ 9] = 51000     ;  T [ 9] = 270.65  ; L [ 9] = 0.0
   H [10] = 51000.1   ;  T [10] = 270.65  ; L [10] = -2.8
   H [11] = 71000     ;  T [11] = 214.65  ; L [11] = -2.8
   H [12] = 71000.1   ;  T [12] = 214.65  ; L [12] = -2.0
   H [13] = 84852     ;  T [13] = 186.95  ; L [13] = -2.0
"""
