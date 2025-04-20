import grpc
from concurrent import futures
import time
import datetime
import threading
import csv
import queue
import logging
from typing import Dict, Iterator

import control_notifications_pb2
import control_notifications_pb2_grpc

# Conjunto global de peers conectados
connected_peers = set()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

CSV_FILENAME = "locations.csv"
CSV_RELOAD_INTERVAL = 60

# Carrega a base de dados globalmente
region_database: Dict[str, str] = {}
last_reload_time = 0.0

def load_region_database(csv_filename: str) -> Dict[str, str]:
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
        logging.error(f"Erro ao ler o CSV: {e}")
    return region_db

def make_notification(role: str, type_: str, command: str, message: str, timestamp: str, send_timestamp: int):
    return control_notifications_pb2.Notification(
        role=role,
        type=type_,
        command=command,
        message=message,
        timestamp=timestamp,
        send_timestamp=send_timestamp
    )

def reload_csv_if_needed():
    global region_database, last_reload_time
    now = time.time()
    if now - last_reload_time >= CSV_RELOAD_INTERVAL:
        region_database = load_region_database(CSV_FILENAME)
        last_reload_time = now
        logging.info("Base de dados recarregada.")

class ControlNotifierServicer(control_notifications_pb2_grpc.ControlNotifierServicer):
    def NotificationStream(self, request_iterator, context) -> Iterator[control_notifications_pb2.Notification]:
        # Identifica e registra o peer do cliente
        peer = context.peer()
        connected_peers.add(peer)
        logging.info(f"Cliente conectado: {peer}")
        current_location = "São Paulo"
        command_queue = queue.Queue()

        def read_client():
            try:
                for msg in request_iterator:
                    logging.info(f"Recebido do cliente: role={msg.role}, command={msg.command}, message={msg.message}")
                    if msg.role == "client":
                        command_queue.put((msg.command, msg.message))
            except Exception as e:
                logging.error(f"Erro ao ler mensagens do cliente: {e}")
                command_queue.put(("disconnect", ""))

        reader_thread = threading.Thread(target=read_client, daemon=True)
        reader_thread.start()

        disconnect = False
        list_locations = False
        update_now = False

        while not disconnect:
            # Mostra os peers conectados a cada ciclo
            logging.info(f"IPs conectados: {connected_peers}")
            reload_csv_if_needed()
            try:
                # Espera por comando ou timeout para atualização periódica
                cmd, msg = command_queue.get(timeout=10)
                if cmd == "disconnect":
                    disconnect = True
                elif cmd == "change_location":
                    if msg in region_database:
                        current_location = msg
                        logging.info(f"Região atualizada para: {current_location}")
                    else:
                        logging.warning(f"Região desconhecida: {msg}")
                elif cmd == "update_now":
                    update_now = True
                elif cmd == "list_locations":
                    list_locations = True
            except queue.Empty:
                # Timeout: envia atualização periódica
                pass

            current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_ts_ns = time.time_ns()

            if list_locations:
                locations_list = ", ".join(region_database.keys())
                list_msg = make_notification(
                    role="server",
                    type_="control",
                    command="list_locations",
                    message=f"Regiões disponíveis: {locations_list}",
                    timestamp=current_time_str,
                    send_timestamp=send_ts_ns
                )
                yield list_msg
                list_locations = False
            else:
                region_info = region_database.get(current_location, "Dados indisponíveis para a região.")
                notification = make_notification(
                    role="server",
                    type_="notification",
                    command="",
                    message=region_info,
                    timestamp=current_time_str,
                    send_timestamp=send_ts_ns
                )
                yield notification

            if update_now:
                current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                send_ts_ns = time.time_ns()
                region_info = region_database.get(current_location, "Dados indisponíveis para a região.")
                immediate_notification = make_notification(
                    role="server",
                    type_="notification",
                    command="update_now",
                    message=region_info,
                    timestamp=current_time_str,
                    send_timestamp=send_ts_ns
                )
                yield immediate_notification
                update_now = False

        final_msg = make_notification(
            role="server",
            type_="control",
            command="disconnect",
            message="Conexão encerrada pelo servidor.",
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            send_timestamp=time.time_ns()
        )
        yield final_msg
        # Remove peer quando a stream finaliza
        connected_peers.discard(peer)
        logging.info(f"Cliente desconectado: {peer}")

def serve():
    # Configurações do servidor (definidas na função serve)
    host = '[::]'
    port = '50054'
    max_workers = 10

    # Carrega CSV
    global region_database, last_reload_time
    region_database = load_region_database(CSV_FILENAME)
    last_reload_time = time.time()

    # Cria o servidor gRPC com ThreadPoolExecutor
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    control_notifications_pb2_grpc.add_ControlNotifierServicer_to_server(ControlNotifierServicer(), server)
    server_address = f"{host}:{port}"
    server.add_insecure_port(server_address)
    server.start()
    logging.info(f"Servidor rodando em {server_address}...")

    try:
        # Mantém o servidor ativo
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logging.info("Encerrando o servidor...")
        server.stop(0)

if __name__ == '__main__':
    serve()
