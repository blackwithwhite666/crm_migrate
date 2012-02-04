from .pacemaker_manager import PacemakerManager


class ManagerRegistry(object):
    class_mapping = (
                     ('pacemaker', PacemakerManager),
                     )
    
    def __init__(self, connection, dry_run=False):
        self.dry_run = dry_run
        self.connection = connection
        self.managers = {}
        self.class_dict = dict(self.class_mapping)
    
    def __getattr__(self, name):
        try:
            manager = self.managers[name]
        except KeyError:
            if name not in self.class_dict:
                raise AttributeError
            manager = self.managers[name] = self.class_dict[name](connection=self.connection, dry_run=self.dry_run)
        return manager
        