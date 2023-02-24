import json
import logging
import obd


class DatasourceObd(object):

    def __init__(self):
        # Init attributes.
        self.connection = None
        self.channels = {}
        self.values = {}

        # Init logging.
        logging.basicConfig(format='%(asctime)s %(message)s',
                            filename='logs/car.log',
                            level=logging.DEBUG)
        logging.info('Starting elm connection.')

    def connect_obd(self):
        logging.info('Trying to connect to elm.')
        self.connection = obd.OBD()

        # Check status.
        elm_status = self.connection.status()

        if elm_status == obd.OBDStatus.CAR_CONNECTED:
            logging.info('Connection successful.')
            return 1
        elif elm_status == obd.OBDStatus.OBD_CONNECTED:
            logging.warning('Connected, but ignition off.')
            return -1
        elif elm_status == obd.OBDStatus.ELM_CONNECTED:
            logging.warning('Connected to ELM, but not to car.')
            return -2
        else:
            logging.warning('Connection failed.')
            return -3

    def get_channels(self, channel_cfg='../channels.json'):
        logging.info('Importing channel list.')

        if self.connection is None or self.connection.status() != obd.OBDStatus.CAR_CONNECTED:
            logging.warning('Importing canceled. Connect OBD first.')

        # Read channel cfg.
        with open(channel_cfg) as cfg_file:
            cfg = json.load(cfg_file)

        # Store channels in object.
        self.channels = cfg['channels']

        # Check channels if avail.
        for ch in self.channels:
            self.channels[ch]['obd_active'] = self.connection.supports(obd.commands[self.channels[ch]['obd_name']])
            if not self.channels[ch]['obd_active']:
                logging.warning(f'Channel {ch} not available for this car.')

    # Query values from the car.
    # Returns the values as dict.
    def get_values(self):
        # Init value dict.
        self.values = {}

        # Loop over available channels.
        for ch in self.channels:
            # Check if the channel is active.
            if not self.channels[ch]['obd_active']:
                continue

            # Get the value.
            response = self.connection.query(obd.commands[self.channels[ch]['obd_name']])

            if response.is_null():
                self.values[ch] = None
            else:
                # Get the value without unit.
                val_mag = response.value.magnitude

                # Apply conversion if any.
                if self.channels[ch]['obd_conversion']:
                    conversion = self.channels[ch]['obd_conversion'].replace('#', str(val_mag))
                    val_mag = eval(conversion)

                # Write to dict.
                self.values[ch] = val_mag

        return self.values


if __name__ == '__main__':
    datasource_car = DatasourceCar()
    datasource_car.connect_obd()
    datasource_car.get_channels()

    breakpoint()
