from __future__ import absolute_import
from __future__ import print_function
import sys
from os import walk
import os
from importlib import reload

walkPaths = [os.path.expanduser('~\\maya\\scripts')]

for p in walkPaths:
    for root, dirs, files in walk(p):
        if not root in sys.path and not 'install' in root and not '.git' in root:
            sys.path.append(root)
            print('add: %s'%root)

print('RMH script init:', walkPaths)

