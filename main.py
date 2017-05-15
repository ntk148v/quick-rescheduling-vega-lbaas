from neutron import context as ncontext
from neutron.common import rpc
from neutron_lbaas.services.loadbalancer.plugin import LoadBalancerPluginv2
from oslo_config import cfg


def reschedule_loadbalancer(loadbalancer_id):
    context = ncontext.get_admin_context()
    cfg.CONF(default_config_files=[
             '/etc/neutron/neutron.conf',
             '/etc/neutron/lbaas_agent.ini',
             '/etc/neutron/neutron_lbaas.conf',
             ])
    rpc.init(cfg.CONF)
    plugin = LoadBalancerPluginv2()
    # NOTE: use only for haproxy
    loadbalancer = plugin.drivers['haproxy'].load_balancer
    # Reschedule loadbalancer
    loadbalancer.reschedule_loadbalancer(context, loadbalancer_id)


def main():
    loadbalancer_id = raw_input(
        'Enter the loadbalancer\'s id you want to reschedule: ')
    reschedule_loadbalancer(loadbalancer_id)


if __name__ == '__main__':
    main()
