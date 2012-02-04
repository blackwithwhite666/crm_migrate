import logging, re, time

from crm_migrate.utils import cached_property
from crm_migrate.parsers import CibConfig
from crm_migrate.defines import VIRT_PRIMITIVE_NAME
from crm_migrate.exceptions import ManagerException

from .base_manager import BaseManager

logger = logging.getLogger('managers.pacemaker')


class PacemakerManager(BaseManager):
    @cached_property()
    def config(self):
        return CibConfig.create(self.connection)
    
    def get_vm_primitive_name(self, name):
        resource = VIRT_PRIMITIVE_NAME % name
        if not self.config.has_primitive(resource):
            raise ManagerException("Resource %s not exist" % resource)
        return resource
    
    def check_locations(self, name):
        locations = self.config.get_locations(rsc=name)
        if locations:
            raise ManagerException("There are existed constrains: %s" 
                                        % ", ".join([ location.prop('id') for location in locations]))
    
    def get_depended_drbd(self, name):
        return self.config.get_depended_drbd(name)

    def get_resource_status(self, name):
        result = []
        for l in self.connection.execute('crm_resource --resource %s --locate' % name).splitlines():
            m = re.match('^resource (?P<resource>.+) is running on: (?P<host>.+) (?P<status>.*)$', l)
            result.append({
                      'resource': m.group('resource'),
                      'host' : m.group('host'),
                      'status': m.group('status') if len(m.groups()) == 3 else None
                      })
        return result
    
    def get_drbd_master_count(self, name, *hosts):
        return len([ state for state in self.get_resource_status(name) 
                     if (hosts and state['host'] in hosts) or
                        (not hosts and state['status'] == 'Master')])
    
    def is_drbd_in_dual_master_state(self, name, *hosts):
        return self.get_drbd_master_count(name, *hosts) > 1
    
    def is_drbd_in_one_master_state(self, name, *hosts):
        return self.get_drbd_master_count(name, *hosts) == 1
    
    def set_resource_parameter(self, resource, name, value, meta=False):
        self.connection.execute("crm_resource --resource %(resource)s %(meta)s --set-parameter %(name)s --parameter-value %(value)s" 
                                    % {'name': name,
                                       'value': value,
                                       'resource': resource,
                                       'meta': '--meta' if meta else ''
                                       })
        
    def set_resource_master_max(self, resource, node_count):
        if not node_count: raise ManagerException("Bad node count")
        self.set_resource_parameter(resource, 'master-max', int(node_count), meta=True)
    
    def get_active_nodes(self):
        nodes = self.config.get_nodes()
        return [ node.prop('id') for node in nodes 
                 if self.config.get_status_nodes(id=node.prop('id'), ha='active') ]
    
    def _wait_for(self, callback, timeout=10):
        all_is_ready = False 
        time_end = time.time() + timeout
        while (not all_is_ready and time_end > time.time()):
            if callback():
                all_is_ready = True
            else:
                time.sleep(1)
        return all_is_ready
    
    def wait_for_dual_master_state(self, resource, **kwargs):
        def state_check():
            return self.is_drbd_in_dual_master_state(resource)
        return self._wait_for(state_check, **kwargs)
    
    def wait_for_one_master_state(self, resource, **kwargs):
        def state_check():
            return self.is_drbd_in_one_master_state(resource)
        return self._wait_for(state_check, **kwargs)
    
    def migrate_resource(self, resource, host=None):
        self.connection.execute("crm_resource --resource %(resource)s --move %(destination)s" 
                                    % {'resource': resource,
                                       'destination': '--node %s' % host if host else ''
                                       })
    
    def is_resource_on_host(self, resource, host):
        resource_state = self.get_resource_status(resource)
        return resource_state and resource_state[0]['host'] == host
    
    def wait_for_resource_migration(self, resource, host, **kwargs):
        def state_check():
            return self.is_resource_on_host(resource, host)
        return self._wait_for(state_check, **kwargs)
