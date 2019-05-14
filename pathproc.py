import os
import sys
import pathlib


def dir_name(filename):
    if not filename:
        return None
    path = pathlib.Path(filename)
    return path.parent

    
def base_name(filename):
    path = pathlib.Path(filename)
    return path.name


def fix_path(path, filename):
    if not path or not filename:
        return filename
    else:
        return str(pathlib.Path(path, filename))


def path_proc(path, what):
    r"""
    This li'l fun() looks for What in a PATHSEP sep'd PATH list
    returns the first fqpn of What or (char *) NULL if not found
    example Path: /bin:/lib:/rocket/lib ( unix PATHSEP )
            Path: \bin;\lib;\rocket\lib ( DOS PATHSEP )
    (somebody gotta help me with VMS)

    order counts !
    """

    for directory in path.split(os.pathsep):
        test_file = pathlib.Path(directory, what)
        if test_file.is_file():
            return test_file

    return None


def whereis(what, env=None, dad=None):
    """
    * notes:  User supplies pointer to Target Buffer
    * ( use PATH_MAX + NAME_MAX + 2  from <sys/limits.h> ??? )
    *
    * search algorithm:
    *
    *    0. Look in `pwd` v4.2
    *          return (1) if found
    *    1. ( EnvV != NULL ) --> try to access What in EnvV PATH
    *          return (1) if found
    *    2. look for a fqpn in Dad, try to access What in Dad's PATH
    *          return (1) if found
    *    3. get the PATH from getenv
    *       clone PATH
    *       for each Dir in PATH:
    *          try to access What in each PATH Dir
    *             return (1) if found
    *    4. return (0) if not found
    *
    *    *** check your return code -- Targ may have trash ! ***
    """

    # 0. Try for What in `pwd`
    targ = path_proc(".", what)
    if targ:
        return targ

    # 1. Try for What in env
    if env:
        path = path_proc(env, what)
        if path:
            return path

    # 2. look for a fqpn in Dad.  ( allows the user to spec a fqpn program )
    if dad:
        path = pathlib.Path(fix_path(dir_name(dad), what))
        if path.is_file():
            return str(path)

    # 3. look for What in the PATH ( if PATH NULL, try for "." )
    return path_proc(os.environ['PATH'], what)


if __name__ == '__main__':
    print(sys.argv, dir_name(sys.argv[0]), base_name(sys.argv[0]))
    print(dir_name(r'c:\users\rnee\file.pdf'))
    print(base_name(r'c:\users\rnee\file.pdf'))
    print(whereis("0K1F.cmd", None, r"c:\dell\uw.cmd"))


