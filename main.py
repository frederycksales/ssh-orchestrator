from helpers.config_loader import config, logger
from helpers.ssh_manager import SSHCommandExecutor

def main():
    # Iterate over each device in the configuration
    for device in config.ssh.devices:
        logger.info(
            f"Testing SSH connection to {device.hostname} ({device.ip_address})"
        )
        # Initialize SSHCommandExecutor with device details
        executor = SSHCommandExecutor(
            host=device.ip_address,
            port=device.port,
            username=device.username,
            password=device.password,
            key_filename=device.key_filename,
            hostname=device.hostname,
            commands_file=device.commands_file,
        )
        try:
            # Establish SSH connection
            executor.connect()
            # Open an interactive terminal session
            executor.interactive_terminal()
            # Wait for prompt
            executor.wait_for_prompt(prompt=r"\:\~\$")
            # Execute commands from file with specified prompt
            executor.execute_commands_from_file(prompt=r"\:\~\$", to_file=True)
        except Exception as e:
            logger.error(f"Failed to execute commands on {device.hostname}: {e}")

if __name__ == "__main__":
    main()
