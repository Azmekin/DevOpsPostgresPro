import paramiko
import psycopg2


class SSHConnection():
    """
    This class created for contain information about host, user, password (secret), port. For stable work use AstraLinux
     Common Edition and RedOS 8.0. You must allow PermitRootLogin for work. If you want to enter only host, you should
     allow PermitEmptyPassword in ssh config. It uses only root setup, because there is unstable work in writing in
     daemon config file by 'sudo tee' or 'bash -c'. It's not working one of twice repeat on clear snapshot of virtual
     machine.
    """
    
    host = ''
    user = 'root'
    secret = ''
    port = 22
    path='/root/'
    client = paramiko.SSHClient()
    
    def connection_sql(self):
        """This function need for testing connection to Postgresql. It can make connect and get version of Postgresql"""
        try:
            conn = psycopg2.connect("dbname='postgres' user='postgres' host='"+self.host+"'")
            with conn.cursor() as curs:

                print("=========TEST OF CONNECT TO POSTGRESQL=========")
                # simple single row system query
                curs.execute("SELECT version()")

                # returns a single row as a tuple
                single_row = curs.fetchone()

                # use an f-string to print the single tuple returned
                print(f"{single_row}")

                # simple multi row system query
                curs.execute("SELECT 1")

                # a default install should include this query and some backend workers
                many_rows = curs.fetchone()

                # use the * unpack operator to print many_rows which is a Python list
                print(*many_rows, sep="\n")

            # a more robust way of handling errors
        except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                exit(-1)
            
    def get_con_param(self):
        """This function take information by user"""
        host = input("Enter ip4 address or DNS name: ")
        while len(host) == 0:
            host = input("Hostname can't be empty. Enter ip4 address or DNS name: ")
        self.host=host
        print("User for connection: root")
        #Uncomment on solved problem of write in deamon config file.
        #user = input("Enter username. Default - root. Set blank for choose default: ")
        #if len(user) != 0:
        #    self.user = user
        secret = input("Enter password. Default - none. Set blank for choose default: ")
        if len(secret) != 0:
            self.secret = secret
        port = input("Enter port. Default - 22. Set blank for choose default: ")
        if len(port) != 0:
            while not isinstance(port, int):
                try:
                    port = int(port)
                except ValueError:
                    port = input("Port must be integer. Enter port: ")
            self.port = int(port)
            
    def get_connection(self):
        """This function try to connect to the host and make test command"""
        print("=========TEST HOST CONNECTION=========")
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
        except Exception as e:
            print("Failed on connection", e)
            self.client.close()
            exit(-1)
        try:
            if self.user!="root":
                self.path="/home/"+self.user+"/"
            stdin, stdout, stderr = self.client.exec_command('whoami')
            data = stdout.read() + stderr.read()
            print(data)
        except Exception as e:
            print("Failed on test execute of command. User don't have permissions", e)
            self.client.close()
            exit(-1)
        self.client.close()
        
    def redos_connection(self):
        """This function used for setup Postgresql on RedOS"""

        self.client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
        print("=========INSTALL WGET=========")
        stdin, stdout, stderr = self.client.exec_command('sudo dnf install wget -y')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========INSTALL SOURCE OF POSTGRESQL=========")
        stdin, stdout, stderr = self.client.exec_command('sudo wget https://ftp.postgresql.org/pub/source/v16.2/postgresql-16.2.tar.gz')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========UNPACKING=========")
        stdin, stdout, stderr = self.client.exec_command('tar -xvf postgresql-16.2.tar.gz')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========INSTALL DEVELOPMENT TOOLS=========")
        stdin, stdout, stderr = self.client.exec_command('sudo yum groupinstall "Development Tools" -y')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========START OF CONFIGURATION=========")
        stdin, stdout, stderr = self.client.exec_command('postgresql-16.2/configure --without-icu --without-readline')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========BUILDING POSTGRESQL=========")
        stdin, stdout, stderr = self.client.exec_command('sudo make install postgresql-16.2/')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========ADD USER POSTGRES=========")
        stdin, stdout, stderr = self.client.exec_command('sudo adduser postgres')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CREATE OF DATA DIRECTORY=========")
        stdin, stdout, stderr = self.client.exec_command('sudo mkdir -p /usr/local/pgsql/data')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CHANGE OWNER OF DIRECTORY=========")
        stdin, stdout, stderr = self.client.exec_command('chown postgres -R /usr/local/pgsql/data')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CREATE .SERVICE FILE=========")
        #This need for cover rm -rf function exeption in the next
        stdin, stdout, stderr = self.client.exec_command(
            'touch /etc/systemd/system/postgres.service')
        print("=========INIT DB=========")
        stdin, stdout, stderr = self.client.exec_command('sudo -u postgres /usr/local/pgsql/bin/initdb -D /usr/local/pgsql/data')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========POSTGRESQL.CONF AND PG_NBA.CONF SETUP=========")
        stdin, stdout, stderr = self.client.exec_command(
            'sudo echo "listen_addresses = \'*\'">> /usr/local/pgsql/data/postgresql.conf')
        stdin, stdout, stderr = self.client.exec_command(
            'sudo echo "host    all     all     0.0.0.0/0      trust">> /usr/local/pgsql/data/pg_hba.conf')
        print("=========TRY OF DELETE OLD VERSION OF POSTGRES.SERVICE FROM ANOTHER SETUP=========")
        #This need to be done. In case you already have\setup postgresql, .service can be broken
        stdin,stdout,stderr=self.client.exec_command("rm -f /etc/systemd/system/postgres.service")
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CREATE POSTGRESQL.SERVICE=========")
        stdin, stdout, stderr = self.client.exec_command(
            'echo "[Unit]\nDescription=postgres\nAfter=gdm.service\nAfter=gdm.service\n[Service]\nExecStart=/usr/local/pgsql/bin/pg_ctl -D /usr/local/pgsql/data start\nType=oneshot\nUser=postgres\nRemainAfterExit=yes\n[Install]\nWantedBy=multi-user.target">> /etc/systemd/system/postgres.service')
        stdin, stdout, stderr = self.client.exec_command('systemctl daemon-reload')
        stdin, stdout, stderr = self.client.exec_command('systemctl enable postgres.service')
        print("=========START POSTGRESQL.SERVICE=========")
        stdin, stdout, stderr = self.client.exec_command('systemctl start postgres.service')
        self.connection_sql()
        #IF you need to test autostart of deamon, you should uncomment this line:
        #stdin, stdout, stderr = self.client.exec_command("reboot")
        self.client.close()
        
    def astra_connection(self):
        self.client.connect(hostname=self.host, username=self.user, password=self.secret, port=self.port)
        print("=========INSTALL WGET=========")
        stdin, stdout, stderr = self.client.exec_command('sudo apt install wget -y')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========INSTALL SOURCE OF POSTGRESQL=========")
        stdin, stdout, stderr = self.client.exec_command('sudo wget https://ftp.postgresql.org/pub/source/v16.2/postgresql-16.2.tar.gz')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========UNPACKING=========")
        stdin, stdout, stderr = self.client.exec_command('sudo tar -xvf postgresql-16.2.tar.gz')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========INSTALL DEVELOPMENT TOOLS=========")
        stdin, stdout, stderr = self.client.exec_command('sudo apt-get install build-essential gcc -y')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CHECK OF SUCCESSFUL UNPACKING=========")
        stdin, stdout, stderr = self.client.exec_command('ls')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========START OF CONFIGURATION=========")
        stdin, stdout, stderr = self.client.exec_command('sudo ./postgresql-16.2/configure --without-icu --without-readline --without-zlib')
        data = stdout.read() + stderr.read()
        print(data)
        stdin, stdout, stderr = self.client.exec_command('cd ./postgresql-16.2/')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========BUILDING POSTGRESQL=========")
        stdin, stdout, stderr = self.client.exec_command('sudo make install')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========ADD USER POSTGRES=========")
        #It's must to be useradd, not adduser
        stdin, stdout, stderr = self.client.exec_command('sudo useradd postgres')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CREATE OF DATA DIRECTORY AND CHANGE OWNER=========")
        stdin, stdout, stderr = self.client.exec_command('sudo mkdir -p /usr/local/pgsql/data')
        stdin, stdout, stderr = self.client.exec_command('sudo chown postgres -R /usr/local/pgsql/data')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CREATE .SERVICE FILE=========")
        #This need for cover rm -rf function exeption in the next
        stdin, stdout, stderr = self.client.exec_command(
            'sudo touch /etc/systemd/system/postgres.service')
        print("=========INIT DB=========")
        stdin, stdout, stderr = self.client.exec_command('sudo -u postgres /usr/local/pgsql/bin/initdb -D /usr/local/pgsql/data')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========POSTGRESQL.CONF AND PG_NBA.CONF SETUP=========")
        stdin, stdout, stderr = self.client.exec_command('sudo echo "listen_addresses = \'*\'">> /usr/local/pgsql/data/postgresql.conf')
        stdin, stdout, stderr = self.client.exec_command('sudo echo "host    all     all     0.0.0.0/0      trust">> /usr/local/pgsql/data/pg_hba.conf')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========TRY OF DELETE OLD VERSION OF POSTGRES.SERVICE FROM ANOTHER SETUP=========")
        #This need to be done. In case you already have\setup postgresql, .service can be broken
        stdin,stdout,stderr=self.client.exec_command("rm -f /etc/systemd/system/postgres.service")
        data = stdout.read() + stderr.read()
        print(data)
        print("=========CREATE POSTGRESQL.SERVICE=========")
        stdin, stdout, stderr = self.client.exec_command(
            'echo "[Unit]\nDescription=postgres\nAfter=gdm.service\nAfter=gdm.service\n[Service]\nExecStart=/usr/local/pgsql/bin/pg_ctl -D /usr/local/pgsql/data start\nType=oneshot\nUser=postgres\nRemainAfterExit=yes\n[Install]\nWantedBy=multi-user.target"| sudo tee -a /etc/systemd/system/postgres.service')
        stdin, stdout, stderr = self.client.exec_command('sudo systemctl daemon-reload')
        data = stdout.read() + stderr.read()
        print(data)
        stdin, stdout, stderr = self.client.exec_command('sudo systemctl enable postgres.service')
        data = stdout.read() + stderr.read()
        print(data)
        print("=========START POSTGRESQL.SERVICE=========")
        stdin, stdout, stderr = self.client.exec_command('sudo systemctl start postgres.service')
        data = stdout.read() + stderr.read()
        print(data)
        self.connection_sql()
        #IF you need to test autostart of deamon, you should uncomment this line:
        #stdin, stdout, stderr = self.client.exec_command("sudo reboot")
        self.client.close()

SSHCon = SSHConnection()
