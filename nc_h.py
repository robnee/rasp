#ifndef N_H

#define N_H

#define  N_H_NONE            0

#define  N_H_UNITS           1
#define  N_H_QUIET           2
#define  N_H_VERBOSE         3
#define  DTIME               4
#define  PRINTTIME           5
#define  PRINTCMD            6

#define  SITEALT             7
#define  SITETEMP            8
#define  SITEPRESS           9
#define  FINALALT            0
#define  RAILLENGTH         11
#define  ENGINEFILE         12

#define  NUMSTAGES          13
#define  NOSETYPE           14
#define  STAGE              15
#define  STAGEDELAY         16
#define  DIAMETER           17
#define  NUMFINS            18
#define  FINTHICKNESS       19
#define  FINSPAN            20
#define  DRYMASS            21
#define  LAUNCHMASS         22
#define  CD                 23
#define  MOTORNAME          24
#define  NUMMOTOR           25
#define  DESTINATION        26
#define  OUTFILE            27
#define  THETA              28
#define  LAUNCH             29
#define  N_H_QUIT           30
#define  N_H_DEBUG          31
#define  N_H_DUMP           32
#define  TITLE              33
#define  COASTTIME          34
#define  N_H_MODE           35
#define  N_H_HOME           36

   typedef struct str_info
   {
      char  * dat ;
   }  str_info ;

   typedef struct log_info
   {
      int dat ;
   }  log_info ;

   typedef struct int_info
   {
      int dat ;
   }  int_info ;

   typedef struct dbl_info
   {
      char * inp  ;
      char * unt  ;
      double dat  ;
   }  dbl_info ;

   typedef struct Mnemonics
   {
      char  * Tag ;
      char  * Dfu ;
      int     Ndx ;
      int    Type ;
      int    Unit ;
   }  MneData ;

   typedef struct StageBat
   {
      dbl_info stagedelay ;
      dbl_info diameter ;
      int_info numfins ;
      dbl_info finthickness ;
      dbl_info finspan ;
      dbl_info drymass ;
      dbl_info launchmass ;
      dbl_info cd ;
      str_info motorname ;
      int_info nummotor ;
   }  StageBat ;

   typedef struct Rocket
   {
      str_info title ;
      str_info home  ;
      str_info units ;

      int_info mode ;
      dbl_info dtime ;
      dbl_info printtime ;
      str_info printcmd ;

      dbl_info sitealt ;
      dbl_info sitetemp ;
      dbl_info sitepress ;
      dbl_info theta ;
      dbl_info finalalt ;
      dbl_info coasttime ;
      dbl_info raillength ;
      str_info enginefile ;
      str_info destination ;
      str_info outfile ;

      str_info nosetype ;
      int_info numstages ;
      StageBat stages [MAXSTAGE] ;

   }  Rocket ;

