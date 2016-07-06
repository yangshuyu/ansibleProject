# coding=GB18030
import cx_Oracle
import os
import sys
import json

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager


def get_json():
    json_string = sys.argv[1]
    dict_value = json.loads(json_string, encoding='GB18030')

    # for (k, v) in dict_value.items():
    #     if isinstance(v, dict):
    #         for (kk, vv) in v.items():
    #             print "dict[%s][%s] =" % (k, kk), vv
    #     else:
    #         print "dict[%s] =" % k, v

    return dict_value


def dict_to_list(keyword, dict_var):
    list_var = []
    for item in dict_var:
        list_var.append(item[keyword])
    return list_var


class GetParamValue(object):
    def __init__(self, username, password, host_string):
        self.username = username
        self.password = password
        self.host_string = host_string

    def makedict(self, cursor):
        cols = [d[0] for d in cursor.description]

        def createrow(*args):
            return dict(zip(cols, args))

        return createrow

    def get_connect(self):
        db = cx_Oracle.connect(self.username, self.password, self.host_string)
        return db.cursor()

    def get_host(self, dict_value):
        cursor = self.get_connect()
        if dict_value.has_key('host_type') and dict_value.has_key('host_info'):
            if dict_value['host_type'] == '0':
                return dict_value['host_info'].split(',')
            elif dict_value['host_type'] == '1':
                sql = """SELECT * FROM ADP_D_HOST WHERE HOST_GROUP = '%(host_info)s'"""
                cursor.execute(sql % dict_value)
                cursor.rowfactory = self.makedict(cursor)
                result = cursor.fetchall()
                return result
        else:
            return False

    def get_exec_log(self, dict_value):
        cursor = self.get_connect()
        if dict_value.has_key('batch_id'):
            sql = """SELECT * FROM ADP_D_EXCE_LOG WHERE BATCH_ID = '%(batch_id)s'"""
            cursor.execute(sql % dict_value)
            cursor.rowfactory = self.makedict(cursor)
            result = cursor.fetchall()
            return result
        else:
            return False

    def get_task(self, dict_value):
        cursor = self.get_connect()
        if dict_value.has_key('task_id') and dict_value.has_key('task_type'):
            sql = """SELECT * FROM ADP_D_TASK WHERE TASK_ID = '%(task_id)s'"""
            cursor.execute(sql % dict_value)
            cursor.rowfactory = self.makedict(cursor)
            result = cursor.fetchall()
            return result
        else:
            return False

    def get_vars(self, dict_value):
        new_list = []
        tmp = {}
        old_list = self.get_task(dict_value)
        for item in old_list:
            param_code = item['PARA_IN_CODE'].split('|')
            param_value = item['PARA_IN_VALUE'].split('|')
            for index in range(len(param_code)):
                tmp.setdefault(param_code[index], param_value[index])
            new_list.append(tmp)
        return new_list

    def get_dispatch(self, dict_value):
        cursor = self.get_connect()
        if 'task_id' in dict_value.keys() and 'task_type' in dict_value.keys():
            dispatch_group_list = self.get_vars(dict_value)
            results_list = []
            for item in dispatch_group_list:
                sql = """SELECT * FROM ADP_D_DISPATCH WHERE DISPATCH_GROUP = '%(dispatch_group)s'"""
                cursor.execute(sql % item)
                cursor.rowfactory = self.makedict(cursor)
                results = cursor.fetchall()
                if 'adp-date' in item.keys():
                    for result in results:
                        result['DEST'] = result['DEST'].replace('{adp-date}', dict_value['vars']['adp-date'])
                        results_list.append(result)
                else:
                    for result in results:
                        results_list.append(result)
            return results_list
        else:
            return False

    def run(self, hosts, src, dest):
        Options = namedtuple('Options',
                             ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection', 'module_path', 'forks',
                              'remote_user', 'remote_port','private_key_file', 'ssh_common_args', 'ssh_extra_args',
                              'sftp_extra_args','record_host_keys','ask_pass','host_key_checking','ssh_args',
                              'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])

        # initialize needed objects
        variable_manager = VariableManager()
        loader = DataLoader()
        options = Options(listtags=False, listtasks=False, listhosts=True, syntax=False, connection='smart',
                          module_path=None, forks=10,
                          remote_user='gtm', remote_port=22,private_key_file='~/.ssh/known_hosts', ssh_common_args='', ssh_extra_args='',
                          sftp_extra_args=None, record_host_keys=True,host_key_checking = False,ssh_args = "",ask_pass=True,scp_extra_args=None, become=False, become_method=None,
                          become_user='gtm'
                          , verbosity=None, check=False)
        passwords = dict(conn_pass='gtm', become_pass='gtm')

        # create inventory and pass to var manager
        inventory = Inventory(loader=loader, variable_manager=variable_manager,
                              host_list=hosts)
        variable_manager.set_inventory(inventory)

        # create play with tasks
        print hosts
        play_source = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='yes',
            tasks=[
                dict(action=dict(module='file',
                                 args=dict(state='directory', path=dest, mode='755', owner='gtm'))),
                dict(action=dict(module='shell', args='cp -r '+src+' '+dest), register='shell_out'),
                dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
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
                stdout_callback='default',
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()


def main():
    dict_value = get_json()
    copyrun = GetParamValue('adp', 'adp', '10.161.24.215:1621/ACT61')
    hosts = dict_to_list('HOST_IP', copyrun.get_host(dict_value))
    dispatch_dict = copyrun.get_dispatch(dict_value)
    for item in dispatch_dict:
        print (item['SRC'])
        print (item['DEST'])
        copyrun.run(hosts, item['SRC'], item['DEST'])


main()
