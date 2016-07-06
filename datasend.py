# coding=GB18030
from play_common import *


def main():
    dict_value = get_json()
    copy_run = GetParamValue('adp', 'adp', '10.161.24.215:1621/ACT61')
    username_password_dict = copy_run.get__host_username_password(dict_value)
    dispatch_dict = copy_run.get_dispatch(dict_value)

    # create play with tasks

    def playbooks(hosts, username, src, dest):
        play_source = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='no',
            remote_user=username,
            tasks=[
                dict(action=dict(module='file',
                                 args=dict(state='directory', path=dest, mode='755', owner=username))),
                dict(action=dict(module='copy', args=dict(src=src, dest=dest, force='yes', validate='yes')))
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

    # res_stats_dict = CallbackModule().get_res_stats()
    # res_stats_dict['batch_id'] = dict_value['batch_id']
    # res_stats_json = json.dumps(res_stats_dict)

    print("[ADP_RESULT]%s" % copy_run.get_res_stats_json(dict_value))


main()
