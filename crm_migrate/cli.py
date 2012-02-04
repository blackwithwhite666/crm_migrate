import logging
import traceback
import sys
import os
from optparse import OptionParser

from .utils import debug
from .dispatcher import Dispatcher
from .ssh import Connection

# create logger
logger = logging.getLogger('main')


def main():
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    
    parser.add_option("-n", "--name", dest='name', 
                      help="resource name")
    
    parser.add_option("-t", "--dry-run", 
                      action="store_true", dest="dry_run")
    
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    
    parser.add_option("-d", "--host", dest="host", default="localhost",
                      action="store", type="string")
    
    parser.add_option("-u", "--user", dest="user", default="root",
                      action="store", type="string")
    
    parser.add_option("-k", "--private-key", dest="private_key", default='',
                      action="store", type="string")
    
    parser.add_option("-r", "--port", dest="port", default=22,
                      action="store", type="int")
    
    parser.add_option("-e", "--dest", dest="destination_node", default=None,
                      action="store", type="string")
    
    (options, _args) = parser.parse_args()
    
    if not options.name:
        parser.error("resource name missing (--name)")
    if not options.host:
        parser.error("host is missing (--host)")
    if not options.user:
        parser.error("user is missing (--user)")
    if not options.port:
        parser.error("port is missing (--port)")
        
    if options.verbose or options.dry_run:
        debug()
    
    logger.info('Connect to %s...' % options.host)
    password = ''
    ssh_params = {'host': options.host, 'username': options.user, 
                  'password': password, 'private_key': options.private_key or None,
                  'port': options.port}
    
    try:
        
        connection = Connection(**ssh_params)
        Dispatcher(connection=connection, 
                   dry_run=options.dry_run, 
                   name=options.name, destination_node=options.destination_node
                   ).process()

    except:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
