import socket
import threading


'''
 Classe Servidor: Responsável por coordenar o 
 compartilhamento de arquivos entre Peers.
'''


class Servidor:
    def __init__(self, server_ip, server_port):
        self.ip = server_ip
        self.port = server_port
        self.peers = {}

    ''' 
    Função utilizada como inicializador e listener do servidor, ou seja, em estado block aguardando o 
    recebimento de mensagens via TCP. Assim a cada mensagem recebida inicializa-se uma thread que 
    será responsável por lidar com a conexão do peer, possibilitando assim que o servidor lide 
    com várias requisições de forma simultânea.
    '''
    def start(self):
        # Inicia o servidor
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.ip, self.port))
            s.listen()

            print(f"Servidor iniciado em {self.ip}:{self.port}.")

            while True:
                conn, addr = s.accept()

                # Criar uma thread para lidar com a conexão do peer
                threading.Thread(target=self.handle_peer, args=(conn, addr)).start()

    '''
    Trata a requisição do cliente, fazendo o redirecionamento aos métodos adequados.
    '''
    def handle_peer(self, conn, addr):
        with conn:
            while True:
                # Recebe a mensagem do peer
                data = conn.recv(1024).decode()

                if data.startswith("JOIN"):
                    self.handle_join(conn, data)
                elif data.startswith("SEARCH"):
                    self.handle_search(conn, data)
                elif data.startswith("UPDATE"):
                    self.handle_update(conn, data)

    '''
    Lida com requisições JOIN, adicionando aos mapas peer -> arquivos e arquivo -> peers.
    '''
    def handle_join(self, conn, data):
        try:
            # Extrai informações do peer da mensagem JOIN
            peer_info = data.split()[1].split(":")
            peer_ip = peer_info[0]
            peer_port = int(peer_info[1])
            files = data.split()[2].split(",")

            # Adiciona o peer à lista de peers
            self.peers[(peer_ip, peer_port)] = files

            # Envia resposta JOIN_OK ao peer
            response = "JOIN_OK"
            conn.sendall(response.encode())

            print(f"Peer {peer_ip}:{peer_port} adicionado")

        except IndexError:
            print(f"Peer enviou uma mensagem JOIN inválida.")

    '''
    Lida com requisições SEARCH, encontrando a lista de peers que possuem o arquivo e os envia para o cliente
    '''
    def handle_search(self, conn, data):
        try:
            #Extrai as informações do peer da mensagem SEARCH
            peer_info = data.split()[1].split(":")
            peer_ip = peer_info[0]
            peer_result = peer_info[1].split(",")
            peer_port = int(peer_result[0])
            filename = peer_result[1]

            # Procura o arquivo nos peers
            peers_with_file = []
            for peer, files in self.peers.items():
                if filename in files:
                    peers_with_file.append(peer)

            # Envia a lista de peers com o arquivo ao peer
            if not peers_with_file:
                response = "[]"
            else:
                response = ",".join([f"{peer[0]}:{peer[1]}" for peer in peers_with_file])

            conn.sendall(response.encode())

            print(f"Peer  {peer_ip}:{peer_port} solicitou arquivo {filename}.")

        except IndexError:
            print("Peer enviou uma mensagem SEARCH inválida.")

    '''
    Lida com requisições UPDATE, atualizando a lista de arquivos do peer que 
    acabou de realizar o download com sucesso, enviando o status de UPDATE_OK 
    após finalizado,tornando-se também um compartilhador do arquivo para outros peers.
    '''
    def handle_update(self, conn, data):
        try:
            # Extrai informações do peer da mensagem UPDATE
            peer_info = data.split()[1].split(":")
            peer_ip = peer_info[0]
            peer_result = peer_info[1].split(",")
            peer_port = int(peer_result[0])
            filename = peer_result[1]

            # Adiciona o peer à lista de peers
            self.peers[(peer_ip, peer_port)] = filename

            # Envia resposta JOIN_OK ao peer
            response = "UPDATE_OK"
            conn.sendall(response.encode())

            print(f"Arquivo {filename} adicionado ao peer {peer_ip}:{peer_port}")

        except IndexError:
            print(f"Peer enviou uma mensagem UPDATE inválida.")


if __name__ == "__main__":
    ip = input("Digite o IP do servidor: ")
    port = int(input("Digite a porta do servidor: "))

    servidor = Servidor(ip, port)
    servidor.start()
