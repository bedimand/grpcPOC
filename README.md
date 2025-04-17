# Sistema de Notificações de Controle via gRPC

Este projeto é um exemplo completo de comunicação cliente-servidor usando gRPC em Python, com foco em notificações dinâmicas baseadas em regiões. O sistema permite que múltiplos clientes recebam notificações periódicas do servidor, podendo interagir com ele através de comandos para alterar o comportamento das notificações.

---

## Visão Geral do Funcionamento

- O **servidor** mantém uma base de dados de regiões (em um arquivo CSV) e envia notificações periódicas sobre a região selecionada pelo cliente.
- O **cliente** pode:
  - Solicitar atualização imediata das informações.
  - Listar todas as regiões disponíveis.
  - Trocar a região de interesse.
  - Encerrar a conexão.
- Toda a comunicação é feita via gRPC, usando mensagens definidas em um arquivo `.proto`.

---

## Estrutura dos Arquivos e Função de Cada Um

### `server.py`
- **Função:** Implementa o servidor gRPC.
- **Por que existe:** É o núcleo do sistema, responsável por:
  - Receber comandos dos clientes.
  - Gerenciar o estado de cada cliente (região atual, comandos recebidos).
  - Ler periodicamente o arquivo `locations.csv` para atualizar as informações das regiões.
  - Enviar notificações automáticas e sob demanda para os clientes.

### `client.py`
- **Função:** Implementa o cliente gRPC.
- **Por que existe:** Permite ao usuário interagir com o servidor, recebendo notificações e enviando comandos. Ele:
  - Exibe as notificações recebidas do servidor.
  - Permite ao usuário digitar comandos para controlar o fluxo de informações.

### `control_notifications.proto`
- **Função:** Define as mensagens e serviços gRPC usados na comunicação.
- **Por que existe:** É o contrato entre cliente e servidor, garantindo que ambos "falem a mesma língua". A partir dele são gerados os arquivos Python necessários para o gRPC funcionar.

### `control_notifications_pb2.py` e `control_notifications_pb2_grpc.py`
- **Função:** Arquivos gerados automaticamente a partir do `.proto`.
- **Por que existem:** São usados internamente pelo Python/gRPC para serializar/deserializar mensagens e definir as interfaces de comunicação.

### `locations.csv`
- **Função:** Base de dados simples das regiões e suas informações.
- **Por que existe:** Permite que o servidor envie informações dinâmicas e facilmente editáveis sobre diferentes regiões, sem precisar alterar o código.
- **Formato esperado:**
  ```csv
  location,info
  Centro,Informações do Centro
  Norte,Informações do Norte
  ...
  ```

### `requirements.txt`
- **Função:** Lista as dependências do projeto.
- **Por que existe:** Facilita a instalação dos pacotes necessários para rodar o sistema.

---

## Como Executar o Projeto

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Gere os arquivos gRPC (se necessário)
Se você modificar o arquivo `.proto`, gere novamente os arquivos Python:
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. control_notifications.proto
```

### 3. Prepare o arquivo `locations.csv`
Certifique-se de que o arquivo existe e está no formato correto (veja acima).

### 4. Rode o servidor
```bash
python server.py
```

### 5. Rode o cliente (em outro terminal)
```bash
python client.py
```

---

## Comandos Disponíveis no Cliente

- `disconnect` — Encerra a conexão com o servidor.
- `update_now` — Solicita uma atualização imediata da notificação da região atual.
- `list_locations` — Solicita ao servidor a lista de regiões disponíveis.
- `change_location:<Região>` — Altera a região para receber notificações de outro local. Exemplo: `change_location:Centro`

---

## Observações e Dicas

- O servidor recarrega automaticamente o arquivo `locations.csv` a cada 20 segundos, permitindo atualização dinâmica das informações.
- O cliente pode ser encerrado a qualquer momento com o comando `disconnect`.
- O sistema pode ser expandido facilmente para incluir novas regiões ou comandos, bastando editar o CSV ou o arquivo `.proto`.
- Para múltiplos clientes, basta rodar vários `client.py` em terminais diferentes.

---

Qualquer dúvida ou sugestão, fique à vontade para entrar em contato!
