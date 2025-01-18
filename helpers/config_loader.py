import os
import logging
from pydantic import BaseModel, field_validator
from typing import List, Optional
import yaml
import socket

# Initial logging configuration
# Define the absolute path for the log file
log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../logs/app.log"))

# Configure the logger with INFO level, message format, and output file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=log_path,
    filemode="a",  # 'a' to append to the existing file, 'w' to overwrite
)

# Create a logger instance for this module
logger = logging.getLogger(__name__)

# Class representing the configuration of an SSH device
class SSHDevice(BaseModel):
    """Represents the configuration of an SSH device."""

    hostname: str  # Hostname of the device
    ip_address: str  # IP address of the device
    port: int = 22  # SSH port, default is 22
    username: str  # Username for SSH authentication
    password: Optional[str] = None  # Password for SSH authentication (optional)
    key_filename: Optional[str] = None  # Path to the private key file (optional)
    commands_file: str  # Path to the file with commands to be executed on the device

    @field_validator("ip_address")
    def validate_ip_address(cls, value):
        """Validates if the IP address is valid (IPv4 or IPv6)."""
        try:
            socket.inet_pton(socket.AF_INET, value)  # Try to validate as IPv4
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, value)  # Try to validate as IPv6
            except socket.error:
                raise ValueError(f"Invalid IP address: {value}")  # Raise error if not valid
        return value

    @field_validator("port")
    def validate_port(cls, value):
        """Validates if the port is within the allowed range (0-65535)."""
        if not (0 <= value <= 65535):
            raise ValueError(f"Invalid port number: {value}")
        return value

    # Validator commented out to check the existence of the private key file
    # @field_validator("key_filename")
    # def validate_key_filename(cls, value):
    #     """Validates if the key_filename points to an existing file."""
    #     if value:
    #         path = Path(value)
    #         if not path.is_file():
    #             raise ValueError(f"Private key file not found: {value}")
    #     return value

# Class representing the SSH configuration containing multiple devices
class SSHConfig(BaseModel):
    """Represents the SSH configuration containing a list of devices."""

    devices: List[SSHDevice]  # List of configured SSH devices

# Class representing the overall project configuration
class Config(BaseModel):
    """Represents the overall project configuration."""

    general: dict  # General project configurations
    ssh: SSHConfig  # Specific SSH configuration

    @classmethod
    def load_config(cls, path: str):
        """
        Loads the configuration from a YAML file.

        Args:
            path (str): Path to the YAML configuration file.

        Returns:
            Config: Instance of the loaded and validated configuration.

        Logs:
            Informs about the start of the loading process.
            Logs an error if the loading fails.
        """
        logger.info(f"Loading configuration from {path}")
        try:
            with open(path, "r") as file:
                data = yaml.safe_load(file)  # Load the YAML content
            return cls(**data)  # Create an instance of Config with the loaded data
        except Exception as e:
            logger.error(f"Failed to load configuration from {path}: {e}")
            raise  # Re-raise the exception after logging the error

# Load the configuration when this module is imported
config = None
try:
    # Define the absolute path to the configuration file
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../config/config.yaml")
    )
    # Load and validate the configuration using the Config class method
    config = Config.load_config(config_path)
    logger.info("Configuration loaded and validated successfully.")
except Exception as e:
    # Log an error if the loading fails and re-raise the exception
    logger.error(f"Failed to load configuration: {e}")
    raise
