from r3e_receive import R3eReceive
import logging


class AutoTelemetry(object):

    def __init__(self):
        # Init attributes.
        # Values.
        self.values = {}

        # Datasource.
        self.datasource_type = 0
        self.datasource_obj = None

        # Init logging.
        logging.basicConfig(format='%(asctime)s %(message)s',
                            filename='auto.log',
                            level=logging.DEBUG)

    # Set datasource and init receive object.
    def set_datasource(self, source):
        if source == 'car' or source == 1:
            self.datasource_type = 1
            self.datasource_obj = None
            logging.info(f'Datasource "car" not implemented yet.')

        elif source == 'r3e' or source == 'R3E' or source == 2:
            self.datasource_type = 2
            self.datasource_obj = R3eReceive()
            self.datasource_obj.connect_udp()
            logging.info(f'Datasource "R3E" not implemented yet.')

        else:
            self.datasource_type = 0
            self.datasource_obj = None
            logging.info(f'Datasource "{source}" unkown.')

    # Get values from any type of datasource.
    def get_values(self):
        # Check if datasource was set.
        if self.datasource_obj is None:
            logging.warning('Set datasource first before asking for values.')
            return

        # Get values from whatever datasource is set.
        self.values = self.datasource_obj.get_values()
