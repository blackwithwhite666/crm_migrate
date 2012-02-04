class BaseManager(object):
    def __init__(self, connection, dry_run=False):
        self.dry_run = dry_run
        self.connection = connection
        
    @property
    def config(self):
        raise NotImplementedError()