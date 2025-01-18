import os
import paramiko
import socket
import time
import re
import select
from helpers.config_loader import config, logger
from helpers.text_processor import clean, dedent, filter_lines


class SSHCommandExecutor:
    """
    Class responsible for managing the execution of SSH commands on remote devices.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str = None,
        key_filename: str = None,
        ciphers: tuple = None,
        hostname: str = None,
        commands_file: str = None,
    ):
        """
        Initializes the SSHCommandExecutor instance with the provided credentials and settings.

        Args:
            host (str): IP address or hostname of the SSH device.
            port (int): Port for SSH connection, default is 22.
            username (str): Username for SSH authentication.
            password (str, optional): Password for SSH authentication. Default is None.
            key_filename (str, optional): Path to the private key file for authentication. Default is None.
            ciphers (tuple, optional): List of allowed encryption ciphers. Default is None, uses standard ciphers if not provided.
            hostname (str, optional): Friendly name of the host. Default is None.
            commands_file (str, optional): Path to the file containing commands to be executed. Default is None.

        Raises:
            ValueError: If neither the password nor the key file is provided for authentication.
        """
        logger.info(
            f"Initializing SSHCommandExecutor for {host}:{port} with user {username}"
        )
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.ciphers = ciphers or ("aes128-ctr", "aes192-ctr", "aes256-ctr")
        self.hostname = hostname
        self.commands_file = commands_file
        self.client = None
        self.channel = None

        if not self.password and not self.key_filename:
            raise ValueError(
                "You must provide either the password or the path to the key file for authentication."
            )

    def connect(self, retries: int = 3, delay: int = 3):
        """
        Establishes an SSH connection with cipher validation.

        Args:
            retries (int, optional): Number of connection attempts in case of failure. Default is 3.
            delay (int, optional): Wait time between connection attempts in seconds. Default is 3.

        Raises:
            ConnectionError: If unable to establish the connection after the specified attempts.
        """
        logger.info(
            f"Attempting to connect to {self.host}:{self.port} with retries={retries}, delay={delay}"
        )

        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Configure security options, such as allowed ciphers
        transport = self.client.get_transport()
        if transport:
            security_options = transport.get_security_options()
            security_options.ciphers = self.ciphers

        for attempt in range(1, retries + 1):
            try:
                if self.key_filename:
                    # Connect using key authentication
                    self.client.connect(
                        hostname=self.host,
                        port=self.port,
                        username=self.username,
                        key_filename=self.key_filename,
                        look_for_keys=False,
                        allow_agent=False,
                        timeout=10,
                    )
                else:
                    # Connect using password authentication
                    self.client.connect(
                        hostname=self.host,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        look_for_keys=False,
                        allow_agent=False,
                        timeout=10,
                    )
                logger.info(f"Connected to {self.host}:{self.port}")
                return
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                logger.warning(f"Connection attempt {attempt}/{retries} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Failed to connect to {self.host} after {retries} attempts."
                    )
                    raise ConnectionError(
                        f"Failed to connect to {self.host} after {retries} attempts."
                    ) from e
            except socket.error as e:
                logger.error(f"Socket error during connection: {e}")
                raise ConnectionError(f"Socket error during connection: {e}") from e

    def interactive_terminal(self):
        """
        Creates an interactive SSH terminal.

        Raises:
            ValueError: If the SSH client is not connected.
            RuntimeError: If failed to create the interactive terminal.
        """
        transport = self.client.get_transport()
        if not transport or not transport.is_active():
            logger.error("SSH client is not connected.")
            raise ValueError("The SSH client must be connected.")

        try:
            self.channel = self.client.invoke_shell()
            logger.info("Interactive terminal created.")
        except paramiko.SSHException as e:
            logger.error(f"Failed to create interactive terminal: {e}")
            raise RuntimeError(f"Failed to create interactive terminal: {e}") from e

    def wait_for_prompt(self, prompt: str, timeout: int = 30) -> bool:
        """
        Waits for a specific prompt on the SSH channel.

        Args:
            prompt (str): Regular expression representing the expected prompt.
            timeout (int, optional): Maximum wait time in seconds. Default is 30.

        Returns:
            bool: True if the prompt is detected, otherwise raises an exception.

        Raises:
            TimeoutError: If the prompt is not detected within the specified time.
            paramiko.SSHException: If an SSH-related exception occurs.
            Exception: For any other unexpected exceptions.
        """
        if not self.channel:
            logger.error("SSH channel is not initialized.")
            raise ValueError("The SSH channel is not initialized.")
        if (
            not self.channel.get_transport()
            or not self.channel.get_transport().is_active()
        ):
            logger.error("SSH channel is not active.")
            raise ValueError("The SSH channel is not active.")

        start_time = time.time()

        try:
            while time.time() - start_time < timeout:
                if self.channel.recv_ready():
                    chunk = self.channel.recv(4096).decode("utf-8", errors="ignore")
                    if re.search(prompt, chunk):
                        logger.info("Prompt received.")
                        return True
                else:
                    # Check if there is data available to read
                    r, _, _ = select.select([self.channel], [], [], 1)
                    if r:
                        continue
                time.sleep(0.1)

            logger.error("Timeout without detecting the prompt.")
            raise TimeoutError("Prompt not detected within the specified time.")
        except paramiko.SSHException as ssh_error:
            logger.error(f"An SSH exception occurred: {ssh_error}")
            raise
        except Exception as general_error:
            logger.error(f"An unexpected exception occurred: {general_error}")
            raise

    def execute_command(
        self, cmd: str, prompt: str, to_file: bool, timeout: int = 30
    ) -> str:
        """
        Executes a command in the interactive terminal and returns the output.

        Args:
            cmd (str): Command to be executed.
            prompt (str): Regular expression representing the expected prompt after command execution.
            to_file (bool): Indicates if the output should be logged to a file.
            timeout (int, optional): Maximum wait time in seconds for command execution. Default is 30.

        Returns:
            str: Dedented and filtered output of the executed command.

        Raises:
            ValueError: If the interactive terminal is not initialized.
            TimeoutError: If the prompt is not detected within the specified time.
        """
        if not self.channel:
            raise ValueError("Interactive terminal is not initialized.")

        logger.info(f"Executing command: {cmd}")
        self.channel.send(f"{cmd}\n")
        result = ""
        start_time = time.time()

        while True:
            if self.channel.recv_ready():
                chunk = self.channel.recv(4096).decode("utf-8", errors="ignore")
                # Handles output pagination
                if "--More--" in chunk:
                    self.channel.send(" ")
                    chunk = chunk.replace("--More--", "")
                if "(END)" in chunk:
                    self.channel.send("q")
                    chunk = chunk.replace("(END)", "")
                result += clean(chunk)
            if re.search(prompt, result):
                break
            if time.time() - start_time > timeout:
                logger.error("Prompt not detected within the time limit.")
                raise TimeoutError("Prompt not detected within the time limit.")

        # Process the output: filter irrelevant lines and remove indentation
        filtered_output = filter_lines(result, [cmd, prompt])
        dedented_output = dedent(filtered_output)

        if to_file:
            self.log_output_to_file(dedented_output)

        logger.info("Command executed successfully.")
        return dedented_output

    def log_output_to_file(self, output: str):
        """
        Logs the command output to a file.

        Args:
            output (str): Content to be logged to the file.

        Raises:
            ValueError: If the data directory is not specified in the configuration.
            Exception: If an error occurs while writing to the file.
        """
        try:
            data_dir = config.general.get("data_dir")
            if not data_dir:
                raise ValueError("Data directory not specified in the configuration.")
            output_dir = os.path.join(data_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            safe_hostname = self.hostname or "unknown_host"
            filename = os.path.join(
                output_dir, f"output_{self.host}_{safe_hostname}.txt"
            )
            with open(filename, "a", encoding="utf-8") as file:
                file.write(output + "\n")
            logger.info(f"Output logged to file: {filename}")
        except Exception as e:
            logger.error(f"Failed to write output to file: {e}")
            raise

    def confirm_close(self):
        """
        Checks if the SSH connection is closed and closes it if not.
        """
        # Close the SSH channel if it is open
        if self.channel:
            if self.channel.closed:
                logger.info("SSH channel is already closed.")
            else:
                self.channel.close()
                time.sleep(0.5)
                if self.channel.closed:
                    logger.info("SSH channel closed successfully.")
                else:
                    logger.warning("Failed to close the SSH channel.")
        else:
            logger.info("SSH channel is not initialized.")

        # Close the SSH client if it is connected
        if self.client:
            transport = self.client.get_transport()
            if not transport or not transport.is_active():
                logger.info("SSH connection is already closed.")
            else:
                self.client.close()
                time.sleep(0.5)
                transport = self.client.get_transport()
                if not transport or not transport.is_active():
                    logger.info("SSH connection closed successfully.")
                else:
                    logger.warning("Failed to close the SSH connection.")
        else:
            logger.info("SSH client is not initialized.")

    def execute_commands_from_file(
        self, prompt: str, to_file: bool = True, timeout: int = 30
    ):
        """
        Reads commands from a file and executes them sequentially on the SSH terminal.

        Args:
            prompt (str): Regular expression representing the expected prompt after each command execution.
            to_file (bool, optional): Indicates if the command outputs should be logged to files. Default is True.
            timeout (int, optional): Maximum wait time in seconds for each command. Default is 30.

        Raises:
            ValueError: If the commands file is not specified.
            FileNotFoundError: If the commands file is not found.
            Exception: If an error occurs during command execution.
        """
        if not self.commands_file:
            logger.error("No commands file specified.")
            raise ValueError("No commands file specified.")
        if not os.path.isfile(self.commands_file):
            logger.error(f"Commands file not found: {self.commands_file}")
            raise FileNotFoundError(
                f"Commands file not found: {self.commands_file}"
            )

        try:
            with open(self.commands_file, "r", encoding="utf-8") as file:
                commands = file.readlines()

            for cmd in commands:
                cmd = cmd.strip()
                if cmd:
                    self.execute_command(cmd, prompt, to_file, timeout)
        except Exception as e:
            logger.error(f"Error executing commands from file: {e}")
            raise
        finally:
            self.confirm_close()

    def __enter__(self):
        """
        Allows the use of the class with context managers (with statement).

        Returns:
            SSHCommandExecutor: Current instance of the class.
        """
        self.connect()
        self.interactive_terminal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ensures the SSH connection is closed when exiting the context.

        Args:
            exc_type: Exception type, if any.
            exc_val: Exception value, if any.
            exc_tb: Exception traceback, if any.
        """
        self.confirm_close()
