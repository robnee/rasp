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

#define RASP_C

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <math.h>

#ifdef UNIX
#include <unistd.h>
#endif

#ifdef MSDOS
#include <io.h>               /* DOS needs stack >= 4096 */
#define access _access
#define R_OK    4
#endif

#include "parse.h"
#include "pathproc.h"
#include "units.h"
#include "rasp.h"
#include "n.h"

double DragDiverge ( int Type, double Mach_1, double Velocity );
int GetNose ( char* Prompt, int Default);
int Proper ( char* OutStr, char* InStr );
double ISAtemp ( double BaseTemp, double Alt );


/* kjh moved this out of Choices () */
/*************************************************************************/
void dumpheader( double wt )
/*************************************************************************/
{
   int i;

   fprintf ( stream, "%c\n",ch1 );

   fprintf ( stream,"%cRocket Name:  %s\n", ch1, rname ) ;
   fprintf ( stream,"%cMotor File:   %s\n", ch1, ename ) ;

   for (i = 0; i < stagenum; i++)
   {
      fprintf ( stream, "%c\n",ch1 );

      fprintf ( stream,"%c%5s  %-16s  %8s  %8s  %8s  %9s\n",
         ch1,"Stage","Engine","Bare","Launch","AirFrame","Effective" );

      fprintf ( stream,"%c%5s  %-16s  %8s  %8s  %8s  %9s  %5s\n",
         ch1,"Num","(Qt) Type","Weight","Weight","Diameter","Diameter", "Cd" );

      fprintf ( stream,"%c%5s  %-16s  %8s  %8s  %8s  %9s  %5s\n",
         ch1,"=====","================","========","========","========","=========","=====" );

      fprintf(stream, "%c%5d  (%1d) %-12s  %8.2f  %8.2f  %8.3f  %9.3f  %5.3f\n",
         ch1, i + 1, stages[i].engnum, e_info[stages[i].engcnum].code,
         stages[i].weight / OZ2KG, wt / OZ2KG, stages[i].maxd,
            (stages[i].maxd + ( sqrt (    fins[i].area /
                                        ( IN2M*IN2M*M_PI )) / 2 )),
             stages[i].cd );

     wt -= stages[i].totalw;

     print_engine_info(stages[i].engcnum);

   }

   if (verbose)
   {
     fprintf(stream, "%c\n%c%4s %10s %10s %10s %11s %10s %10s\n", ch1, ch1,
             "Time", "Altitude", "Velocity","Accel", "Weight", "Thrust", "Drag");
     fprintf(stream, "%c%4s %10s %10s %10s %11s %10s %10s\n", ch1,
             "(Sec)", "(Feet)", "(Feet/Sec)", "(Ft/Sec^2)", "(Grams)", "(Newtons)" , "(Newtons)");
     fprintf(stream, "%c%4s %10s %10s %10s %11s %10s %10s\n", ch1,
             "-----", "---------", "---------", "---------", "-----------", "---------", "---------");
   }
/* else
      fprintf ( stream, "%c\n", ch1 );
 */
}

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
      else if ( destnum == 2 )
         strncpy ( fname, "PRN", RASP_FILE_LEN );

#endif

#ifdef UNIX

      if ( destnum == 1 )
         strncpy ( fname, "/dev/tty", RASP_FILE_LEN ) ;
      else if ( destnum == 2 )
         strncpy ( fname, "/dev/lp", RASP_FILE_LEN );

#endif

#ifdef VMS

      if ( destnum == 1 )
         strncpy ( fname, "TT:", RASP_FILE_LEN );
      else if ( destnum == 2 )
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

