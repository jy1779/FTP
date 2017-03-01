import socketserver,hashlib
import json,os
class MyTCPHandler(socketserver.BaseRequestHandler):
    def put(self,*args):
        '''上传客户端的文件'''
        put_log = open('/root/ftp_server/log/put.log','a+')
        data_path = '/root/ftp_server/data/'
        cmd_dic = args[0]
        filename = cmd_dic["filename"]
        filesize = cmd_dic["size"]
        m = hashlib.md5()
        if os.path.isfile(data_path + filename):
            f = open(data_path + filename + ".new","wb")
        else:
            f = open(data_path + filename , "wb")
        self.request.send(b"200 OK")
        received_size = 0
        while received_size < filesize:
            data = self.request.recv(1024)
            m.update(data)
            f.write(data)
            received_size += len(data)
        else:
            new_file_md5 = m.hexdigest()
            put_log.write("file [%s] has uploads..."% filename + '\n')
            f.close()
            self.request.send('SYN'.encode('utf-8'))
            client_file_md5 = self.request.recv(1024)
            client_md5 = "server file md5:" + client_file_md5.decode() + '\n'
            new_md5 = "client file md5:" + new_file_md5 + '\n'
            put_log.write(client_md5)
            put_log.write(new_md5)
            put_log.close()
    def get(self,*args):
        '''下载服务端文件'''
        get_log = open('/root/ftp_server/log/get.log','a+')
        data_path = '/root/ftp_server/data/'
        cmd_dic = args[0]
        filename = cmd_dic['filename']
        if os.path.isfile(data_path + filename):
            f = open(data_path + filename, 'rb')
            m = hashlib.md5()
            file_size = os.stat(data_path + filename).st_size
            self.request.send(str(file_size).encode('utf-8'))
            ack1 = self.request.recv(1024)
            for line in f:
                m.update(line)
                self.request.send(line)
            file_md5 = 'file md5:'+ m.hexdigest()+'\n'
            get_log.write(file_md5)
            get_log.close()              
            f.close()
            ack2 = self.request.recv(1024)
            self.request.send(m.hexdigest().encode())
    def ls(self,*args):
        os.chdir("/root/ftp_server/data/")
        cmd_dic = args[0]
        path = cmd_dic["path"]
        dir_dic = {}
        root_result_path = os.listdir(os.getcwd())
        def send(*args):
            cmd_result = ''.join(args)
            self.request.send(str(len(cmd_result.encode('utf-8'))).encode('utf-8'))
            ack=self.request.recv(1024)
            self.request.send(str(cmd_result).encode('utf-8'))
        if path == 'None' or path == '.' or path == '/':
            cmd_path = os.listdir(".")
            send(' '.join(cmd_path))
        else:
            for i in root_result_path[:]:
                dir_dic[i]=i
            if path in dir_dic:
                if os.path.isdir(path):
                    cmd_result = os.listdir(path)
                    send(' '.join(cmd_result))
                else:
                    send('It is not a directory')
            else:
                send('It is not a directory')
    def cd(self,*args):
        os.chdir("/root/ftp_server/data/")
        dir_dic = {}
        cmd_dic = args[0]
        path = cmd_dic["path"]
        root_result_path = os.listdir(".")
        for i in root_result_path[:]:
            dir_dic[i] = i
        if path in dir_dic:
            if os.path.isdir(path):
                os.chdir(path)
                self.request.send(os.getcwd().encode('utf-8'))
            else:
                self.request.send('It is not a directory'.encode('utf-8'))
        else:
            self.request.send('It is not a directory'.encode('utf-8'))
    def handle(self):
        acc_log = open('/root/ftp_server/log/access.log','a+')
        while True:
            try:
                self.data = self.request.recv(1024).strip()
                address = "addres:{}".format(self.client_address[0]) + '\n'
                client_data = self.data.decode() + '\n'
                acc_log.write(address)
                acc_log.flush()
                acc_log.write(client_data)
                acc_log.flush()
                cmd_dic = json.loads(self.data.decode())
                action = cmd_dic["action"]
                if hasattr(self,action):
                    func = getattr(self,action)
                    func(cmd_dic)
            except ConnectionResetError as e:
                err = str(e) + '\n'
                acc_log.write(err)
                acc_log.flush()
                acc_log.close()
                break
def authentication():
    f = open('/root/ftp_server/conf/user', 'r')
    user_dic = {}
    password_dic = {}
    for i in f:
        name, passwd = i.strip('\n').split(':')
        user_dic[passwd] = name
        password_dic[name] = passwd
    while True:
        user = input('User:')
        password = input('Password:')
        if user == user_dic.get(password) and password == password_dic.get(user):
            print('Welcome to Jonny FTP')
            break
        else:
            print('The user does not exist or the account password is incorrect')
            continue


if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 888
    server = socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
