# coding=GB18030
import cx_Oracle
import os
import sys
import json
# import pprint

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.playbook.play import Play
from ansible.plugins.callback.minimal import CallbackModule


def get_json():
    json_string = sys.argv[1]
    # json_string = json_string.decode('utf-8').encode('utf-8')
    # print (type(json_unicode))
    # print 'out' + json_string
    encoding = sys.stdout.encoding
    # json_string = json_unicode.encode('utf-8')
    dict_value = json.loads(json_string, encoding='GB18030')

    # for (k, v) in dict_value.items():
    #     if isinstance(v, dict):
    #         for (kk, vv) in v.items():
    #             print "dict[%s][%s] =" % (k, kk), vv
    #     else:
    #         print "dict[%s] =" % k, v
    # print (dict_value)
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

        # print db.version
        # versioning = db.version.split('.')
        # if versioning[0] == '10':
        #     print "Running 10g"
        # elif versioning[0] == '9':
        #     print "Running 9i"
        # print db.dsn

        # sql = 'SELECT * FROM' + self.table_name
        # # cursor.execute('SELECT * FROM %s',str)
        # cursor.execute(sql)
        # # pprint(cursor.fetchall())
        #
        # # for row in cursor:  ## notice that this is plain English!
        # #     print row
        #
        # column_data_types = cursor.execute('SELECT * FROM ADP_D_HOST')
        #
        # print column_data_types
        #
        # pprint(cursor.description)
        return db.cursor()

    def get_host(self, dict_value):
        cursor = self.get_connect()
        if 'host_type' in dict_value.keys() and 'host_info' in dict_value.keys():
            if dict_value['host_type'] == '2':
                list_obj = dict_value['host_info'].split(',')
                str_obj = ''
                for item in list_obj:
                    str_obj = str_obj + '\'' + str(item).strip() + '\'' + ','
                sql = """SELECT * FROM ADP_D_HOST WHERE HOST_IP IN (""" + str_obj[:-1] + """)"""
                print (sql)
                cursor.execute(sql)
                cursor.rowfactory = self.makedict(cursor)
                result = cursor.fetchall()
                return result
            elif dict_value['host_type'] == '1':
                sql = """SELECT * FROM ADP_D_HOST WHERE HOST_GROUP = '%(host_info)s'"""
                cursor.execute(sql % dict_value)
                cursor.rowfactory = self.makedict(cursor)
                result = cursor.fetchall()
                return result
        else:
            return False

    def get__host_username_password(self, dict_value):
        username_password_dict = {}
        hosts_info = self.get_host(dict_value)
        for host_info in hosts_info:
            hosts_list = []
            if username_password_dict and (
                    host_info['USERNAME'], host_info['PASSWORD']) in username_password_dict.keys():
                username_password_dict[(host_info['USERNAME'], host_info['PASSWORD'])].append(host_info['HOST_IP'])
            else:
                hosts_list.append(host_info['HOST_IP'])
                username_password_dict.setdefault((host_info['USERNAME'], host_info['PASSWORD']), hosts_list)
        return username_password_dict

    def get_exec_log(self, dict_value):
        cursor = self.get_connect()
        if 'batch_id' in dict_value.keys():
            sql = """SELECT * FROM ADP_D_EXCE_LOG WHERE BATCH_ID = '%(batch_id)s'"""
            cursor.execute(sql % dict_value)
            cursor.rowfactory = self.makedict(cursor)
            result = cursor.fetchall()
            return result
        else:
            return False

    def get_task(self, dict_value):
        cursor = self.get_connect()
        if 'task_id' in dict_value.keys() and 'task_type' in dict_value.keys():
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

    def get_res_stats_json(self, dict_value):
        tag_remark = {}
        tag_remark['1'] = '完全成功'
        tag_remark['2'] = '失败'
        tag_remark['4'] = '部分成功'
        # print (tag_remark['4'])
        # print (type(tag_remark.keys()[0]))
        res_stats_dict = CallbackModule().get_res_stats()
        res_stats_dict['batch_id'] = dict_value['batch_id']
        res_stats_dict['task_id'] = dict_value['task_id']
        res_stats_dict['host_type'] = dict_value['host_type']
        res_stats_dict['host_info'] = dict_value['host_info']
        res_stats_dict['error_info'] = ""
        res_stats_dict['process_tag'] = CallbackModule().get_res_tag()
        res_stats_dict['remark'] = tag_remark[CallbackModule().get_res_tag()]
        res_stats_json = json.dumps(res_stats_dict, ensure_ascii=False, encoding='GB18030')
        return res_stats_json

    def run(self, hosts, username, password, playbook):
        Options = namedtuple('Options',
                             ['connection', 'forks', 'module_path', 'ssh_common_args', 'sftp_extra_args',
                              'private_key_file', 'become', 'become_method', 'become_user', 'remote_user',
                              'ssh_extra_args', 'scp_extra_args', 'verbosity', 'check'])
        # initialize needed objects
        variable_manager = VariableManager()
        loader = DataLoader()
        options = Options(connection='smart', forks=20, module_path=None,
                          ssh_common_args=None, sftp_extra_args=None, private_key_file='~/.ssh/id_rsa',
                          become=True, become_method=None, become_user=username,
                          remote_user=username, ssh_extra_args=None, scp_extra_args=None, verbosity=1, check=False)
        passwords = dict(conn_pass=password, become_pass=password)

        # create inventory and pass to var manager
        inventory = Inventory(loader=loader, variable_manager=variable_manager,
                              host_list=hosts)
        variable_manager.set_inventory(inventory)

        play = Play().load(playbook, variable_manager=variable_manager, loader=loader)

        # actually run it
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                options=options,
                passwords=passwords,
                stdout_callback='minimal'
            )
            result = tqm.run(play)
            # print (result)
        finally:
            if tqm is not None:
                tqm.cleanup()
