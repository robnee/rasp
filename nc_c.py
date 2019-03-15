import units
import math
import raspinfo

VERSION = '4.2'
press_oride = False


class Dbl:
    def __init__(self, inp, unit):
        self.inp = inp
        self.unit = unit
    
    def __float__(self):
        return float(self.inp)

    def __str__(self):
        return " ".join((self.inp, self.unit))

    def conv_unit(self, unit):
        return units.conv_unit(float(self.inp))


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
        
        # AddBatDbl ( & BatStru->sitetemp, "59.0", "F", 288.15 )
        
        self.sitetemp = Dbl("59.0", "F")
        self.sitepress = Dbl("1013.25", "mb")
        self.finalalt = Dbl("0.00", "ft")
        self.coasttime = Dbl("0.00", "sec")
        
        # self.raillength, "5.00", "ft", 1.523999995 )
        
        self.raillength = Dbl("5.00", "ft")
        self.enginefile = "rasp.eng"
        self.destination = "screen"
        self.outfile = ""
        self.theta = Dbl("0.00", "deg")
        self.nosetype = "ogive"

        self.stages = [Stage()]

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


def to_da_moon_alice(rocket):
    wt = 0.0
    nexteng = 0
    rocketwt = 0.0

    rname = rocket.title
    # strncpy ( ename, rocket.enginefile, RASP_BUF_LEN ) ; /* v4.0a */
    # sprintf ( ename, "%s%s", rocket.home, rocket.enginefile );

    if rocket.mode > 0:
        verbose = True
    else:
        verbose = False
    
    nose = find_nose(rocket.nosetype)
    stagenum = len(rocket.stages)
    
    site_alt = rocket.sitealt
    coast_base = rocket.coasttime    
    base_temp = rocket.sitetemp
    rod = rocket.raillength
    
    if PressOride:
        baro_press = rocket.sitepress / IN2PASCAL
    else:
        baro_press = 1 - ( 0.00000688 * site_alt * M2FT )
        baro_press =  STD_ATM * exp ( 5.256 * log ( baro_press ))
    
    mach1_0 = math.sqrt (MACH_CONST * base_temp)
    Rho_0 = (baro_press * IN2PASCAL) / (GAS_CONST_AIR * base_temp)
    
    if sys.platform == "Windows"
        if rocket.destination == "printer":
            fname = "CON"
        else:
            fname = "PRN"
    elif platform == "Linux":
        if rocket.destination == "printer":
            fname = "/dev/lp"
        else:
            fname = "/dev/tty"
    
    if rocket.outfile:
        fname = rocket.outfile
    
    for stage in rocket.stages:
        e = raspinfo.findmotor(stage.motorname)

        stage.engcnum = e
        stage.engnum  = stage.nummotor
        stage.weight  = stage.drymass
        stage.maxd    = stage.diameter / IN2M
        
        fins.num       = rocket.stages [i].numfins
        fins [i].thickness = rocket.stages [i].finthickness / IN2M
        fins [i].span      = rocket.stages [i].finspan / IN2M
        fins [i].area      = fins [i].num * fins [i].thickness * fins [i].span * IN2M * IN2M
        
        stages [i].cd      = rocket.stages [i].cd
        
        if i == 0:
            stages[i].start_burn = 0.0
        else:
            stages[i].start_burn = stages [i-1].end_stage
        
        stages[i].end_burn = stages[i].start_burn + e_info[stages[i].engcnum].t2
        
        stages[i].end_stage = stages[i].end_burn + rocket.stages [i].stagedelay
        
        stages[i].totalw = stages[i].weight + (e_info[stages[i].engcnum].wt * stages[i].engnum);
  
        rocketwt += stages[i].totalwt
    
    if (( stream = fopen ( fname, "w" )) == NULL ):
      fprintf ( stderr, "cannot open %s\n", fname )
      return
    
    wt = rocketwt
    
    fprintf ( stderr, "Launching ( %s ) ...\n", Mcode )
    
    dumpheader ( wt )
    
    calc ()
"""


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

                              if ( Stage > RaspBat.numstages )
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
"""

def main():
    print("\nRASP - Rocket Altitude Simulation Program V%s\n" % VERSION)

    print(sys.argv)
    if sys.argv:
        batch_flite(sys.argv)


if __name__ == '__main__':
    main()
