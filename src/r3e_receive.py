import socket
import logging
from datetime import datetime

BUFFER_SIZE = 1024
LOCAL_IP = "127.0.0.1"
DEFAULT_PORT = 11000


# Convert a string to a suitable type: float, int or remain string.
def string2val(string):
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string


class R3eReceive(object):

    def __init__(self):
        # Init attributes.
        self.udp_server = None
        self.buffer_size = 1024
        self.values = {}
        self.last_rec_address = ''
        self.logfile = ''
        self.channels = {}
        self.channels_short = {}

        # Init logging.
        logging.basicConfig(format='%(asctime)s %(message)s',
                            filename='r3e.log',
                            level=logging.DEBUG)

        # Set datafile.
        self.data_file = fr'logs\{datetime.now().strftime("%y%m%d_%H%M%S_r3e.dat")}'
        with open(self.data_file, 'w') as data_file_handle:
            data_file_handle.write('PosX,PosY,PosZ,Speed,AccX,AccY,AccZ,\n')

    # Set the channels attribute.
    # Also set up a dict "channels_short" as a map to quickly find channel names from short names.
    def set_channels(self, channels_in):
        # Set the channels attribute.
        self.channels = channels_in

        # Collect the short names.
        self.channels_short = {}
        for ch in self.channels:
            self.channels_short[self.channels[ch]['short_name']] = ch

    # Setup udp server to receive data from r3e.
    def connect_udp(self, ip=LOCAL_IP, port=DEFAULT_PORT, buffer_size=BUFFER_SIZE):
        # Create a datagram socket.
        self.udp_server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        # Bind to address and ip
        self.udp_server.bind((ip, port))
        logging.info("UDP server up and listening")

        self.buffer_size = buffer_size

    # Write data directly to a file.
    # Should not be used any more. Use auto-telemetry.
    # TODO: Change to full names.
    def write_to_datafile(self):
        # Setup write string.
        write_str = ''
        write_str += '{:8.3f},'.format(self.values['Ti'])
        write_str += '{:8.3f},{:8.3f},{:8.3f},'.format(self.values['Lx'], self.values['Ly'], self.values['Lz'])
        write_str += '{:8.3f},'.format(self.values['S'])
        write_str += '{:8.3f},{:8.3f},{:8.3f},'.format(self.values['Ax'], self.values['Ay'], self.values['Az'])
        write_str += '\n'

        with open(self.data_file, 'a') as data_file_handle:
            data_file_handle.write(write_str)

    # Get current values.
    # Reads from udp input.
    # Converts the input and writes it to "values" for use in auto-telemetry.
    def get_values(self):
        bytes_address_pair = self.udp_server.recvfrom(self.buffer_size)

        self.last_rec_address = bytes_address_pair[1]

        # Decode byte message.
        client_msg = bytes_address_pair[0].decode('utf-8')
        logging.info(f"Message received: {client_msg}")

        # Get values from string.
        msg_split = client_msg.split(';')

        self.values = {}
        for val in msg_split:
            # Split at : in name and value.
            val_split = val.split(':')

            # Store the value.
            # Get full name and convert to correct type.
            self.values[self.channels_short[val_split[0]]] = string2val(val_split[1])

        return self.values


if __name__ == '__main__':
    # Create object and connect udp.
    r3e = R3eReceive()
    r3e.connect_udp()

    while True:
        r3e.get_values()
        r3e.write_to_datafile()
