import grpc
import time
import threading
import queue

import control_notifications_pb2
import control_notifications_pb2_grpc

def request_generator(send_queue):
    while True:
        msg = send_queue.get()
        if msg is None:
            break
        yield msg

def send_user_commands(send_queue):
    while True:
        user_input = input("Digite um comando (disconnect, update_now, list_locations, change_location:<Região>): ")
        cmd_lower = user_input.strip().lower()
        if cmd_lower == "disconnect":
            command = "disconnect"
            message_text = ""
        elif cmd_lower == "update_now":
            command = "update_now"
            message_text = ""
        elif cmd_lower == "list_locations":
            command = "list_locations"
            message_text = ""
        elif cmd_lower.startswith("change_location"):
            parts = user_input.split(":", 1)
            if len(parts) == 2:
                command = "change_location"
                message_text = parts[1].strip()
            else:
                print("Formato inválido. Use change_location:<Região>")
                continue
        else:
            print("Comando não reconhecido.")
            continue

        control_msg = control_notifications_pb2.Notification(
            role="client",
            type="control",
            command=command,
            message=message_text,
            timestamp="",
            send_timestamp=time.time()
        )
        send_queue.put(control_msg)
        if command == "disconnect":
            send_queue.put(None)
            break

def run_client():
    send_queue = queue.Queue()
    channel = grpc.insecure_channel('localhost:50054')
    stub = control_notifications_pb2_grpc.ControlNotifierStub(channel)

    # Envia mensagem inicial de inscrição
    subscribe_msg = control_notifications_pb2.Notification(
        role="client",
        type="control",
        command="subscribe",
        message="Inscrição para notificações.",
        timestamp="",
        send_timestamp=time.time()
    )
    send_queue.put(subscribe_msg)

    threading.Thread(target=send_user_commands, args=(send_queue,), daemon=True).start()

    responses = stub.NotificationStream(request_generator(send_queue))
    try:
        for response in responses:
            print(f"[{response.timestamp}] {response.role.upper()} - {response.type.upper()} (command: {response.command}): {response.message}")
            if response.role == "server" and response.command == "disconnect":
                print("Conexão encerrada pelo servidor.")
                break
    except grpc.RpcError as e:
        print("Erro na conexão:", e)

if __name__ == '__main__':
    run_client()
