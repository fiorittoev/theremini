import serial


def read_serial_data(port, baudrate=115200, timeout=1):
    """Reads data from a serial port.

    Args:
        port (str): The serial port to read from (e.g., 'COM1' on Windows, '/dev/ttyUSB0' on Linux).
        baudrate (int): The baud rate of the serial connection (default: 9600).
        timeout (int or float): The timeout in seconds for reading data (default: 1).

    Returns:
        str: The data read from the serial port.
    """

    with serial.Serial(port, baudrate, timeout=timeout) as ser:
        while True:
            data = ser.readline().decode("utf-8").strip()
            if data:
                print(data)


if __name__ == "__main__":
    port = "COM3"  # Replace with your actual port
    read_serial_data(port)
