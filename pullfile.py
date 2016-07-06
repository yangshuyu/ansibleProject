#!/usr/bin/env python
# coding=GB18030

from play_common import *
import time
import subprocess


def main():
    dict_value = get_json()
    copy_run = GetParamValue('adp', 'adp', '10.161.24.215:1621/ACT61')
    username_password_dict = copy_run.get__host_username_password(dict_value)
    dispatch_dict = copy_run.get_dispatch(dict_value)

    # create play with tasks

    def playbooks(hosts, username, src, dest):
        # src = '/cbss/credit/shell'
        # dest = '/ngbss/adp/huyh/'
        # print (hosts)
        # print (type(username))
        # hostnum = hosts[0].split('.')[-1]
        # print (hostnum)
        # date = time.strftime("%Y%m%d", time.localtime())
        # dest = dest + date + '/' + username + hostnum + '/'
        # print (dest)
        # subprocess.call('mkdir ' + dest, shell=True)
        play_source = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='no',
            remote_user=username,
            tasks=[
                dict(action=dict(module='file',
                                 args=dict(state='directory', path='~/.ssh/', mode='755', owner=username))),
                dict(action=dict(module='copy',
                                 args=dict(src='~/.ssh/authorized_keys', dest='~/.ssh/authorized_keys', owner=username,
                                           mode='755', force='yes'))),
                dict(action=dict(module='synchronize',
                                 args=dict(mode='pull', src=src, dest=dest)))
            ]
        )

        return play_source

    for item in dispatch_dict:
        print ("File src path:%s" % item['SRC'])
        print ("File dest path:%s" % item['DEST'])
        for username_password_list, hosts_list in username_password_dict.items():
            print ("Hosts list:%s" % hosts_list)
            print ("Host's username:%s\nHost's password:%s" % (username_password_list[0], username_password_list[1]))
            targets = ['shell', 'etc']
            for target in targets:
                for host in hosts_list:
                    src = '/cbss/' + username_password_list[0] + '/' + target
                    dest = '/ngbss/adp/file_backup/'
                    # print (host)
                    # print (type(username_password_list[0]))
                    hostnum = host.split('.')[-1]
                    # print (hostnum)
                    date = time.strftime("%Y%m%d", time.localtime())
                    dest = dest + date + '/' + username_password_list[0] + hostnum + '/'
                    # print (dest)
                    subprocess.call('mkdir -p ' + dest, shell=True)
                    item['SRC'] = src
                    item['DEST'] = dest
                    host_list = []
                    host_list.append(host)
                    copy_run.run(host_list, username_password_list[0], username_password_list[1],
                                 playbooks(host_list, username_password_list[0], item['SRC'], item['DEST']))

    # res_stats_dict = CallbackModule().get_res_stats()
    # res_stats_dict['batch_id'] = dict_value['batch_id']
    # res_stats_json = json.dumps(res_stats_dict)

    print("[ADP_RESULT]%s" % copy_run.get_res_stats_json(dict_value))


main()
