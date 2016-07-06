# -*- coding: GB18030 -*-
# --------------------------------------
# Author:Liu Shuai
# Date:2016-05-16
# Desc:Ansible自动备份脚本
# --------------------------------------

from play_common import *

class AutoBackup(object):
    def __init__(self):
        self.dict_value=get_json()
        self.comm=GetParamValue('adp', 'adp', '10.161.24.215:1621/ACT61')
        self.username_password_dict = self.comm.get__host_username_password(self.dict_value)
        self.dispatch_dict = self.comm.get_dispatch(self.dict_value)

    def playbooks(hosts, username, src, dest):
        play_source = dict(
            name="AutoBackup",
            hosts=hosts,
            gather_facts='no',
            remote_user=username,
            tasks=[
                dict(action=dict(module='file',
                                 args=dict(state='directory', path=dest, mode='755', owner=username))),
                dict(action=dict(module='shell', args='cp -r '+src+' '+dest), register='shell_out'),
            ]
        )
        return play_source

    def run(self):
        for item in self.dispatch_dict:
            print ("File src path:%s" % item['SRC'])
            print ("File dest path:%s" % item['DEST'])
            for username_password_list, hosts_list in self.username_password_dict.items():
                print ("Hosts list:%s" % hosts_list)
                print ("Host's username:%s\nHost's password:%s" % (username_password_list[0], username_password_list[1]))
                self.comm.run(hosts_list, username_password_list[0], username_password_list[1],
                             self.playbooks(hosts_list, username_password_list[0], item['SRC'], item['DEST']))

        print("[ADP_RESULT]%s" % self.comm.get_res_stats_json(self.dict_value))

if __name__ == "__main__":
    ab=AutoBackup()
    ab.run()