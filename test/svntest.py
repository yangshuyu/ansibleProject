#!/usr/bin/python2

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager

Options = namedtuple('Options',
                     ['connection', 'forks', 'module_path', 'ssh_common_args', 'sftp_extra_args',
                      'private_key_file', 'become', 'become_method', 'become_user', 'remote_user',
                      'ssh_extra_args', 'scp_extra_args', 'verbosity', 'check'])
# initialize needed objects
variable_manager = VariableManager()
loader = DataLoader()
options = Options(connection='smart', forks=20, module_path=None,
                  ssh_common_args=None, sftp_extra_args=None, private_key_file='~/.ssh/id_rsa',
                  become=True, become_method=None, become_user='adp',
                  remote_user='adp', ssh_extra_args=None, scp_extra_args=None, verbosity=1, check=False)
passwords = dict(conn_pass='adp', become_pass='adp')

# create inventory and pass to var manager
inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list='localhost')
variable_manager.set_inventory(inventory)

# create play with tasks
play_source = dict(
    name="Ansible Play",
    hosts='localhost',
    gather_facts='no',
    tasks=[
        dict(action=dict(module='subversion', args=dict(dest='/ngbss/adp/svndocker',
                                                        repo='http://10.124.0.19/svn/CBSS4G/branches/branch_160607/BSS4.2/billing_X86/credit/src',
                                                        username='Oreader', password='Oreader')))
    ]
)
play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

# actually run it
tqm = None
try:
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=options,
        passwords=passwords,
        stdout_callback='minimal',
    )
    result = tqm.run(play)
finally:
    if tqm is not None:
        tqm.cleanup()
