import socket
import os
import threading

'''
 Classe Peer: Atua como distribuídora dos arquivos e realiza downloads 
 de arquivos baseados nas requisições do usuário.
'''


class Peer:
    def __init__(self, servidor_ip, servidor_port):
        self.server_socket = None
        self.server_ip = servidor_ip
        self.server_port = servidor_port
        self.peer_ip = socket.gethostbyname(socket.gethostname())
        self.peer_port = None
        self.folder = None
        self.files = []

    ''' 
       Função utilizada como inicializador do peer, ou seja, permite sua 
       conexão com o servidor baseado nas informações obtidas pelo cliente, 
       com uma thread para também lidar com a conexão do peer.
    '''

    def start(self):

        self.peer_port = int(input("Digite a porta deste peer: "))
        self.folder = input("Digite o local onde está a pasta de arquivos:")
        self.files = os.listdir(self.folder)

        # Tratamento para pasta de arquivos vazios
        if not self.files:
            self.files = ["[]"]

        # Cria uma thread para lidar com a conexão do peer
        threading.Thread(target=self.run).start()

    '''
    Faz o direcionamento para os métodos adequados de acordo com a requisição do usuário.
    '''

    def run(self):
        while True:
            self.print_menu()
            option = input("Digite a opção desejada: ")
            if option == "1":
                self.join()
                self.enable_peer_server()
            elif option == "2":
                self.search_file()
            elif option == "3":
                self.download_file_request()
            elif option == "4":
                break
            else:
                print("Opção inválida. Tente novamente.")

    '''
     Efetua requisição JOIN ao servidor e caso receba JOIN_OK permite
     a atuação do Peer como um servidor de compartilhamento de arquivos.
    '''

    def join(self):
        try:
            # Conecta ao servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.server_ip, self.server_port))

                # Envia requisição JOIN ao servidor
                join_message = f"JOIN {self.peer_ip}:{self.peer_port} {','.join(self.files)}"
                s.sendall(join_message.encode())

                # Recebe resposta do servidor
                response = s.recv(1024).decode()

                if response == "JOIN_OK":
                    print(f"Sou peer {self.peer_ip}:{self.peer_port} com arquivos {', '.join(self.files)}")
                else:
                    print("Falha ao entrar na rede.")

        except ConnectionRefusedError:
            print("Não foi possível conectar ao servidor.")

    '''
    Orquestra a requisição SEARCH com o servidor, criando um socket TCP para o envio 
    da mensagem e posteriormente esperando pela resposta do servidor 
    pelo conjunto de Peers com o arquivo.
    '''

    def search_file(self):
        try:
            filename = input("Digite o nome do arquivo a ser pesquisado: ")

            # Conecta ao servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.server_ip, self.server_port))

                # Envia requisição SEARCH ao servidor
                search_message = f"SEARCH {self.peer_ip}:{self.peer_port},{filename}"
                s.sendall(search_message.encode())

                # Recebe resposta do servidor
                response = s.recv(1024).decode()

                if response != "[]":
                    peers = response.split(',')
                    print(f"Peers com o arquivo solicitado ({filename}):")
                    for p in peers:
                        print(p)
                else:
                    print("Arquivo não encontrado.")

        except ConnectionRefusedError:
            print("Não foi possível conectar ao servidor.")

    '''
    Função utilizada para criação de thread com o objetivo de, paralelamente, habilitar o 
    Peer como um servidor e aceitar requisições de download, ao mesmo momento em que pode 
    se conectar com o servidor e fazer suas devidas requisições.
    '''
    def enable_peer_server(self):
        # Cria um socket de servidor para aceitar a conexão
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.peer_ip, self.peer_port))
        self.server_socket.listen()

        def handle_requests():
            while True:
                conn, addr = self.server_socket.accept()
                request = conn.recv(1024).decode()

                if request.startswith("DOWNLOAD"):
                    self.handle_download_request(conn, request)
                    conn.close()
                else:
                    pass

        # Cria uma thread para lidar com as requisições
        request_thread = threading.Thread(target=handle_requests)
        request_thread.daemon = True
        request_thread.start()

    '''
    Orquestra o DOWNLOAD do arquivo, cria uma conecão TCP com o peer alvo, 
    enviando uma requisição de download e recebendo o arquivo em sua pasta 
    como resposta. Se feito com sucesso, chama a função de update para atualização
    da lista.
    '''

    def download_file_request(self):

        peer_ip = input("Digite o IP do peer que possui o arquivo: ")
        peer_port = int(input("Digite a porta do peer que possui o arquivo: "))
        filename = input("Digite o nome do arquivo a ser baixado: ")

        try:
            # Conecta ao servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port))

                s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16384)

                # Envia requisição DOWNLOAD ao peer
                download_message = f"DOWNLOAD {filename}"
                s.sendall(download_message.encode())

                file_path = os.path.join(self.folder, filename)

                # Receber o arquivo do peer
                with open(file_path, "wb") as file:
                    data = s.recv(1024)
                    while data:
                        file.write(data)
                        data = s.recv(1024)

                print(f"Arquivo {filename} baixado com sucesso na pasta {self.folder}.")

                self.update_file(filename)

        except ConnectionRefusedError:
            print("Não foi possível conectar ao peer.")

    '''
    Orquestra a requisição de UPDATE, se conecta com o servidor, enviando o 
    nome do arquivo novo adquirido e recebe uma mensagem de UPTADE_OK caso 
    tenha sido atualizado com sucesso.
    '''

    def update_file(self, filename):
        try:
            # Conecta ao servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.server_ip, self.server_port))

                # Envia requisição UPDATE ao servidor
                update_message = f"UPDATE {self.peer_ip}:{self.peer_port},{filename}"
                s.sendall(update_message.encode())

                # Recebe resposta do servidor
                response = s.recv(1024).decode()

                if response != "UPDATE_OK":
                    print("Falha ao inserir arquivo na lista de arquivos")

        except ConnectionRefusedError:
            print("Não possível conectar ao servidor.")

    '''
    Função de lida com a requisição de DOWNLOAD recebida por outro peer.
    É responsável por ler o arquivo existente em sua pasta e enviá-lo 
    para o peer solicitante.
    '''
    def handle_download_request(self, conn, request):
        try:
            filename = request.split()[1]

            if self.peer_ip and self.peer_port:

                folder_path = os.path.join(self.folder, filename)

                # Enviar o arquivo ao peer
                with open(folder_path, "rb") as file:
                    data = file.read(1024)
                    while data:
                        conn.sendall(data)
                        data = file.read(1024)

        except IndexError:
            print(f"Peer enviou uma mensagem DOWNLOAD inválida.")

    @staticmethod
    def print_menu():
        print("\nMenu Interativo:")
        print("1. JOIN")
        print("2. SEARCH")
        print("3. DOWNLOAD")
        print("4. Sair")


if __name__ == "__main__":
    server_ip = input("Digite o IP do servidor: ")
    server_port = int(input("Digite a porta do servidor: "))

    peer = Peer(server_ip, server_port)
    peer.start()
