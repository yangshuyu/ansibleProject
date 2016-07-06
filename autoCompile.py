# -*- coding: GB18030 -*-
# --------------------------------------
# Author:Liu Shuai
# Date:2016-05-16
# Desc:Ansible自动编译脚本
# --------------------------------------
from play_common import *


def main():
    dict_value = get_json()
    copy_run = GetParamValue('adp', 'adp', '10.161.24.215:1621/ACT61')
    username_password_dict = copy_run.get__host_username_password(dict_value)
    dispatch_dict = copy_run.get_dispatch(dict_value)

    # create play with tasks

    def playbooks(hosts, username, src, cmd):
        #if(type==)
        play_source = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='no',
            remote_user=username,
            tasks=[
                dict(action=dict(module='shell', args=cmd), register='shell_out'),
            ]
        )

        return play_source

    for item in dispatch_dict:
        print ("File src path:%s" % item['SRC'])
        print ("File dest path:%s" % item['DEST'])
        for username_password_list, hosts_list in username_password_dict.items():
            print ("Hosts list:%s" % hosts_list)
            print ("Host's username:%s\nHost's password:%s" % (username_password_list[0], username_password_list[1]))
            copy_run.run(hosts_list, username_password_list[0], username_password_list[1],
                         playbooks(hosts_list, username_password_list[0], item['SRC'], item['DEST']))

    print("[ADP_RESULT]%s" % copy_run.get_res_stats_json(dict_value))


main()