#ifdef N_C

   MneData Mnemons [ ] =
   {
      { "none"           , ""    , N_H_NONE    , UNITS_NONE     , UNITS_NONE } ,
      { "home"           , ""    , N_H_HOME    , UNITS_STRING   , UNITS_NONE } ,
      { "homedir"        , ""    , N_H_HOME    , UNITS_STRING   , UNITS_NONE } ,
      { "rasphome"       , ""    , N_H_HOME    , UNITS_STRING   , UNITS_NONE } ,
      { "raspdir"        , ""    , N_H_HOME    , UNITS_STRING   , UNITS_NONE } ,
      { "units"          , ""    , N_H_UNITS   , UNITS_STRING   , UNITS_NONE } ,
      { "mode"           , ""    , N_H_MODE    , UNITS_STRING   , UNITS_NONE } ,
      { "quiet"          , ""    , N_H_QUIET   , UNITS_INTEGER  , UNITS_NONE } ,
      { "summary"        , ""    , N_H_QUIET   , UNITS_INTEGER  , UNITS_NONE } ,
      { "verbose"        , ""    , N_H_VERBOSE , UNITS_INTEGER  , UNITS_NONE } ,
      { "detail"         , ""    , N_H_VERBOSE , UNITS_INTEGER  , UNITS_NONE } ,
      { "launch"         , ""    , LAUNCH      , UNITS_NONE     , UNITS_NONE } ,
      { "quit"           , ""    , N_H_QUIT    , UNITS_NONE     , UNITS_NONE } ,
      { "done"           , ""    , N_H_QUIT    , UNITS_NONE     , UNITS_NONE } ,
      { "exit"           , ""    , N_H_QUIT    , UNITS_NONE     , UNITS_NONE } ,
      { "debug"          , ""    , N_H_DEBUG   , UNITS_INTEGER  , UNITS_NONE } ,
      { "dump"           , ""    , N_H_DUMP    , UNITS_NONE     , UNITS_NONE } ,
      { "title"          , ""    , TITLE       , UNITS_NONE     , UNITS_NONE } ,

      { "dtime"          , "sec" , DTIME       , UNITS_DOUBLE   , UNITS_TIME } ,
      { "printtime"      , "sec" , PRINTTIME   , UNITS_DOUBLE   , UNITS_TIME } ,
      { "printcommand"   , ""    , PRINTCMD    , UNITS_STRING   , UNITS_NONE } ,

      { "sitealtitude"   , "ft"  , SITEALT     , UNITS_DOUBLE   , UNITS_LENGTH } ,
      { "finalaltitude"  , "ft"  , FINALALT    , UNITS_DOUBLE   , UNITS_LENGTH } ,
      { "coasttime"      , "sec" , COASTTIME   , UNITS_DOUBLE   , UNITS_TIME } ,
      { "sitetemperature", "F"   , SITETEMP    , UNITS_DOUBLE   , UNITS_TEMP } ,
      { "sitepressure"   , "inHg", SITEPRESS   , UNITS_DOUBLE   , UNITS_PRESS } ,
      { "raillength"     , "in"  , RAILLENGTH  , UNITS_DOUBLE   , UNITS_LENGTH } ,
      { "rodlength"      , "in"  , RAILLENGTH  , UNITS_DOUBLE   , UNITS_LENGTH } ,
      { "enginefile"     , ""    , ENGINEFILE  , UNITS_FILENAME , UNITS_EXISTS } ,
      { "motorfile"      , ""    , ENGINEFILE  , UNITS_FILENAME , UNITS_EXISTS } ,

      { "numstages"      , ""    , NUMSTAGES   , UNITS_INTEGER  , UNITS_NONE } ,
      { "nosetype"       , ""    , NOSETYPE    , UNITS_STRING   , UNITS_NONE } ,
      { "stage"          , ""    , STAGE       , UNITS_INTEGER  , UNITS_NONE } ,
      { "stagedelay"     , "sec" , STAGEDELAY  , UNITS_DOUBLE   , UNITS_TIME } ,
      { "diameter"       , "in"  , DIAMETER    , UNITS_DOUBLE   , UNITS_LENGTH } ,
      { "numfins"        , ""    , NUMFINS     , UNITS_INTEGER  , UNITS_NONE } ,
      { "finthickness"   , "in"  , FINTHICKNESS, UNITS_DOUBLE   , UNITS_LENGTH } ,
      { "finspan"        , "in"  , FINSPAN     , UNITS_DOUBLE   , UNITS_LENGTH } ,
      { "drymass"        , "oz"  , DRYMASS     , UNITS_DOUBLE   , UNITS_MASS } ,
      { "dmass"          , "oz"  , DRYMASS     , UNITS_DOUBLE   , UNITS_MASS } ,
      { "mass"           , "oz"  , DRYMASS     , UNITS_DOUBLE   , UNITS_MASS } ,
      { "launchmass"     , "oz"  , LAUNCHMASS  , UNITS_DOUBLE   , UNITS_MASS } ,
      { "lmass"          , "oz"  , LAUNCHMASS  , UNITS_DOUBLE   , UNITS_MASS } ,
      { "cd"             , ""    , CD          , UNITS_DOUBLE   , UNITS_NONE } ,
      { "motorname"      , ""    , MOTORNAME   , UNITS_STRING   , UNITS_NONE } ,
      { "enginename"     , ""    , MOTORNAME   , UNITS_STRING   , UNITS_NONE } ,
      { "nummotor"       , ""    , NUMMOTOR    , UNITS_INTEGER  , UNITS_NONE } ,
      { "numengine"      , ""    , NUMMOTOR    , UNITS_INTEGER  , UNITS_NONE } ,
      { "destination"    , ""    , DESTINATION , UNITS_STRING   , UNITS_NONE } ,
      { "outfile"        , ""    , OUTFILE     , UNITS_FILENAME , UNITS_NONE } ,
      { "outputfile"     , ""    , OUTFILE     , UNITS_FILENAME , UNITS_NONE } ,
      { "theta"          , "deg" , THETA       , UNITS_DOUBLE   , UNITS_ANGLE } ,
      { "launchangle"    , "deg" , THETA       , UNITS_DOUBLE   , UNITS_ANGLE } 
   } ;

#define  NUM_MNEMONS   ( sizeof ( Mnemons ) / sizeof ( MneData ))

   void  AddBatStr ( str_info *, char * ) ;
   void  AddBatInt ( int_info *, int ) ;
   void  AddBatDbl ( dbl_info *, char *, char *, double ) ;
   void  InitBat ( Rocket * ) ;
   void  DumpBat ( Rocket * ) ;
   void  ToDaMoonAlice () ;
   void  BatchFlite ( char * ) ;

#else

   /* extern void  AddBatStr ( str_info *, char * ) ;                /* hide */
   /* extern void  AddBatInt ( int_info *, int ) ;                   /* hide */
   /* extern void  AddBatDbl ( dbl_info *, char *, char *, double ); /* hide */
   /* extern void  InitBat ( Rocket * ) ;                            /* hide */
   extern void  DumpBat ( Rocket * ) ;
   extern void  ToDaMoonAlice () ;
   extern void  BatchFlite ( char * ) ;

#endif

#endif
