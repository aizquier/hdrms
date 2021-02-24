# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
#import colorama
import termcolor
import inspect
import os

colored = termcolor.colored


class _Console:
    def __init__(self):
        self.justify = False
        self.outfile = sys.stdout

    def set_outfile(self, outfilename):
        if outfilename == 'stdout':
            self.outfile = sys.stdout
        elif outfilename == 'stderr':
            self.outfile = sys.stderr
        else:
            self.outfile = outfilename #open(outfilename, 'a')
            self.mode_color = None

    def _print(self, *args, **kwargs):
        """Prints the string preceded by the caller file name
        and line number.
        n : emulates the -n parameter of bash's echo
        exit: exits after print

        """

        # * get value of _n . set it as False by default if undefined.
        _n = kwargs['n'] if 'n' in kwargs else False
        _exit = kwargs['exit'] if 'exit' in kwargs else False
        _exitcode = int(kwargs['exitcode']) if 'exitcode' in kwargs else 0


        # * Returns the current line number in our program.
        # * (see http://code.activestate.com/recipes/
        # *   145297-grabbing-the-current-line-number-easily/)
        # * (two levels back from the current frame
        # *  currentframe().f_back.f_back )
        current_line = inspect.currentframe().f_back.f_back.f_lineno
        current_file = os.path.basename(inspect.getfile(inspect.currentframe().f_back.f_back))

        con_head_str = "[%s:%d]" % (current_file, current_line)
        if self.justify:
            con_head_str = "%s%s " % (  " "*(22- len(con_head_str)),
                                    con_head_str, )

        if self.mode_color is not None:
            con_head_str = colored(con_head_str, self.mode_color)

        if (self.outfile == sys.stdout) or (self.outfile == sys.stderr):
            print(con_head_str, end=" ", file=self.outfile)
        else:
            with open(self.outfile, 'a') as stream:
                print(con_head_str, end=" ", file=stream)

        for string in args:
            if self.mode_color is not None:
                string = colored(string, self.mode_color)

            if (self.outfile == sys.stdout) or (self.outfile == sys.stderr):
                print(string, end=" ", file=self.outfile)
            else:
                with open(self.outfile, 'a') as stream:
                    print(string, end=" ", file=stream)

        if not _n:
            if (self.outfile == sys.stdout) or (self.outfile == sys.stderr):
                print("\n", end=" ", file=self.outfile)
            else:
                with open(self.outfile, 'a') as stream:
                    print("\n", end=" ", file=stream)

        if _exit:
            sys.exit(_exitcode)

    def log(self, *args, **kwargs):
        self.mode_color = None
        self._print(*args, **kwargs)

    def debug(self, *args, **kwargs):
        if self.outfile == sys.stderr:
            self.mode_color = 'yellow'
        else:
            self.mode_color = None

        self._print(*args, **kwargs)

    def error(self, *args, **kwargs):
        if self.outfile == sys.stderr:
            self.mode_color = 'red'
        else:
            self.mode_color = None

        self._print(*args, **kwargs)


'''
class _Console:

    def log(self, *args, **kwargs):
        """Prints the string preceded by the caller file name
        and line number.
        _n : emulates the -n parameter of bash's echo
        """

        # * get value of _n . set it as False by default if undefined.
        _n = kwargs['_n'] if '_n' in kwargs else False

        # * Returns the current line number in our program.
        # * (see http://code.activestate.com/recipes/
        # *   145297-grabbing-the-current-line-number-easily/)
        current_line = inspect.currentframe().f_back.f_lineno
        current_file = \
          os.path.basename(inspect.getfile(inspect.currentframe().f_back))

        print "[%s:%d] " % (current_file, current_line),

        for string in args:
            print string,

        if not _n:
            print

    def debug(self, *args, **kwargs):
        """Prints in red color the string preceded by the caller file name
        and line number.
        _n : emulates the -n parameter of bash's echo
        """

        # * get value of _n . set it as False by default if undefined.
        _n = kwargs['_n'] if '_n' in kwargs else False

        # * Returns the current line number in our program.
        # * (see http://code.activestate.com/recipes/
        # *   145297-grabbing-the-current-line-number-easily/)
        current_line = inspect.currentframe().f_back.f_lineno
        current_file = \
          os.path.basename(inspect.getfile(inspect.currentframe().f_back))

        print colored("[%s:%d] " % (current_file, current_line), 'yellow' ),

        for string in args:
            print colored(string, 'yellow'),

        if not _n:
            print

    def error(self, *args, **kwargs):
        """Prints in red color the string preceded by the caller file name
        and line number.
        _n : emulates the -n parameter of bash's echo
        """

        # * get value of _n . set it as False by default if undefined.
        _n = kwargs['_n'] if '_n' in kwargs else False
        _exit = kwargs['exit'] if 'exit' in kwargs else False

        # * Returns the current line number in our program.
        # * (see http://code.activestate.com/recipes/
        # *   145297-grabbing-the-current-line-number-easily/)
        current_line = inspect.currentframe().f_back.f_lineno
        current_file = \
          os.path.basename(inspect.getfile(inspect.currentframe().f_back))

        print colored("[%s:%d] " % (current_file, current_line), 'red' ),

        for string in args:
            print colored(string, 'red'),

        if not _n:
            print

        if _exit:
            sys.exit()

'''

console = _Console()


if __name__ == '__main__':
    console.debug("Please run main.py!")
