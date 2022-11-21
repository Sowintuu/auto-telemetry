import socket


# Convert a string to a suitable type: float, int or remain string.
def string2val(string):
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string


if __name__ == '__main__':

    localIP = "127.0.0.1"
    localPort = 11000
    bufferSize = 1024

    # Create a datagram socket
    udp_server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Bind to address and ip
    udp_server.bind((localIP, localPort))
    print("UDP server up and listening")

    # Listen for incoming datagrams.
    print('Lx:-000.000  Ly:-00.000  Lz:-00.000')
    while True:
        bytesAddressPair = udp_server.recvfrom(bufferSize)

        address = bytesAddressPair[1]

        # Decode byte message.
        client_msg = bytesAddressPair[0].decode('utf-8')

        # Get values from string.
        msg_split = client_msg.split(';')

        values = {}
        for val in msg_split:
            # Split at : in name and value.
            val_split = val.split(':')

            # Convert to correct type.
            values[val_split[0]] = string2val(val_split[1])

        # Print the values.
        print_str = ''
        # print_str = 'Lx:{:8.3f}  Ly:{:8.3f}  Lz:{:8.3f}'.format(values['Lx'], values['Ly'], values['Lz'])
        print_str += 'S:{:8.3f}  '.format(values['S'])
        print_str += 'Ax:{:8.3f}  Ay:{:8.3f}  Az:{:8.3f}  '.format(values['Ax'], values['Ay'], values['Az'])

        print(print_str)

        # breakpoint()
