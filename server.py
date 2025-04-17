import grpc
from concurrent import futures
import time
import random
import datetime
import threading
import csv

import control_notifications_pb2
import control_notifications_pb2_grpc

def load_region_database(csv_filename):
    """Carrega as informações do CSV e retorna um dicionário com os dados das regiões."""
    region_db = {}
    try:
        with open(csv_filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                region = row['location'].strip()
                info = row['info'].strip()
                region_db[region] = info
    except Exception as e:
        print("Erro ao ler o CSV:", e)
    return region_db

class ControlNotifierServicer(control_notifications_pb2_grpc.ControlNotifierServicer):
    def NotificationStream(self, request_iterator, context):
        # Estado do cliente: região atual (padrão "Centro")
        current_location = ["Centro"]

        # Flags para controle de comandos do cliente
        disconnect_flag = threading.Event()
        update_now_flag = threading.Event()
        list_locations_flag = threading.Event()

        # Variável para armazenar a base de dados dos locais, que será recarregada periodicamente
        region_database = load_region_database("locations.csv")
        csv_reload_interval = 20  # Intervalo de recarga do CSV (em segundos)
        last_reload_time = time.time()

        # Thread para ler comandos vindos do cliente
        def read_client():
            try:
                for msg in request_iterator:
                    print(f"Recebido do cliente: role={msg.role}, command={msg.command}, message={msg.message}")
                    if msg.role == "client":
                        if msg.command == "disconnect":
                            disconnect_flag.set()
                            break
                        elif msg.command == "change_location":
                            # Atualiza a região se existir na base de dados atual
                            if msg.message in region_database:
                                current_location[0] = msg.message
                                print("Região atualizada para:", current_location[0])
                            else:
                                print("Região desconhecida:", msg.message)
                        elif msg.command == "update_now":
                            update_now_flag.set()
                        elif msg.command == "list_locations":
                            list_locations_flag.set()
            except Exception as e:
                print("Erro ao ler mensagens do cliente:", e)
                disconnect_flag.set()

        # Inicia thread para processar mensagens do cliente
        reader_thread = threading.Thread(target=read_client, daemon=True)
        reader_thread.start()

        # Loop principal de envio de notificações
        while not disconnect_flag.is_set():
            current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_time = time.time()

            # Verifica se é hora de recarregar o CSV
            if time.time() - last_reload_time >= csv_reload_interval:
                region_database = load_region_database("locations.csv")
                last_reload_time = time.time()
                print("Base de dados recarregada.")

            # Se o cliente solicitou listar as regiões disponíveis
            if list_locations_flag.is_set():
                locations_list = ", ".join(region_database.keys())
                list_msg = control_notifications_pb2.Notification(
                    role="server",
                    type="control",
                    command="list_locations",
                    message=f"Regiões disponíveis: {locations_list}",
                    timestamp=current_time_str,
                    send_timestamp=send_time
                )
                yield list_msg
                list_locations_flag.clear()
            else:
                # Envia a notificação com os dados da região atual
                region_info = region_database.get(current_location[0], "Dados indisponíveis para a região.")
                notification = control_notifications_pb2.Notification(
                    role="server",
                    type="notification",
                    command="",
                    message=region_info,
                    timestamp=current_time_str,
                    send_timestamp=send_time
                )
                yield notification

            # Se o cliente solicitou um update_now, envia a atualização imediatamente
            if update_now_flag.is_set():
                current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                send_time = time.time()
                region_info = region_database.get(current_location[0], "Dados indisponíveis para a região.")
                immediate_notification = control_notifications_pb2.Notification(
                    role="server",
                    type="notification",
                    command="update_now",
                    message=region_info,
                    timestamp=current_time_str,
                    send_timestamp=send_time
                )
                yield immediate_notification
                update_now_flag.clear()

            time.sleep(5)

        # Envia mensagem final de desconexão
        final_msg = control_notifications_pb2.Notification(
            role="server",
            type="control",
            command="disconnect",
            message="Conexão encerrada pelo servidor.",
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            send_timestamp=time.time()
        )
        yield final_msg

def serve():
    # Configurações do servidor (definidas na função serve)
    host = '[::]'
    port = '50054'
    max_workers = 10

    # Cria o servidor gRPC com ThreadPoolExecutor
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    control_notifications_pb2_grpc.add_ControlNotifierServicer_to_server(ControlNotifierServicer(), server)
    server_address = f"{host}:{port}"
    server.add_insecure_port(server_address)
    server.start()
    print(f"Servidor rodando em {server_address}...")

    try:
        # Mantém o servidor ativo
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("Encerrando o servidor...")
        server.stop(0)

if __name__ == '__main__':
    serve()
