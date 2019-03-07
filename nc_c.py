#define  N_C

/* #define  N_C_MAIN /* uncomment to make ntst */

/* Added rfn */
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <sys/types.h>
#include <math.h>
#include <malloc.h>

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

#define INP_SIZE  2048
#define MAXARG       8

   static Rocket RaspBat ;

   char NoBatStr [1] = { '\0' } ;

   int PressOride = 0 ;

#ifdef MSDOS
#define DIR_SEP '\\'
#endif

#ifdef UNIX
#define DIR_SEP '/'
#endif

#ifdef VMS                       /* What is the DIR_SEP for VMS */
#define DIR_SEP ':'
#endif

/* ------------------------------------------------------------------------ */
void  ToDaMoonAlice ()
/* ------------------------------------------------------------------------ */
{
   int i ;
   int e ;

   double wt ;

   nexteng  = 0 ;
   rocketwt = 0.0 ;

   strncpy ( rname, RaspBat.title.dat, RASP_BUF_LEN ) ;

   /* strncpy ( ename, RaspBat.enginefile.dat, RASP_BUF_LEN ) ; /* v4.0a */

   /* sprintf ( ename, "%s%s", RaspBat.home.dat, RaspBat.enginefile.dat ); */

   /* v4.1 */

   (void) FixPath ( RASP_FILE_LEN, ename, 
                    RaspBat.home.dat, RaspBat.enginefile.dat );

   if ( access ( ename, R_OK ) != 0 )
   {
      i = strlen ( RaspBat.enginefile.dat ) + 1 ;

      (void) BaseName ( i, RaspBat.enginefile.dat, RaspBat.enginefile.dat ) ;

      if ( WhereIs ( RASP_FILE_LEN, ename, 
                     RaspBat.enginefile.dat, RaspHome, PrgName ) == 0 )
      {
         fprintf ( stderr, "Cannot find %s anyplace!\n",
                     RaspBat.enginefile.dat ) ;
         return ;
      }
   }

   if ( RaspBat.mode.dat > 0 )
   {
      verbose = TRUE ;
   }
   else
      verbose = FALSE ;

   Nose = FindNose ( RaspBat.nosetype.dat ) ;

   stagenum = RaspBat.numstages.dat ;

   site_alt = RaspBat.sitealt.dat ;

   coast_base = RaspBat.coasttime.dat ;

   base_temp = RaspBat.sitetemp.dat ;

   /* if ( RaspBat.sitepress.dat == 0.00 ) */

   if ( PressOride == 0 )
   {
      baro_press = 1 - ( 0.00000688 * site_alt * M2FT ) ;
      baro_press =  STD_ATM * exp ( 5.256 * log ( baro_press )) ;
   }
   else
   {
      baro_press = RaspBat.sitepress.dat / IN2PASCAL ;
   }

   mach1_0 = sqrt ( MACH_CONST * base_temp ) ;

   Rho_0 = ( baro_press * IN2PASCAL ) / ( GAS_CONST_AIR * base_temp ) ;

   Rod = RaspBat.raillength.dat ;

   if ( strcmp ( RaspBat.destination.dat, "file" ) == 0 )
      destnum = 3;
   else if ( strcmp ( RaspBat.destination.dat, "printer" ) == 0 )
      destnum = 2 ;
   else
      destnum = 1 ;

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

   if ( strlen ( RaspBat.outfile.dat ) > 0 )
      strncpy ( fname, RaspBat.outfile.dat, RASP_FILE_LEN ) ;

   for ( i = 0 ; ( i < stagenum && i < MAXSTAGE ) ; i ++ )
   {
      strncpy ( Mcode, RaspBat.stages [i].motorname.dat, RASP_BUF_LEN ) ;
      strncpy ( MLines [i].MEnt, Mcode, RASP_BUF_LEN ) ;

      e = nexteng ++ ;

      if ( findmotor ( Mcode, e ) <= 0 )
      {
         fprintf ( stderr, "Cannot find Motor:  %s\n", Mcode ) ;
         return ;
      }

      stages [i].engcnum = e ;

      stages [i].engnum  = RaspBat.stages [i].nummotor.dat ;

      stages [i].weight  = RaspBat.stages [i].drymass.dat ;

      stages [i].maxd    = RaspBat.stages [i].diameter.dat / IN2M ;

      fins [i].num       = RaspBat.stages [i].numfins.dat ;

      fins [i].thickness = RaspBat.stages [i].finthickness.dat / IN2M ;
      fins [i].span      = RaspBat.stages [i].finspan.dat / IN2M ;

      fins [i].area      = fins [i].num * fins [i].thickness * fins [i].span
                                        * IN2M               * IN2M ;

      stages [i].cd      = RaspBat.stages [i].cd.dat ;

      if ( i == 0 )
         stages[i].start_burn = 0.0 ;
      else
         stages[i].start_burn = stages [i-1].end_stage ;

      stages[i].end_burn = stages[i].start_burn +
                           e_info[stages[i].engcnum].t2 ;

      stages[i].end_stage = stages[i].end_burn +
                            RaspBat.stages [i].stagedelay.dat ;

      stages[i].totalw = stages[i].weight +
                         (e_info[stages[i].engcnum].wt * stages[i].engnum);

      rocketwt += stages[i].totalw;

   }

   if (( stream = fopen ( fname, "w" )) == NULL )
   {
      fprintf ( stderr, "cannot open %s\n", fname ) ;
      return ;
   }

   wt = rocketwt ;

   fprintf ( stderr, "Launching ( %s ) ...\n", Mcode ) ;

   dumpheader ( wt ) ;

   calc () ;

   /* V4.1b 981021 -- Thanks to Jeff Taylor -- closed by calc () */
   /* fclose ( stream ) ; */

   return ;

}
/* ------------------------------------------------------------------------ */
void  AddBatStr ( str_info* StrStru, char* InStr )
/* ------------------------------------------------------------------------ */
{
   int   len ;

   if (( StrStru->dat != 0 ) && ( StrStru->dat != NoBatStr ))
   {
      free ( StrStru->dat ) ;
   }

   /* v4.2 no need for strncpy here ... StrStru->dat is dynamically alloc'd */

   len = strlen ( InStr ) ;

   if (( len > 0 ) && (( StrStru->dat = (char *) malloc ( len + 1 )) != NULL ))
      strcpy ( StrStru->dat, InStr ) ;
   else
      StrStru->dat = NoBatStr ;
}
/* ------------------------------------------------------------------------ */
void  AddBatInt ( int_info* IntStru, int InInt )
/* ------------------------------------------------------------------------ */
{
   IntStru->dat = InInt ;
}
/* ------------------------------------------------------------------------ */
void  AddBatDbl ( dbl_info* DblStru, char* OValue, char* OUnit, double CValue )
/* ------------------------------------------------------------------------ */
{
   int   len ;

   if (( DblStru->inp != 0 ) && ( DblStru->inp != NoBatStr ))
      free ( DblStru->inp ) ;

   /* v4.2 no need for strncpy here ... DblStru->inp is dynamically alloc'd */

   len = strlen ( OValue ) ;

   if (( len > 0 ) && (( DblStru->inp = (char *) malloc ( len + 1 )) != NULL ))
      strcpy ( DblStru->inp, OValue ) ;
   else
      DblStru->inp = NoBatStr ;

   if (( DblStru->unt != 0 ) && ( DblStru->unt != NoBatStr ))
      free ((void *) DblStru->unt ) ;

   /* v4.2 no need for strncpy here ... DblStru->unt is dynamically alloc'd */

   len = strlen ( OUnit ) ;

   if (( len > 0 ) && (( DblStru->unt = (char *) malloc ( len + 1 )) != NULL ))
      strcpy ( DblStru->unt, OUnit ) ;
   else
      DblStru->unt = NoBatStr ;

   DblStru->dat = CValue ;

}
/* ------------------------------------------------------------------------ */
void  InitBat ( Rocket* BatStru )
/* ------------------------------------------------------------------------ */
{

   int Stage ;

   memset ( (void *) BatStru, '\0', sizeof ( Rocket )) ;

   AddBatStr ( & BatStru->title, "None" ) ;

   AddBatStr ( & BatStru->units, "FPS" ) ;

   AddBatInt ( & BatStru->mode, 1 ) ;

   AddBatStr ( & BatStru->home, EngHome ) ;     /* v4.1 */

/*
#ifdef UNIX
   AddBatStr ( & BatStru->home, "./" ) ;
#endif
#ifdef MSDOS
   AddBatStr ( & BatStru->home, ".\\" ) ;
#endif
#ifdef VMS
   AddBatStr ( & BatStru->home, "" ) ;
#endif
*/

   AddBatDbl ( & BatStru->dtime, "0.01", "sec", 0.01 ) ;

   AddBatDbl ( & BatStru->printtime, "0.1", "sec", 0.1 ) ;

   AddBatStr ( & BatStru->printcmd, "lp -dL1" ) ;

   AddBatDbl ( & BatStru->sitealt, "0.00", "ft", 0.00 ) ;

   /* AddBatDbl ( & BatStru->sitetemp, "59.0", "F", 288.15 ) ; */

   AddBatDbl ( & BatStru->sitetemp, "59.0", "F",
             ConvDUnit ( UNITS_TEMP, 59.0,  "F" )) ;

   AddBatDbl ( & BatStru->sitepress, "1013.25", "mb",
             ConvDUnit ( UNITS_PRESS, 1013.25,  "mb" )) ;

   AddBatDbl ( & BatStru->finalalt, "0.00", "ft", 0.00 ) ;

   AddBatDbl ( & BatStru->coasttime, "0.00", "sec", 0.00 ) ;

   /* AddBatDbl ( & BatStru->raillength, "5.00", "ft", 1.523999995 ) ; */

   AddBatDbl ( & BatStru->raillength, "5.00", "ft",
             ConvDUnit ( UNITS_LENGTH, 5.00,  "ft" )) ;

   AddBatStr ( & BatStru->enginefile, "rasp.eng" ) ;

   AddBatStr ( & BatStru->destination, "screen" ) ;

   AddBatStr ( & BatStru->outfile, "" ) ;

   AddBatDbl ( & BatStru->theta, "0.00", "deg", 0.00 ) ;

   AddBatInt ( & BatStru->numstages, 1 ) ;

   AddBatStr ( & BatStru->nosetype, "ogive" ) ;

   for ( Stage = 0 ; Stage < MAXSTAGE ; Stage ++ )
   {
      AddBatDbl ( & BatStru->stages [Stage].stagedelay, "0.00", "sec", 0.00 ) ;

      AddBatDbl ( & BatStru->stages [Stage].diameter, "0.00", "in", 0.00 ) ;

      AddBatInt ( & BatStru->stages [Stage].numfins, 0 ) ;

      AddBatDbl ( & BatStru->stages [Stage].finthickness, "0.00", "in", 0.00 ) ;

      AddBatDbl ( & BatStru->stages [Stage].finspan, "0.00", "in", 0.00 ) ;

      AddBatDbl ( & BatStru->stages [Stage].drymass, "0.00", "oz", 0.00 ) ;

      AddBatDbl ( & BatStru->stages [Stage].launchmass, "0.00", "oz", 0.00 ) ;

      AddBatDbl ( & BatStru->stages [Stage].cd, "0.75", "", 0.75 ) ;

      AddBatStr ( & BatStru->stages [Stage].motorname, "" ) ;

      AddBatInt ( & BatStru->stages [Stage].nummotor, 1 ) ;
   }
}
/* ------------------------------------------------------------------------ */
void  DumpBat ( Rocket* BatStru )
/* ------------------------------------------------------------------------ */
{

   int i, j ;

   fprintf ( stderr, "\nRASP Batch Dump\n\n" ) ;

   fprintf ( stderr, "BatStru->title       = %s\n", BatStru->title.dat ) ;

   fprintf ( stderr, "BatStru->units       = %s\n", BatStru->units.dat ) ;

   fprintf ( stderr, "BatStru->mode        = %d\n", BatStru->mode.dat  ) ;

   fprintf ( stderr, "BatStru->home        = %s\n", BatStru->home.dat  ) ;

   fprintf ( stderr, "BatStru->dtime,      = %s  %s  %.6f\n",
                                           BatStru->dtime.inp,
                                           BatStru->dtime.unt,
                                           BatStru->dtime.dat ) ;

   fprintf ( stderr, "BatStru->printtime   = %s  %s  %.6f\n",
                                           BatStru->printtime.inp,
                                           BatStru->printtime.unt,
                                           BatStru->printtime.dat ) ;

   fprintf ( stderr, "BatStru->printcmd    = %s\n", BatStru->printcmd.dat ) ;

   fprintf ( stderr, "\n" ) ;

   fprintf ( stderr, "BatStru->sitealt     = %s  %s  %.6f\n",
                                           BatStru->sitealt.inp,
                                           BatStru->sitealt.unt,
                                           BatStru->sitealt.dat ) ;

   fprintf ( stderr, "BatStru->sitetemp    = %s  %s  %.6f\n",
                                           BatStru->sitetemp.inp,
                                           BatStru->sitetemp.unt,
                                           BatStru->sitetemp.dat ) ;

   fprintf ( stderr, "BatStru->sitepress   = %s  %s  %.6f\n",
                                           BatStru->sitepress.inp,
                                           BatStru->sitepress.unt,
                                           BatStru->sitepress.dat ) ;

   fprintf ( stderr, "BatStru->raillength  = %s  %s  %.6f\n",
                                           BatStru->raillength.inp,
                                           BatStru->raillength.unt,
                                           BatStru->raillength.dat ) ;

   fprintf ( stderr, "BatStru->theta       = %s  %s  %.6f\n",
                                           BatStru->theta.inp,
                                           BatStru->theta.unt,
                                           BatStru->theta.dat ) ;

   fprintf ( stderr, "BatStru->finalalt    = %s  %s  %.6f\n",
                                           BatStru->finalalt.inp,
                                           BatStru->finalalt.unt,
                                           BatStru->finalalt.dat ) ;

   fprintf ( stderr, "BatStru->coasttime   = %s  %s  %.6f\n",
                                           BatStru->coasttime.inp,
                                           BatStru->coasttime.unt,
                                           BatStru->coasttime.dat ) ;

   fprintf ( stderr, "BatStru->enginefile  = %s\n",
                                           BatStru->enginefile.dat ) ;

   fprintf ( stderr, "BatStru->destination = %s\n",
                                           BatStru->destination.dat ) ;

   fprintf ( stderr, "BatStru->outfile     = %s\n",
                                           BatStru->outfile.dat ) ;

   fprintf ( stderr, "BatStru->nosetype    = %s\n",
                                           BatStru->nosetype.dat ) ;

   fprintf ( stderr, "BatStru->numstages   = %d\n",
                                           BatStru->numstages.dat ) ;

   for ( i = 0 ; i < ( BatStru->numstages.dat ) ; i ++ )
   {

   j = i + 1 ;

   fprintf ( stderr, "\n" ) ;

   fprintf ( stderr, "   *** stage [%d] data ***\n\n", j ) ;

   fprintf ( stderr, "   diameter [%d]     = %s  %s  %.6f\n", j,
                                    BatStru->stages [i].diameter.inp,
                                    BatStru->stages [i].diameter.unt,
                                    BatStru->stages [i].diameter.dat ) ;

   fprintf ( stderr, "   numfins [%d]      = %d\n", j,
                                    BatStru->stages [i].numfins.dat ) ;

   fprintf ( stderr, "   finthickness [%d] = %s  %s  %.6f\n", j,
                                 BatStru->stages [i].finthickness.inp,
                                 BatStru->stages [i].finthickness.unt,
                                 BatStru->stages [i].finthickness.dat ) ;

   fprintf ( stderr, "   finspan [%d]      = %s  %s  %.6f\n", j,
                                 BatStru->stages [i].finspan.inp,
                                 BatStru->stages [i].finspan.unt,
                                 BatStru->stages [i].finspan.dat ) ;

   fprintf ( stderr, "   cd [%d]           = %s  %s  %.6f\n", j,
                                 BatStru->stages [i].cd.inp,
                                 BatStru->stages [i].cd.unt,
                                 BatStru->stages [i].cd.dat ) ;

   fprintf ( stderr, "   drymass [%d]      = %s  %s  %.6f\n", j,
                                 BatStru->stages [i].drymass.inp,
                                 BatStru->stages [i].drymass.unt,
                                 BatStru->stages [i].drymass.dat ) ;

   fprintf ( stderr, "   nummotor [%d]     = %d\n", j,
                                 BatStru->stages [i].nummotor.dat ) ;

   fprintf ( stderr, "   motorname [%d]    = %s\n", j,
                                 BatStru->stages [i].motorname.dat ) ;

   fprintf ( stderr, "   stagedelay [%d]   = %s  %s  %.6f\n", j,
                                    BatStru->stages [i].stagedelay.inp,
                                    BatStru->stages [i].stagedelay.unt,
                                    BatStru->stages [i].stagedelay.dat ) ;

   fprintf ( stderr, "   launchmass [%d]   = %s  %s  %.6f\n", j,
                                 BatStru->stages [i].launchmass.inp,
                                 BatStru->stages [i].launchmass.unt,
                                 BatStru->stages [i].launchmass.dat ) ;

   }
}
/* ------------------------------------------------------------------------ */
void  BatchFlite ( char * BatFile )
/* ------------------------------------------------------------------------ */
{
   int   i = 0 ;
   int   j = 0 ;

   char     InpBuf [ INP_SIZE+1 ] ;
   char  *  ArgBuf [ MAXARG ] ;

   int      lth ;
   char   * pptr ;

   unsigned int NumArg = 0;
   FILE *       BatAddr ;

   double      dtmp ;
   int         itmp ;
   char      * stmp ;

   char      * p ;

   int         Stage = 1 ;

   /* v4.2 subtle bug processing home directory ... I was writing a / at *
    * the tail of * ArgBuf [2] -- Possibly on top of sombody else's data *
    * space !  Adding a work buffer for doing the deed.                  */

   char WorkBuf [ RASP_FILE_LEN+1] ;

   NoBatStr [0] = '\0' ;

   if ( BatFile [0] == '\0' )
   {
      fprintf ( stderr, "\nno batch file !\n" );
      return ;
   }

   if (( BatAddr = fopen ( BatFile, "rb" )) == NULL )
   {
      fprintf ( stderr, "\ncannot open batch file %s for input\n", BatFile ) ;
   }
   else
   {
      InitBat ( & RaspBat ) ;

      while ( ! feof ( BatAddr ))
      {
         if ( fgets ( InpBuf, INP_SIZE, BatAddr ) != NULL )
         {
            /* wac trailing <cr>, <lf>, etc ... */

            lth  = strlen ( InpBuf )  - 1 ;

            while ( lth >= 0 )
            {
               if ( iscntrl ( InpBuf [ lth ] ))
                  InpBuf [ lth -- ] = '\0' ;
               else
                  break ;
            }

            pptr = InpBuf + lth ;

            if (( NumArg = Parse ( InpBuf, " \t\r\n=", MAXARG, ArgBuf )) > 0 )
            {
               ToLower ( ArgBuf [0] ) ;

               lth = strlen ( ArgBuf [0] ) ;

               for ( i = 0 ; i < NUM_MNEMONS ; i ++ )
               {
                  if ( strncmp ( Mnemons [i].Tag, ArgBuf [0], lth ) == 0 )
                  {
                     if ( Mnemons [i].Ndx == TITLE )
                     {
                        if ( NumArg > 1 )
                        {
                           /* this stipid thingie undoes what Parse() did */

                           p = ArgBuf [0] + lth ;

                           while ( p < pptr )
                              if ( * p == '\0' )
                                 * p ++ = ' ' ;
                              else
                                 p ++ ;

                           AddBatStr ( & RaspBat.title, ArgBuf [1] ) ;
                        }
                        break ;
                     }
                     else if ( Mnemons [i].Ndx == LAUNCH )
                     {
                        ToDaMoonAlice () ;
                        break ;
                     }
                     else if ( Mnemons [i].Ndx == N_H_QUIT )
                     {
                        fclose ( BatAddr ) ;
                        return ;
                     }
                     else if ( Mnemons [i].Ndx == N_H_DUMP )
                     {
                        DumpBat ( & RaspBat ) ;
                        break ;
                     }
                     else if ( Mnemons [i].Type == UNITS_DOUBLE )
                     {
                        /* get the number */

                        dtmp = atof ( ArgBuf [ 1 ] ) ;

                        /* find the units string */

                        if (( NumArg < 3 ) || ( strlen ( ArgBuf [2] ) <= 0 ))
                           stmp = Mnemons [i].Dfu ;
                        else
                           stmp = ArgBuf [2] ;

                        /* convert the units to SI */

                        dtmp = ConvDUnit ( Mnemons [i].Unit, dtmp, stmp ) ;

                     }
                     else if ( Mnemons [i].Type == UNITS_INTEGER )
                     {
                        if ( NumArg >= 2 )
                           itmp = atoi ( ArgBuf [ 1 ] ) ;
                        else
                           itmp = 0 ;
                     }
                     else
                     {
                        if ( NumArg >= 2 )
                           stmp = ArgBuf [ 1 ] ;
                        else
                           stmp = NULL ;
                     }

                     switch ( Mnemons [i].Ndx )
                     {
                        case N_H_UNITS:
                           AddBatStr ( & RaspBat.units, stmp ) ;
                           break ;

                        case N_H_HOME:

                           /* v4.2 fix a possible bug */

                           if (( lth = strlen ( ArgBuf [1] )) >= RASP_FILE_LEN )
                           {
                              fprintf ( stderr, 
                                  "your RASPHOME env varb is too long !\n" ) ;
                              fprintf ( stderr, 
                                  "%s\n", ArgBuf [1] ) ;
                              exit ( 1 );
                           }

                           strncpy ( WorkBuf, ArgBuf [1], RASP_FILE_LEN ) ;

                           lth -- ;

                           if (( lth > 0 ) && ( WorkBuf [lth] != DIR_SEP ))
                           {
                              WorkBuf [++lth] = DIRSEP ;
                              WorkBuf [++lth] = '\0' ;
                           }

                           AddBatStr ( & RaspBat.home, WorkBuf ) ;
                           break ;

                        case N_H_MODE:

                           ToLower ( ArgBuf [1] ) ;

                           if (( strncmp ( "quiet", ArgBuf [1], 5 ) == 0 )
                           ||  ( strncmp ( "summa", ArgBuf [1], 5 ) == 0 ))
                              AddBatInt ( & RaspBat.mode, 0 ) ;
                           else
                              AddBatInt ( & RaspBat.mode, 1 ) ;

                           break ;

                        case N_H_QUIET:
                           AddBatInt ( & RaspBat.mode, 0 ) ;
                           break ;
                        case N_H_VERBOSE:
                           AddBatInt ( & RaspBat.mode, 1 ) ;
                           break ;
                        case N_H_DEBUG:
                           AddBatInt ( & RaspBat.mode, 2 ) ;
                           break ;

                        case DTIME:
                           AddBatDbl ( & RaspBat.dtime,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case PRINTTIME:
                           AddBatDbl ( & RaspBat.printtime,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case PRINTCMD:
                           AddBatStr ( & RaspBat.printcmd, stmp ) ;
                           break ;
                        case SITEALT:
                           AddBatDbl ( & RaspBat.sitealt,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case SITETEMP:
                           AddBatDbl ( & RaspBat.sitetemp,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case SITEPRESS:
                           PressOride = 1 ;
                           AddBatDbl ( & RaspBat.sitepress,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case FINALALT:
                           AddBatDbl ( & RaspBat.finalalt,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case COASTTIME:
                           AddBatDbl ( & RaspBat.coasttime,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case RAILLENGTH:
                           AddBatDbl ( & RaspBat.raillength,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case ENGINEFILE:
                           AddBatStr ( & RaspBat.enginefile, stmp ) ;
                           break ;
                        case DESTINATION:
                           AddBatStr ( & RaspBat.destination, stmp ) ;
                           break ;
                        case OUTFILE:
                           AddBatStr ( & RaspBat.outfile, stmp ) ;
                           break ;
                        case THETA:
                           AddBatDbl ( & RaspBat.theta,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;

                        case NUMSTAGES:
                           AddBatInt ( & RaspBat.numstages, itmp ) ;
                           break ;
                        case NOSETYPE:
                           AddBatStr ( & RaspBat.nosetype, stmp ) ;
                           break ;
                        case STAGE:

                           if (( itmp > 0 ) && ( itmp <= MAXSTAGE ))
                           {
                              Stage = itmp ;

                              if ( Stage > RaspBat.numstages.dat )
                                 AddBatInt ( & RaspBat.numstages, itmp ) ;
                           }
                           break ;

                        case STAGEDELAY:
                           AddBatDbl ( & RaspBat.stages [Stage-1].stagedelay,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case DIAMETER:
                           AddBatDbl ( & RaspBat.stages [Stage-1].diameter,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case NUMFINS:
                           AddBatInt ( & RaspBat.stages [Stage-1].numfins,
                                         itmp ) ;
                           break ;
                        case FINTHICKNESS:
                           AddBatDbl ( & RaspBat.stages [Stage-1].finthickness,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case FINSPAN:
                           AddBatDbl ( & RaspBat.stages [Stage-1].finspan,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case DRYMASS:
                           AddBatDbl ( & RaspBat.stages [Stage-1].drymass,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case LAUNCHMASS:
                           AddBatDbl ( & RaspBat.stages [Stage-1].launchmass,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case CD:
                           AddBatDbl ( & RaspBat.stages [Stage-1].cd,
                                         ArgBuf [1], stmp, dtmp ) ;
                           break ;
                        case MOTORNAME:
                           AddBatStr ( & RaspBat.stages [Stage-1].motorname,
                                         stmp ) ;
                           break ;
                        case NUMMOTOR:
                           AddBatInt ( & RaspBat.stages [Stage-1].nummotor,
                                         itmp ) ;
                           break ;
                     }

                     break ;

                  }
               }
            }
         }
      }
      fclose ( BatAddr ) ;
   }
   return ;
}
#ifdef N_C_MAIN

/*************************************************************************/
int main ( int argc, char* argv[] )
/*************************************************************************/
{
   printf("\nRASP - Rocket Altitude Simulation Program V%s\n\n", VERSION);

   if (argc > 1)
   {
      BatchFlite ( argv [1] ) ;
   }

   return (0) ;
}
#endif
