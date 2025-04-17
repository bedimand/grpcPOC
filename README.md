# Sistema de Notificações de Controle via gRPC

Este projeto implementa um sistema de notificações entre cliente e servidor utilizando gRPC em Python. O servidor envia notificações periódicas sobre diferentes regiões, e o cliente pode interagir enviando comandos para controlar o fluxo de informações.

## Estrutura dos Arquivos

- `server.py`: Implementação do servidor gRPC, responsável por enviar notificações e responder a comandos do cliente.
- `client.py`: Implementação do cliente gRPC, que recebe notificações e envia comandos ao servidor.
- `control_notifications.proto`: Definição das mensagens e serviços gRPC (não incluído aqui, mas necessário para gerar os arquivos *_pb2.py*).
- `control_notifications_pb2.py` e `control_notifications_pb2_grpc.py`: Arquivos gerados a partir do proto.
- `locations.csv`: Base de dados das regiões e informações associadas (deve estar presente na mesma pasta do servidor).
- `requirements.txt`: Lista de dependências do projeto.

## Pré-requisitos

- Python 3.7+
- Instalar as dependências:

```bash
pip install -r requirements.txt
```

- Gerar os arquivos gRPC a partir do proto (caso altere o arquivo .proto):

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. control_notifications.proto
```

## Como rodar o servidor

1. Certifique-se de que o arquivo `locations.csv` está presente na mesma pasta do `server.py`.
2. Execute o servidor:

```bash
python server.py
```

O servidor ficará escutando na porta 50054.

## Como rodar o cliente

Abra outro terminal e execute:

```bash
python client.py
```

O cliente irá se conectar ao servidor e exibir as notificações recebidas.

## Comandos disponíveis no cliente

Durante a execução do cliente, você pode digitar os seguintes comandos:

- `disconnect`: Encerra a conexão com o servidor.
- `update_now`: Solicita uma atualização imediata da notificação da região atual.
- `list_locations`: Solicita ao servidor a lista de regiões disponíveis.
- `change_location:<Região>`: Altera a região para receber notificações de outro local. Exemplo: `change_location:Centro`

## Observações

- O servidor recarrega automaticamente o arquivo `locations.csv` a cada 20 segundos.
- O cliente pode ser encerrado a qualquer momento com o comando `disconnect`.
- Certifique-se de que o arquivo `control_notifications.proto` está correto e que os arquivos *_pb2.py* estão atualizados.

---

Qualquer dúvida ou sugestão, fique à vontade para entrar em contato!
