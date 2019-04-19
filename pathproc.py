import os
import pathlib


dir_name(filename):
    path = pathlib.Path(filename)
    print(path.parts)
    
   if (( q = strrchr ( File, DIRSEP )) == (char *) NULL )
      Targ [0] = '\0' ;
   else
   {
      p = File ;

      while ( p < q )
      {
         Targ [i++] = * p ;
         p ++ ;
      }
      Targ [i] = '\0' ;
   }

   return ( Targ ) ;
}


base_name(filename):
   if (( q = strrchr ( File, DIRSEP )) == (char *) NULL )
      strncpy ( Targ, File, BufLen-1 ) ;
   else
   {
      if (( File + strlen ( File ) - 1 ) == q )     /* dupe unix behaviour */
      {
         if ( q == File )
            Targ [0] = '\0' ;
         else
         {
            while ( --p >= File )
               if ( *p == DIRSEP )
                  break ;

            i = 0 ;

            while ( ++p < q )
            {
               Targ [i++] = * p ;
            }

            Targ [i] = '\0' ;
         }
      }
      else
      {
         strncpy ( Targ, ++q, BufLen-1 ) ;
      }
   }

   return ( Targ ) ;
}


if __name__ == '__main__':
    print(dir_name('.'))
