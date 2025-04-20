import grpc
import time
import threading
import queue
import logging
from typing import Iterator

import control_notifications_pb2
import control_notifications_pb2_grpc

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def request_generator(send_queue: queue.Queue) -> Iterator[control_notifications_pb2.Notification]:
    while True:
        msg = send_queue.get()
        if msg is None:
            break
        yield msg

def make_notification(command: str, message_text: str) -> control_notifications_pb2.Notification:
    # Usa timestamp em nanosegundos para compatibilidade com send_timestamp int64
    send_ts_ns = time.time_ns()
    return control_notifications_pb2.Notification(
        role="client",
        type="control",
        command=command,
        message=message_text,
        timestamp="",
        send_timestamp=send_ts_ns
    )

def send_user_commands(send_queue: queue.Queue) -> None:
    simple_cmds = {"disconnect", "update_now", "list_locations"}
    while True:
        try:
            user_input = input("Digite um comando (disconnect, update_now, list_locations, change_location:<Região>): ")
        except (EOFError, KeyboardInterrupt):
            logging.info("Entrada encerrada pelo usuário. Desconectando.")
            send_queue.put(make_notification("disconnect", ""))
            send_queue.put(None)
            break
        cmd_lower = user_input.strip().lower()
        if cmd_lower in simple_cmds:
            command = cmd_lower
            message_text = ""
        elif cmd_lower.startswith("change_location:"):
            command = "change_location"
            message_text = user_input.split(":", 1)[1].strip()
        else:
            logging.warning("Comando não reconhecido ou formato inválido. Use change_location:<Região>.")
            continue

        control_msg = make_notification(command, message_text)
        send_queue.put(control_msg)
        if command == "disconnect":
            send_queue.put(None)
            break

def run_client() -> None:
    send_queue = queue.Queue()
    channel = grpc.insecure_channel('localhost:50054')
    stub = control_notifications_pb2_grpc.ControlNotifierStub(channel)

    threading.Thread(target=send_user_commands, args=(send_queue,), daemon=True).start()

    responses = stub.NotificationStream(request_generator(send_queue))
    try:
        for response in responses:
            # Calcula delay em nanosegundos
            receive_ns = time.time_ns()
            send_ns = response.send_timestamp  # valor em ns enviado pelo servidor
            delay_ns = receive_ns - send_ns
            delay_ms = delay_ns / 1e6  # converte para ms
            logging.info(
                f"[{response.timestamp}] {response.role.upper()} - {response.type.upper()}"
                f" (command: {response.command}): {response.message}"
                f" [delay: {delay_ms:.6f} ms]"
            )
            if response.role == "server" and response.command == "disconnect":
                logging.info("Conexão encerrada pelo servidor.")
                break
    except grpc.RpcError as e:
        logging.error(f"Erro na conexão: {e.code()} - {e.details()}")

if __name__ == '__main__':
    run_client()
