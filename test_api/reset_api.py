import paramiko
import time

"""
test for the retart of the gazebo simulation 
"""


def reset():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh.connect(
        hostname="192.168.0.148", port=22, username="sony", password="sony", timeout=10
    )
    invoke = ssh.invoke_shell()
    invoke.send("rosservice call /gazebo/reset_simulation \n")
    time.sleep(3)
    # stdin,stdout,stderr =ssh.exec_command("bash -lc 'echo $PATH' ")
    # # stdin,stdout,stderr =ssh.exec_command("echo $PATH")
    # # ssh.exec_command("bash --login -c 'ifconfig'", get_pty=True)
    # # stdin,stdout,stderr =ssh.exec_command("bash -lc 'rosservice call /gazebo/reset_simulation'", get_pty=True)
    # output= stdout.read().decode()
    # print(output)
    # print(stderr.read().decode())
    ssh.close()


reset()