/*************************************************************************/
void calc()
/*************************************************************************/
{

   int j;                                   /* iteration variable */
   int thrust_index = 0;                    /* index into engine table */
   int stage_engcnum,                       /* engcnum for current stage */
       this_stage = 0;                      /* current stage */
   double stage_time = 0.0,                 /* elapsed time for current stage */
          burn_time = 0.0,                  /* Elapsed time for motor burn */
          stage_wt,                         /* current wt of this_stage */
          stage_diam;                       /* max diam at current time */
   double t_rod = 0.0, v_rod  ;             /* launch rod info */
   double c;
   double cc, drag_bias;
   double thrust = 0.0;                     /* Thrust */
   double vel = 0.0;                        /* Velocity */
   double accel = 0.0;                      /* Acceleration */
   double alt = LAUNCHALT ;                 /* Altitude */
   double print_vel, print_alt, print_accel, print_mass;  /* used for printing */

   double mass = 0.0;
   double t = 0.000000;
   double max_accel = 0.0;
   double t_max_accel = 0.0;
   double min_accel = 0.0;
   double t_min_accel = 0.0;
   double max_vel = 0.0;
   double t_max_vel = 0.0;
   double max_alt = 0.0;                 /* kjh added to save max alt */
   double max_t   = 0.0;                 /* kjh added to save time to max alt */
   double drag    = 0.0;                 /* kjh added to print Drag in Nt */

   double old_vel = 0.0;                 /* kjh added to avg vel in interval */
   double avg_vel = 0.0;                 /* kjh ditto                        */

   double sum_o_thrust = 0.0 ;           /* kjh added to reduce pro mass ~ thrust */

   double old_thrust = 0.0;              /* last engine thrust  from table */
   double old_time = 0.0;                /* last engine thrust time  from table */
   double d, m1;                         /* temp vars */

   int print_index = 0;                  /* used for print loop */
   int launched = 0;                     /* indicates rocket has lifted off */

   double delta_t = 0.001;               /* Time interval - 1us */
   int ten_over_delta_t = 100 ;
   double r ;                            /* rho == Air Density for drag calc */
   double y;

/* double air_density();                 /* kjh put this inline */

   double drag_constant = 0.0 ;          /* compute once-per-stage */
   double coast_time = 0.00;             /* kjh to coast after burnout */

   double vcoff = 0.00 ;
   double acoff = 0.00 ;
   double tcoff = 0.00 ;   /* kjh added for cutoff data */

/* double mach0_8 ;
   double mach1_2 ;
 */
   double dT      ;                      /* change in temp vs altitude */

/* mach0_8 = mach1_0 * 0.8;
   mach1_2 = mach1_0 * 1.2;
 */
   r = Rho_0 ;

   stage_wt = stages[this_stage].totalw;

   stage_engcnum = stages[this_stage].engcnum;
   mass = rocketwt;

   /*
   for ( j=0 ; j < stagenum ; j++ )
      fprintf ( stream, "%cStage Weight [%d]:  %9.4f\n", ch1, j, stages[j].totalw );
    */

   /* What is the effective Diameter */

   for (j = 0; j < stagenum; j++)
   {
      stage_diam = stages[j].maxd;
      drag_coff  = stages[j].cd ;                  /* kjh Added This */

      if (j > 0)
      {
         if ( stage_diam < stages[j-1].maxd)
            stage_diam = stages[j-1].maxd;

         if ( drag_coff < stages[j-1].cd )         /* kjh added this too */
            drag_coff = stages[j-1].cd ;
      }
   }

   d = stage_diam * IN2M ;

   /* c = r * M_PI * drag_coff * d * d * 0.125;   */

   drag_constant = 0.5 * drag_coff * (( M_PI * d * d * 0.25 ) + fins[this_stage].area ) ;

   c = r * drag_constant ;

   /* kjh wants to see thrust at t=0 if there is any ... */

   if ( e_info[0].thrust[0] == 0.0 )      /*    .thrust [ evens ] = Time */
   {
      thrust = e_info[0].thrust[1] ;      /*    .thrust [ odds ] = Thrust */

      if ( thrust != 0.0 )
         accel  = (( thrust - drag ) / mass) - G ;
      else
         accel = 0.0 ;

      print_alt = alt * M2FT;
      print_vel = vel * M2FT;
      print_accel = accel * M2FT;
      print_mass = mass * 1000;           /* I want my Mass in Grams */

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
      else if ( y > MAXALT )
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
      else if (vel < mach1_0)
        drag_bias = (1.0 + ((vel - mach0_8) / (mach1_0 - mach0_8)));
      else if (vel < mach1_2)
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

      else if ( !launched && ( vel < 0 ))
          alt = vel = accel = 0;        /* can't fall off pad! */

      else if ( launched && ( vel < 0 ))
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
      else if ( accel < min_accel )
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

/*************************************************************************/
int main ( int argc, char* argv[] )
/*************************************************************************/
{
   char ans[3];
   int i;
   int DeBug = 1 ;
   int argp = 1 ;

   char * p ;           /* v4.1 temp */

   printf("\nRASP - Rocket Altitude Simulation Program V%s\n\n", VERSION);

   if ( argc > argp )
   {
      if ( * argv [argp] == '-' )
      {
         if (( * ++ argv [argp] == 'q' ) || ( * argv [argp] == 'Q' ) ||
             (    * argv [argp] == 's' ) || ( * argv [argp] == 'S' ))
         {
            verbose = FALSE;
         }
         else if (( * argv [argp] == 'd' ) || ( * argv [argp] == 'D' ))
         {
            DeBug = TRUE;
         }
         argp ++ ;
      }
   }

   /* v4.1 do the Home bit */

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

   if ( DeBug )
   {
   printf ( "RASP Home = %s\n", (RaspHome == (char *) NULL ) ? "" : RaspHome) ;
   printf ( "Eng Home  = %s\n", EngHome ) ;
   printf ( "Prog Name = %s\n", PrgName ) ;
   printf ( "Eng File  = %s\n", ename ) ;
   }

   /*  kjh initialized the stage info */

   rname [ 0 ] = '\0' ;
   oname [ 0 ] = '\0' ;

   destnum = 1;
   bname [ 0 ] = '\0' ;
   stagenum = 1 ;
   faren_temp = 59;
   site_alt = LAUNCHALT / M2FT ;
   baro_press = STD_ATM ;
   Rod = ROD ;
   Nose = 1;

   for ( i = 0 ; i < MAXSTAGE ; i++ )
      stages[i].engnum = 1 ;       /* # of engines in stage */

   /* this is the batch mode block ( see n.c ) */

   if ( argc > argp )
   {
      while ( argc > argp )
         BatchFlite ( argv [argp++] ) ;

      exit ( 0 ) ;
   }
   else
   {
      for (;;)
      {
         rocketwt = 0;
         nexteng = 0;
         choices();
         calc();

         /* kjh changed this */

         strcpy ( ans, "Y" ) ;     /* v4.2 no need for strncpy here */

         GetStr ( "\nDo Another One", ans, 2 ) ;

         if (( strncmp ( ans,"y",1 ) == 0 ) || ( strncmp ( ans,"Y", 1 ) == 0 ))
         {
            printf ( "\n" );
            continue;
         }
         else
            exit( 0 );
      }
   }
}
/***********************************************************************/
int GetInt ( char * Prompt, int Default )
/***********************************************************************/
{

   int GotOne = 0 ,
      i, l ;
   char  EntryStr [MAXSTRLEN + 1];

   while ( ! GotOne )
   {
      fprintf ( stdout, "%s [%d]:  ", Prompt, Default )  ;
      fgets ( EntryStr, MAXINTLEN, stdin ) ;

      l = strlen ( EntryStr ) - 1 ;

      EntryStr [l] = '\0' ;

      GotOne = 1 ;

      if ( l > 0 )
      {
         for ( i = 0 ; i < l ; i++ )
         {
            if ( ! ( isdigit ( EntryStr [ i ] )))
            {
/*             fprintf ( stderr, "\a\a\a" ) ;         */
               GotOne = 0 ;
            }
         }
      }
   }

   return (( l == 0 ) ? Default : atoi ( EntryStr ));

}

/***********************************************************************/
int isfloat ( char* InStr )
/***********************************************************************/
{

   char * p ;

   for ( p = InStr ; p < ( InStr + strlen ( InStr )) ; p ++ )
      if ( strchr ( FloatChars, * p ) == NULL )
         return 0 ;

   return -1 ;
}
/***********************************************************************/
double GetDbl ( char* Prompt, double Default)
/***********************************************************************/
{

   int GotOne = 0;
   int l ;
   char  EntryStr [MAXSTRLEN + 1];

   while ( ! GotOne )
   {
      fprintf ( stdout, "%s [%.2f]:  ", Prompt, Default ) ;
      fgets ( EntryStr, MAXDBLLEN, stdin ) ;

      l = strlen ( EntryStr ) - 1 ;          /* fgets returns the \n */

      EntryStr [l] = '\0' ;

      GotOne = 1 ;

      if ( l > 0 )
      {
         if ( ! ( isfloat ( EntryStr )))
         {
/*          fprintf ( stderr, "\a\a\a" ) ;      */
            GotOne = 0 ;
         }
      }
   }
   return (( strlen ( EntryStr ) == 0 ) ? Default : atof ( EntryStr )) ;

}
/***********************************************************************/
int GetStr ( char* Prompt, char* Default, int NumChr )
/***********************************************************************/
{
   char  EntryStr [MAXSTRLEN + 1];

   fprintf ( stdout, "%s [%s]:  ", Prompt, Default ) ;
   fgets ( EntryStr, NumChr, stdin ) ;

   EntryStr [ strlen ( EntryStr ) -1 ] = '\0' ;

   if ( strlen ( EntryStr ) > 0 )
      strncpy ( Default, EntryStr, NumChr ) ;

   return ( strlen ( Default )) ;

}
/***********************************************************************/
int FindNose ( char* nose )
/***********************************************************************/
{
   int i, j, k, l ;

   int GotOne = 0 ;

   for ( i = 0 ; i < ( l = strlen ( nose )) ; i++ )
      if ( isupper ( nose [i] ))
         nose [i] = tolower ( nose [i] );

   for ( i = 0 ; i < NUMNOSES ; i++ )
   {
      k = strlen ( Noses [ i ].name ) ;

      for ( j = 0 ; ( j < l && j < k ) ; j++ )
         if ( nose [ j ] != Noses [ i ].name [ j ] )
            break ;

      if ( j == l )
      {
         GotOne = i ;
         break ;
      }
   }

   return ( GotOne ) ;
}
/***********************************************************************/
int GetNose ( char* Prompt, int Default)
/***********************************************************************/
{
   int GotOne = 0;
   int l ;
   char  EntryStr [MAXSTRLEN + 1];

   char Temp [ MAXSTRLEN ] ;

   Proper ( Temp, Noses [ Default ].name ) ;

   while ( ! GotOne )
   {
      fprintf ( stdout, "%s [%s]:  ", Prompt, Temp ) ;
      fgets ( EntryStr, MAXSTRLEN, stdin ) ;

      l = strlen ( EntryStr ) - 1 ;          /* fgets returns the \n */

      if ( l <= 0 )
         return ( Default ) ;

      EntryStr [l] = '\0' ;

      GotOne = FindNose ( EntryStr ) ;

   }
   return ( GotOne ) ;

}
/***********************************************************************/
int Proper ( char* OutStr, char* InStr )
/***********************************************************************/
{
   int   i = 0,
         l;

   if (( l = strlen ( InStr )) > 0 )
   {

      if ( islower ( InStr [ i ] ))
         OutStr [ i ] = toupper ( InStr [ i ] ) ;
      else
         OutStr [ i ] = InStr [ i ] ;

      i ++ ;

      while ( i < l )
      {
         if ( isupper ( InStr [ i ] ))
            OutStr [ i ] = tolower ( InStr [ i ] ) ;
         else
            OutStr [ i ] = InStr [ i ] ;

         i ++ ;
      }
   }

   OutStr [ l ] = '\0' ;

   return ( l ) ;
}
/***********************************************************************/
double DragDiverge ( int Type, double Mach_1, double Velocity )
/***********************************************************************/
{

   double MachNumber ;
   double Diverge ;

   MachNumber = Velocity / Mach_1 ;

   if (( MachNumber <=  0.9 ) || ( MachNumber <= 0.0 ))
      return ( 1.0 ) ;

   if ( Noses [ Type ].form == 2 )           /* Rounded Noses */
   {
      if ( MachNumber <= 1.2 )
      {
         Diverge = 1.0 + 4.88 * pow ((( double ) ( MachNumber - 0.9 )), ( double ) ( 1.1 )) ;
      }
      else if ( MachNumber < 2.0 )
      {
         Diverge = 2.0 + 0.30 * exp (( double ) ( -5.75 * ( MachNumber - 1.2 ))) ;
      }
      else
      {
         Diverge = 2.0 ;
      }
   }
   else                                      /* Sharp Noses */
   {
      if ( MachNumber <= 1.05 )
      {
         Diverge = MachNumber - 0.9 ;
         Diverge *= Diverge ;
         Diverge = 1.0 + 35.5 * Diverge ;
      }
      else if ( MachNumber < 2.0 )
      {
         Diverge = 1.27 + 0.53 * exp (( double ) ( -5.2 * ( MachNumber - 1.05 ))) ;
      }
      else
      {
         Diverge = 1.27 ;
      }
   }
   return ( Diverge );
}
/***********************************************************************/
double ISAtemp ( double BaseTemp, double Alt )
/***********************************************************************/
{

   double dT = 0 ;

   if ( Alt <= 11000 )
      dT = BaseTemp - ( Alt * 0.0065 ) ;
   else if ( Alt <= 20000 )
      dT = 216.65 ;
   else if ( Alt <= 32000 )
      dT = 228.65 + (( Alt - 32000 ) * 0.0010 ) ;
   else if ( Alt <= 47000 )
      dT = 228.65 + (( Alt - 47000 ) * 0.0028 ) ;
   else if ( Alt <= 51000 )
      dT = 270.65 ;
   else if ( Alt <= 71000 )
      dT = 214.65 - (( Alt - 71000 ) * 0.0028 ) ;
   else if ( Alt <= 84852 )
      dT = 186.95 - (( Alt - 84852 ) * 0.0020 ) ;
   else
      dT = 186.95 ;

   if ( dT < 0 ) dT = 0.0 ;

   return ( dT ) ;

   /*
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
   */
}


#ifndef RASP_H

#define RASP_H

#define VERSION   "4.1b"
#define TRUE      1
#define FALSE     0
#define MAXENG    5
#define MAXT      256
#define MAXSTAGE  5

# if ! defined (M_PI)
#  define M_PI       3.14159265358979323846
# endif

# if ! defined ( M_E)
#  define M_E        2.7182818284590452354
# endif

#define G         9.806650
#define IN2M      0.0254
#define GM2LB     0.00220462
#define OZ2KG     0.028349523
#define M2FT      3.280840
#define IN2PASCAL 3386.39
#define ROD       60 * IN2M   /* Length of launch rod in meters (60") */
#define MACH0_8   265.168     /* Mach 0.8 in Meters/sec  870 ft/sec */
#define MACH1     331.460     /* Mach 1.0 in Meters/sec  1086 ft/sec*/
#define MACH1_2   397.752     /* Mach 1.2 in Meters/sec  1305 ft/sec */

#define LAUNCHALT 0.00

/* kjh moved this from air.c to rasp.c */

#define TEMP_CORRECTION 1

#define DT_DH            0.006499         /* degK per meter */
#define DT_DF            0.001981         /* degK per foot */
#define TEMP0            273.15   /* Temp of air at Std Density at Sea Level */
#define S_L_RHO          1.29290          /* Density of Air at STP ( 0C ) */
#define MAXALT           36093 * M2FT     /* Where the Stratosphere begins */
#define STD_ATM          29.92            /* Standard Pressure */

#define SPACEALT         43610            /* q&d fix */

/*
 * Define the 1st character on non-data output lines. This forces
 * output to be gnuplot compatible.
 */

/*
 *  kjh added Mach Correction for Temp
 */
#define GAMMA           1.40109        /*  specific heat ratio of air */
#define GAS_CONST_AIR   286.90124      /*   ( J / Kg*K )              */
#define MACH_CONST      GAMMA * GAS_CONST_AIR     /* speed it up, bub */

#define MAXINTLEN    6
#define MAXLONGLEN   11
#define MAXDBLLEN    17
#define MAXSTRLEN    256

#define DFILE "rasp.eng"

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

struct stage_info {
    int engcnum;        /* index into e_info */
    int engnum;         /* # of engines in stage */
    double start_burn;  /* Start of engine (includes previous stage) */
    double end_burn;    /* End of engine burn  (includes previous stage) */
    double end_stage;   /* End of stage (includes previous stage) */
    double drop_stage;  /* When stage is dropped (includes previous stage) */
    double weight;      /* stage wt w/o engine */
    double totalw;      /* wt of stage w/ engine(s) */
    double maxd;        /* max diameter of stage  */
    double cd;          /* kjh added cd per stage */
};

struct fin_info {
    int    num;         /* Number of Fins / Stage  */
    double thickness;   /* Max Thickness of Fin Stock */
    double span;        /* Max Span of Fins from BT */
    double area;        /* Computed Once to run faster */
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

   int FindNose ( char* nose );
   int findmotor ( char* Name, int e );
   void dumpheader( double wt );
   void calc ();

#ifdef RASP_C

   double   GetDbl ( char* Prompt, double Default );
   int      GetStr ( char* Prompt, char* Default, int NumChr );
   int      GetInt ( char * Prompt, int Default );

   /*
    * Define the 1st character on non-data output lines. This forces
    * output to be gnuplot compatible.
    */

#ifdef VMS
   char ch1 = '!';
#else
   char ch1 = '#';
#endif

   /*
    * Global Variables
    */

   int verbose = TRUE;
   double rocketwt;
   double drag_coff;
   double base_temp;
   double faren_temp ;
   double mach1_0;
   double site_alt ;
   double baro_press ;
   double Rho_0 ;
   double Rod ;
   double coast_base;

   char  PROMPT [ 81 ] ;
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

   struct nose_cone Noses [ ] =
   {
      { "undefined",      1 } ,
      { "ogive",          1 } ,
      { "conic",          1 } ,
      { "elliptic",       2 } ,
      { "parabolic",      2 } ,
      { "blunt",          2 }
   } ;

#define NUMNOSES ( sizeof Noses / sizeof ( struct nose_cone ))

   int Nose ;
   struct stage_info stages [ MAXSTAGE+1 ];
   struct engine     e_info [ MAXENG+1 ];
   struct fin_info   fins [ MAXSTAGE+1 ];
   double o_wt [ MAXSTAGE+1 ] ;  /* kjh added to remember weight run-to-run */
   struct motor_entry MLines [ MAXSTAGE+1 ] ;

   char DELIM [] = {" ,()" };

#else /* n.c decls */

   extern int verbose ;
   extern double rocketwt;
   extern double drag_coff;
   extern double base_temp;
   extern double faren_temp ;
   extern double mach1_0;
   extern double site_alt ;
   extern double baro_press ;
   extern double Rho_0 ;
   extern double Rod ;
   extern double coast_base;

   extern int nexteng,     /* next free engine index */
              destnum,     /* index into array of devices for output - dest */
              stagenum;    /* number of stages */

   extern char Mcode [];      /* array to hold engine code */

   extern char rname [];      /* rocket name */
   extern char oname [];      /* old rocket name */
   extern char bname [];      /* output file base name for simulation */
   extern char fname [];      /* output file name for simulation */
   extern char ename [];      /* Holds Motor File Name */

   extern char PrgName [];    /* v4.1 -- program Name ( fqpn ) */
   extern char EngHome [];    /* v4.1 -- engine file Home Dir ( rasp.eng ) */
   extern char * RaspHome ;   /* v4.1 -- getenv ( "RASPHOME" ) */

   extern FILE *stream,  *efile;

   extern struct nose_cone Noses [] ;

   extern int Nose ;
   extern struct stage_info stages [] ;
   extern struct engine     e_info [] ;
   extern struct fin_info   fins [] ;
   extern double o_wt [] ;            /* added to remember weight run-to-run */
   extern struct motor_entry MLines [] ;

#endif
#endif
