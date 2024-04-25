# This is a sample Python script.
from connection_param import   SSHCon
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and set


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    SSHCon.get_con_param()
    print(SSHCon.host,SSHCon.user,SSHCon.secret,SSHCon.port)
    SSHCon.get_connection()
    os_type=input("Leave blank for RedOS Setup, type something for AstraLinux setup: ")
    try:
        if len(os_type)!=0:
            SSHCon.astra_connection()
        else:
            SSHCon.redos_connection()
    except Exception as e:
        print("Error on ssh session on setup: ", e)


