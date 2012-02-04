import logging

from .managers import ManagerRegistry
from .exceptions import DispatcherException


# create logger
logger = logging.getLogger('dispatcher')


class Dispatcher(object):
    def __init__(self, connection, dry_run, name, destination_node=None):
        self.name = name
        self.destination_node = destination_node
        self.managers = ManagerRegistry(connection=connection, dry_run=dry_run)

    def _select_destination_node(self, nodes, exclude_node):
        for node in nodes:
            if node != exclude_node:
                return node
        raise DispatcherException('No node to migrate')

    def process(self):
        # get nodes
        nodes = self.managers.pacemaker.get_active_nodes()
        logger.debug('Active nodes: %s' % ", ".join(nodes))
        node_count = len(nodes)
        if node_count < 2:
            raise DispatcherException('There are only %d node' % node_count)
            
        # get primitive name to manage
        primitive_to_migrate = self.managers.pacemaker.get_vm_primitive_name(self.name)
        logger.debug('Get resource name: %s' % primitive_to_migrate)
        
        # check existed constrains
        logger.debug('Check existed constrains')
        self.managers.pacemaker.check_locations(primitive_to_migrate)
        
        # get node on which primitive is running
        primitive_state = self.managers.pacemaker.get_resource_status(primitive_to_migrate)[0]
        logger.debug('Currently resource work on %s' % primitive_state['host'])
        
        # node to which migrate
        destination_host = self.destination_node if self.destination_node else self._select_destination_node(nodes, primitive_state['host'])
        if destination_host not in nodes:
            raise DispatcherException('Node %s not exist' % destination_host)
        logger.debug('Migrate resource to %s' % destination_host)
        
        # get depended resource list
        depended_resources = self.managers.pacemaker.get_depended_drbd(primitive_to_migrate)
        logger.debug('Found depended resources: %s' % ", ".join(depended_resources))
        
        # go to dual master state
        for resource in depended_resources:
            if not self.managers.pacemaker.is_drbd_in_dual_master_state(resource):
                logger.debug('Set parameters for %s' % resource)
                self.managers.pacemaker.set_resource_master_max(resource, node_count)
        
        # wait for master state
        logger.debug('Wait for resource changes')
        for resource in depended_resources:
            logger.debug('Wait for %s' % resource)
            if not self.managers.pacemaker.wait_for_dual_master_state(resource):
                raise DispatcherException('Resource %s is not in dual master state' % resource)
        
        # migrate
        logger.debug('Migrate main resource')
        self.managers.pacemaker.migrate_resource(primitive_to_migrate, host=destination_host)
        
        # wait for migration end
        logger.debug('Wait for migration')
        self.managers.pacemaker.wait_for_resource_migration(primitive_to_migrate, destination_host)
        
        # return resources to one master state
        for resource in depended_resources:
            if not self.managers.pacemaker.is_drbd_in_one_master_state(resource):
                logger.debug('Set parameters for %s' % resource)
                self.managers.pacemaker.set_resource_master_max(resource, 1)
        
        # wait for one master state
        logger.debug('Wait for resource changes')
        for resource in depended_resources:
            logger.debug('Wait for %s' % resource)
            if not self.managers.pacemaker.wait_for_one_master_state(resource):
                raise DispatcherException('Resource %s is not in one master state' % resource)