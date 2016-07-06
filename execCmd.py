# -*- coding: GB18030 -*-
# --------------------------------------
# Author:Liu Shuai
# Date:2016-05-16
# Desc:Ansible远程执行命令脚本
# --------------------------------------

from play_common import *

class ExecCmd(object):
    def __init__(self):
        self.dict_value=get_json()
        self.comm=GetParamValue('adp', 'adp', '10.161.24.215:1621/ACT61')
        self.username_password_dict = self.comm.get__host_username_password(self.dict_value)
        self.dispatch_dict = self.comm.get_dispatch(self.dict_value)

    def playbooks(hosts, username, cmd):
        play_source = dict(
            name="AutoBackup",
            hosts=hosts,
            gather_facts='no',
            remote_user=username,
            tasks=[
                dict(action=dict(module='shell', args=cmd), register='shell_out'),
            ]
        )
        return play_source

    def run(self):
        print 'Command is :'+self.dispatch_dict
        for item in self.dispatch_dict:
            print 'Command is :' + item['CMD']
            for username_password_list, hosts_list in self.username_password_dict.items():
                print ("Hosts list:%s" % hosts_list)
                print ("Host's username:%s\nHost's password:%s" % (username_password_list[0], username_password_list[1]))
                self.comm.run(hosts_list, username_password_list[0], username_password_list[1],
                             self.playbooks(hosts_list, username_password_list[0], item['CMD']))

        print("[ADP_RESULT]%s" % self.comm.get_res_stats_json(self.dict_value))

if __name__ == "__main__":
    ab=ExecCmd()
    ab.run()