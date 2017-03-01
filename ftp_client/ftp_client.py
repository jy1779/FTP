import socket,hashlib,os,json
from oldboy.day8.ftp_server.core import main
class FtpClient(object):
    def __init__(self):
        self.client = socket.socket()
    def help(self):
        '''命令帮助信息'''
        msg='''
        ls
        pwd
        cd ../..
        get filename
        put filename
        '''
        print(msg)
    def connect(self,ip,port):
        '''连接服务器'''
        self.client.connect((ip,port))
    def interactive(self):
        '''命令交互'''
        main.authentication()
        while True:
            cmd = input(">>>").strip()
            if len(cmd) == 0 : continue
            cmd_str = cmd.split() [0] #取命令第一个值，第一值永远是命令
            if hasattr(self,"cmd_%s" % cmd_str):  #如果方法存在
                func = getattr(self,"cmd_%s" % cmd_str) #获取方法赋值func
                func(cmd) #用户输入的指令传进去。
            else:
                self.help()
    def cmd_put(self,*args):  #为了以后可能传入多个参数，所以用*args
        cmd_split = args[0].split() #取第一个命令
        if len(cmd_split) > 1:      #判断命令存在
            filename = cmd_split[1] #第二个值赋值给filename
            if os.path.isfile(filename):  #判断是否为文件
                filesize = os.stat(filename).st_size  #文件大小
                put_mgs_dic = {    #准备信息发送给服务器
                    "action":"put",
                    "filename":filename,
                    "size":filesize,
                    "overridden":True  #打比方，如果有重名就覆盖
                }
                self.client.send(json.dumps(put_mgs_dic).encode('utf-8'))  #socket只能传bytes,把mgs_dic转成json格式转成utf-8
                #防止粘包，等服务器确认
                server_response = self.client.recv(1024)
                f = open(filename,'rb')  #打开文件
                m = hashlib.md5()
                for line in f:
                    m.update(line)
                    self.client.send(line)  #循环发送文件

                else:
                    print('file upload success...')
                    f.close()
                print('file md5:', m.hexdigest())
                ack = self.client.recv(1024)
                self.client.send(m.hexdigest().encode())
            else:
                print(filename,'is not exist')
    def cmd_get(self,*args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            get_mgs_dic = {  # 准备信息发送给服务器
                "action": "get",
                "filename": filename
            }
            self.client.send(json.dumps(get_mgs_dic).encode('utf-8'))
            server_file_size = self.client.recv(1024)
            file_total_size = int(server_file_size.decode())
            self.client.send("SYN1".encode("utf-8"))
            received_size = 0
            f = open(filename, 'wb')
            m = hashlib.md5()
            while received_size < file_total_size:
                data = self.client.recv(1024)
                received_size += len(data)
                m.update(data)
                f.write(data)
            else:
                new_file_md5 = m.hexdigest()
                print('file recv done', received_size, file_total_size)
                f.close()
                self.client.send("SYN2".encode("utf-8"))
                server_file_md5 = self.client.recv(1024)
                print("server file md5:", server_file_md5)
                print("client file md5:", new_file_md5)
    def cmd_ls(self,*args):
        cmd_split = args[0].split()
        if len(cmd_split) >1:
            action = cmd_split[0]
            path = cmd_split[1]
        else:
            action = cmd_split[0]
            path = 'None'
        int_cmd_mgs_dic = {
            "action":action,
            "path":path
        }
        self.client.send(json.dumps(int_cmd_mgs_dic).encode('utf-8'))
        new_cmd_size = 0
        new_cmd_data = b''
        cmd_size = self.client.recv(1024)
        self.client.send('SYN'.encode('utf-8'))
        while new_cmd_size < int(cmd_size.decode()):
            data = self.client.recv(1024)
            new_cmd_size += len(data)
            new_cmd_data += data
        else:
            print(new_cmd_data.decode())
    def cmd_cd(self,*args):
        cmd_split = args[0].split()
        if len(cmd_split) >1:
            action = cmd_split[0]
            path = cmd_split[1]
            int_cmd_mgs_dic = {
                "action": action,
                "path": path
            }
            self.client.send(json.dumps(int_cmd_mgs_dic).encode('utf-8'))
            dir_path = self.client.recv(1024)
            print(dir_path.decode())
        else:
            print('cd directory')


ftp = FtpClient()
ftp.connect("localhost",888)
ftp.interactive()