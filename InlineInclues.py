#!/usr/bin/python
#
# The Atom/TTS extension supports #include to insert files.  Unfortunately
# when loading scripts from TTS it only adds the #include, so if the user
# does not have the script in question in their filesystem everything breaks.
#
# This quick hack reads a ttslua script, injecting #include content.
# At the time of this writing this is a one-way transformation.

from os.path import expanduser
import re
import sys

includePattern = re.compile('^#include <(~/.*)>$')
delim = '-- ############################################################################\n'

def process(src):
    insideComment = False
    for line in src:
        if line.find('--[[') != -1:
            insideComment = True
        if line.find(']]') != -1:
            insideComment = False
        if line.startswith('#include') and not insideComment:
            m = includePattern.search(line)
            filename = m.group(1) + '.ttslua'
            sys.stdout.write(delim)
            sys.stdout.write('-- #### #include <' + filename + '>\n')
            sys.stdout.write(delim)
            sys.stdout.write('do\n')
            sys.stdout.write('\n')
            filename = expanduser(filename)
            include = open(filename)
            process(include)
            include.close()
            sys.stdout.write('\n')
            sys.stdout.write('end\n')
        else:
            sys.stdout.write(line)

process(sys.stdin)
sys.stdout.flush()
