import subprocess
import time


from neutron import context as ncontext
from neutron.common import rpc
from neutron_lbaas.services.loadbalancer.plugin import LoadBalancerPluginv2
from oslo_config import cfg


def run_cmd_over_ssh(cmd, host):
    ssh = subprocess.Popen(["ssh", "%s" % host, cmd],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print 'ERROR: %s' % error
    else:
        print result


def q_and_a(cmd, host):
    """Q&A part"""
    while True:
        answer = raw_input('Do you want to exectue \
            \' %(cmd)s \' in %(host)s? (y/n): ' % {
            'cmd': cmd,
            'host': host,
        })
        if answer == 'y':
            run_cmd_over_ssh(cmd, host)
            break
        elif answer == 'n':
            break
        else:
            print 'Answer mus be y or n.'


def remove_unused_loadbalancer(loadbalancer_id, prev_host):
    remove_port_cmd = 'ip netns del qlbaas-' + loadbalancer_id
    # Remove port qlbaas-<loadbalancer_id>
    q_and_a(remove_port_cmd, prev_host)
    remove_haproxy_config_dir = 'rm -rf /var/lib/neutron/lbaas/v2/' + \
                                loadbalancer_id
    # Remove haproxy config dir
    q_and_a(remove_haproxy_config_dir, prev_host)
    kill_haproxy_process = 'ps -ef | grep ' + loadbalancer_id + '\
                 | grep -v grep | awk \'{print $2}\' | xargs kill -9'
    # Kill haproxy process
    q_and_a(kill_haproxy_process, prev_host)


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
    # Get current agent
    prev_agent = loadbalancer.get_agent_hosting_loadbalancer(context,
                                                             loadbalancer_id)
    prev_agent_data = prev_agent['agent']
    try:
        # Reschedule loadbalancer
        loadbalancer.reschedule_loadbalancer(context, loadbalancer_id)
        new_agent = loadbalancer.get_agent_hosting_loadbalancer(context,
                                                                loadbalancer_id)
        new_agent_data = new_agent['agent']
        print 'Move lb from %(prev_host)s to %(new_host)s!' % {
            'prev_host': prev_agent_data['host'],
            'new_host': new_agent_data['host'],
        }
        print 'Waiting for 5 seconds...'
        time.sleep(5)  # delays for 5 seconds
        if prev_agent_data['host'] != new_agent_data['host']:
            remove_unused_loadbalancer(loadbalancer_id, prev_agent_data['host'])
        else:
            print 'Same host.'
    except Exception as e:
        print 'ERROR: %s' % str(e)


def main():
    loadbalancer_id = raw_input(
        'Enter the loadbalancer\'s id you want to reschedule: ')
    reschedule_loadbalancer(loadbalancer_id)


if __name__ == '__main__':
    main()
