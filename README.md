# SSH Orchestrator - Multiple Targets Multiple Commands

## Table of Contents

- [SSH - Multiple Targets Multiple Commands Orchestrator](#ssh---multiple-targets-multiple-commands-orchestrator)
  - [Table of Contents](#table-of-contents)
  - [Introdução](#introdução)
  - [Descrição](#descrição)
  - [Características](#características)
  - [Pré-requisitos](#pré-requisitos)
  - [Instalação](#instalação)
  - [Configuração](#configuração)
  - [Uso](#uso)
    - [Passos Realizados pelo Script](#passos-realizados-pelo-script)
  - [Estrutura do Projeto](#estrutura-do-projeto)
  - [Logs](#logs)

## Introdução

O **SSH Orchestrator** é uma ferramenta em Python projetada para gerenciar e executar comandos SSH em múltiplos dispositivos de forma automatizada. Este projeto facilita a administração de redes e sistemas, permitindo a execução simultânea de tarefas em diversos dispositivos de maneira eficiente e segura.

## Descrição

O **SSH Orchestrator** utiliza a biblioteca Paramiko para estabelecer conexões SSH, executar comandos definidos em arquivos específicos para cada dispositivo e registrar as saídas de forma organizada.

## Características

- **Conexões SSH Automatizadas:** Estabelece conexões SSH com dispositivos usando autenticação por senha ou chave privada.
- **Execução de Comandos em Massa:** Executa comandos listados em arquivos específicos para cada dispositivo.
- **Processamento de Saída:** Limpa e filtra a saída dos comandos, removendo códigos ANSI e backspaces.
- **Registro de Logs:** Mantém registros detalhados das operações e erros em arquivos de log.
- **Flexibilidade de Configuração:** Configurações centralizadas em arquivos YAML para fácil personalização.
- **Interface de Linha de Comando:** Simples execução via script Python principal.

## Pré-requisitos

Antes de começar, certifique-se de ter os seguintes itens instalados em sua máquina:

- **Python 3.8 ou superior**
- **pip** (gerenciador de pacotes Python)

## Instalação

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/ssh-orchestrator.git
   cd ssh-orchestrator
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuração

1. **Configuração Geral (`config/config.yaml`):**

   Este arquivo contém as configurações gerais do projeto, incluindo a lista de dispositivos SSH e diretórios de dados.

   ```yaml
   general:
     data_dir: "data"
     logs_dir: "logs"
     debug_log: "app.log"

   ssh:
     devices:
       - hostname: "dispositivo1"
         ip_address: "192.168.1.10"
         port: 22
         username: "usuario1"
         password: "senha1"  # Opcional se usar chave privada
         key_filename: "/caminho/para/chave_privada1.pem"  # Opcional se usar senha
         commands_file: "data/commands/commands_device_1.txt"
       - hostname: "dispositivo2"
         ip_address: "192.168.1.11"
         port: 22
         username: "usuario2"
         password: "senha2"
         key_filename: "/caminho/para/chave_privada2.pem"
         commands_file: "data/commands/commands_device_2.txt"
   ```

   - **`general.data_dir`:** Diretório onde os arquivos de saída serão armazenados.
   - **`ssh.devices`:** Lista de dispositivos SSH com suas respectivas configurações.

2. **Arquivos de Comandos (`data/commands/commands_device_*.txt`):**

   Cada dispositivo possui um arquivo de comandos correspondente. Liste os comandos que deseja executar nesses arquivos, um por linha.

   **Exemplo (`commands_device_1.txt`):**

   ```bash
   show version
   show ip interface brief
   ```

## Uso

Execute o script principal para iniciar a orquestração das conexões SSH e a execução dos comandos:

```bash
python main.py
```

### Passos Realizados pelo Script

1. **Iteração sobre Dispositivos:**
   - O script lê a lista de dispositivos definidos em `config/config.yaml`.

2. **Estabelecimento de Conexão SSH:**
   - Para cada dispositivo, uma conexão SSH é estabelecida usando as credenciais fornecidas (senha ou chave privada).

3. **Abertura de Terminal Interativo:**
   - Após a conexão, um terminal interativo é aberto para permitir a execução de comandos.

4. **Execução de Comandos:**
   - O script espera pelo prompt especificado e executa os comandos listados no arquivo de comandos correspondente ao dispositivo.

5. **Registro de Saída:**
   - As saídas dos comandos são processadas (limpeza e filtragem) e registradas em arquivos dentro do diretório `data/output`.

6. **Tratamento de Erros:**
   - Qualquer erro durante o processo é registrado no arquivo de log `logs/app.log`.

## Estrutura do Projeto

```
ssh-orchestrator/
├── config/
│   └── config.yaml          # Arquivo de configuração principal
├── data/
│   ├── commands/
│   │   ├── commands_device_1.txt  # Comandos para dispositivo 1
│   │   └── commands_device_2.txt  # Comandos para dispositivo 2
│   └── output/              # Diretório para armazenar saídas dos comandos
├── helpers/
│   ├── config_loader.py     # Carregamento e validação da configuração
│   ├── __init__.py
│   ├── ssh_manager.py       # Gerenciamento de conexões SSH e execução de comandos
│   └── text_processor.py    # Processamento de saída de comandos
├── logs/
│   └── app.log              # Arquivo de logs da aplicação
├── main.py                  # Script principal de execução
├── requirements.txt         # Lista de dependências do projeto
└── README.md                # Este arquivo
```

## Logs

Os logs da aplicação são armazenados no arquivo `logs/app.log`. Eles contêm informações detalhadas sobre as operações realizadas, incluindo:

- Inicialização de conexões SSH
- Execução de comandos
- Erros e exceções
- Informações gerais de status

**Exemplo de Entrada de Log:**

```
2025-01-17 12:16:46,123 - INFO - Loading configuração from /path/to/config/config.yaml
2025-01-17 12:16:46,456 - INFO - Configuração loaded and validated successfully.
2025-01-17 12:17:00,789 - INFO - Testing SSH connection to dispositivo1 (192.168.1.10)
2025-01-17 12:17:01,012 - INFO - Conectado a 192.168.1.10:22
2025-01-17 12:17:01,345 - INFO - Terminal interativo criado.
2025-01-17 12:17:02,678 - INFO - Prompt recebido.
2025-01-17 12:17:03,901 - INFO - Executando comando: show version
2025-01-17 12:17:04,234 - INFO - Comando executado com sucesso.
2025-01-17 12:17:04,567 - INFO - Saída registrada no arquivo: data/output/output_192.168.1.10_dispositivo1.txt
```
