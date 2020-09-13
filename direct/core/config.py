

from configparser import ConfigParser
import os
import collections 

def Load(cfgfile="direct.ini"):
    """
    load configuration from file
    """
    if not os.path.exists(cfgfile):
        return collections.defaultdict()
    parser = ConfigParser()
    with open(cfgfile, 'r') as f:
        parser.read_file(f)
    return parser