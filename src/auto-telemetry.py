import os
import sys
import time
import logging
import json
from datetime import datetime

import MySQLdb
import thingspeak

from datasourceObd import DatasourceObd
from datasourceRbox import DatasourceRbox
from r3e_receive import R3eReceive
from datasourceRnd import DatasourceRnd

if os.name == 'posix':
    from datasourceGpio import DatasourceGpio


class AutoTelemetry(object):

    def __init__(self, logfile_dir=''):
        # Init attributes.
        # Values.
        self.values = {}

        # Config.
        self.channels = {}
        self.options = {}

        # Datasources.
        self.datasources = {}

        # Database SQL.
        self.db = None
        self.db_curs = None
        self.db_address = 'localhost'
        self.db_password = 'Laendle_MS_sql'
        self.db_name = 'laendle_ms'
        self.db_table_name = ''

        # Database thingspeak.
        self.thingspeak_channels = []
        self.thingspeak_last_send = time.time()-60
        self.thingspeak_interval = 15

        # Datalogging.
        self.logfile_path = ''
        self.logfile_dir = logfile_dir
        self.get_logfile_path()

        # Init logging.
        logging.basicConfig(format='%(asctime)s %(message)s',
                            filename='auto.log',
                            level=logging.DEBUG)

        # Output logging to console.
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    # Set logfile path from logfile dir and current time.
    # If logfile path is not set yet, set it too.
    def get_logfile_path(self):
        # Get logfile path if not set already.
        if not self.logfile_dir:
            if not self.logfile_dir and os.name == 'nt':
                self.logfile_dir = 'logs'
            else:
                self.logfile_dir = '/home/pi/telemetry/'  #

        # Create directory, if not already exists.
        if not os.path.isdir(self.logfile_dir):
            os.makedirs(self.logfile_dir)

        # Set the logfile path.
        self.logfile_path = os.path.join(self.logfile_dir, datetime.now().strftime("%y%m%d_%H%M%S_tele.dat"))

    # Read all channels from a json file.
    def read_channel_config(self, channel_file='../channels.json'):
        # Read the json content.
        with open(channel_file) as json_file:
            json_load = json.load(json_file)

        # Store the channels in the property.
        self.channels = json_load['channels']
        # TODO: Check for file integrity.
        # No duplicate channels.
        # No duplicate short names.

        # Store the other options.
        self.options = json_load['options']

    # Add datasource and init receive object.
    def add_datasource(self, source_add):
        # Check if a channel config is already loaded.
        if not self.channels:
            logging.warning('Load channel config first.')
            return

        # Check if the source is already added.
        if source_add not in self.datasources:
            # Create the source object and add it.
            if source_add == 'obd':
                self.datasources['obd'] = DatasourceObd()
                result = self.datasources['obd'].connect_obd()
                if result == 1:
                    self.datasources[source_add].channels = self.channels
                    self.datasources['obd'].check_channel_availability()
                else:
                    self.datasources.pop('obd')
                    return
                logging.warning('Error connecting to ELM.')

            elif source_add == 'gpio':
                self.datasources['gpio'] = DatasourceGpio()
                self.datasources[source_add].channels = self.channels

            elif source_add == 'r_box':
                self.datasources['r_box'] = DatasourceRbox()
                self.datasources[source_add].channels = self.channels

            elif source_add == 'r3e':
                self.datasources['r3e'] = R3eReceive()
                self.datasources['r3e'].connect_udp()
                self.datasources[source_add].set_channels(self.channels)

            elif source_add == 'rnd':
                self.datasources['rnd'] = DatasourceRnd()
                self.datasources[source_add].channels = self.channels
                self.datasources['rnd'].init_random()

            else:
                # Show warning if datasource not known.
                logging.warning(f'Datasource {source_add} unknown.')
                return

            # Log for successful addition.
            logging.info(f'Datasource {source_add} added.')

        else:
            # Show warning, if already added.
            logging.warning(f'Datasource {source_add} already added.')

    def connect_sql(self):
        # TODO: Adjust to new channel structure.
        # TODO: Catch exceptions more explicitly.
        # Except possible errors
        try:
            # Connect to db.
            self.db = MySQLdb.connect(self.db_address, "root", self.db_password, self.db_name)
            self.db_curs = self.db.cursor()

            # Set table name from date.
            self.db_table_name = datetime.now().strftime("tele_%y%m%d_%H%M%S")

            # Create new table with channels from config.
            db_string = f'CREATE TABLE {self.db_table_name}(id int NOT NULL AUTO_INCREMENT, session_time TIME, '
            for val in self.channels:
                # Ignore time channel.
                if val == 'Ti':
                    continue
                db_string += f'{val} {self.config["channels"][2].upper()},'

            db_string += ' PRIMARY KEY(id));'

            self.db_curs.execute(db_string)
            self.db.commit()

        except:
            if self.db is None:
                logging.warning('Error. No db created.')
            else:
                logging.warning("Error. Rolling back.")
                self.db.rollback()

    # Get values from the datasource with the highest priority.
    def get_values(self):
        # Check if datasource was set.
        if not self.datasources:
            logging.warning('Set datasource first before asking for values.')
            return

        # Get values at all datasources.
        for src in self.datasources:
            self.datasources[src].get_values()

        # Get value for every channel.
        for ch in self.channels:
            # Loop over datasources in order, to get the value from the prioritized datasource.
            for src in self.channels[ch]['src_prio']:
                # Check if the prioritized datasource is added.
                if src in self.datasources:
                    # Get the value and continue with the next channel.
                    self.values[ch] = self.datasources[src].values[ch]
                    break

    # Write locally to a file.
    def write_to_file(self):
        # Check if values for writing are present.
        if not self.values:
            logging.debug('No values for writing to data file.')
            return

        # Set string for logging.
        log_string = f'{datetime.now().strftime("%y%m%d_%H%M%S")},'
        for var in self.values:
            log_string += f'{self.values[var]},'
        log_string.strip(',')
        log_string += '\n'

        # Write string to file.
        # Check if file exists. If not, write the header and the first data.
        if not os.path.isfile(self.logfile_path):
            header_str = 'time,'
            for val in self.values:
                header_str += f'{val},'
            header_str.strip(',')
            header_str += '\n'
            with open(self.logfile_path, 'w') as logfile:
                logfile.write(header_str)
                logfile.write(log_string)

        # Else, write only the data.
        else:
            with open(self.logfile_path, 'a') as logfile:
                logfile.write(log_string)

    # Send values to SQL database.
    def send_sql(self):
        # TODO: Check rollback command. Until when and what will be rolled back?
        # TODO: Check sql format for time and date.
        # Check if values for writing are present.
        if not self.values:
            logging.debug('No values to send to sql server.')
            return

        # Set up db write string.
        db_string = f'INSERT INTO {self.db_table_name} (time, '

        # Example for DB connection.
        # sensor = Adafruit_DHT.DHT22
        # pin = 4
        # self.db = MySQLdb.connect("localhost", "root", "passwort", "haus")
        # self.db_curs = self.db.cursor()
        #
        # try:
        #     humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
        #     curs.execute(
        #         "INSERT INTO temperatur_tb (datum, uhrzeit, wert) VALUES (CURRENT_DATE(), NOW(), %.2f);" % temperature)
        #     db.commit()
        #     print("Done")
        # except:
        #     print("Error. Rolling back.")
        #     db.rollback()

    def send_thingspeak(self):
        # Check sending interval.
        if time.time() - self.thingspeak_last_send < self.thingspeak_interval:
            logging.debug('Thingspeak attempt below interval.')
            return

        # Check if values for writing are present.
        if not self.values:
            logging.debug('No values to send to thingspeak.')
            return

        # Setup dicts for channel update.
        out_dicts = [{}] * len(self.thingspeak_channels)
        for val in self.values:
            # Check if channel and field are specified, otherwise skip.
            if None in [self.channels[val]['thingspeak_channel'], self.channels[val]['thingspeak_field']]:
                continue

            # Get channel and field number.
            channel_nr = self.channels[val]['thingspeak_channel']
            field_nr = self.channels[val]['thingspeak_field']

            # Add the value to the right dict.
            out_dicts[channel_nr][f'field{field_nr}'] = self.values[val]

        # Update channels.
        for ch_id, ch in enumerate(self.thingspeak_channels):
            if out_dicts[ch_id]:
                result = ch.update(out_dicts[ch_id])
                if result != "0":
                    self.thingspeak_last_send = time.time()

    def telemetry_loop(self):
        sleep_time_max = 1 / self.options['query_frequency']

        # Setup thingspeak channel object.
        if self.options['do_send_thingspeak']:
            for ch_id, ch in enumerate(self.options['thinkspeak_channel_ids']):
                self.thingspeak_channels.append(thingspeak.Channel(id=self.options['thinkspeak_channel_ids'][ch_id],
                                                                   api_key=self.options['thingspeak_keys_write'][ch_id]))

        # Start loop.
        while True:
            # Start run timer.
            run_time_start = time.time()

            # Get values for each datasource.
            self.get_values()

            # Write values to file.
            if self.options['do_log']:
                self.write_to_file()

            # Send values to db.
            if self.options['do_send_sql']:
                self.send_sql()

            if self.options['do_send_thingspeak']:
                self.send_thingspeak()

            # Get runtime, sleeptime and sleep until next execution.
            run_time = time.time() - run_time_start
            sleep_time = sleep_time_max - run_time
            if sleep_time < 0:
                sleep_time = 0
            time.sleep(sleep_time)


if __name__ == '__main__':
    tele = AutoTelemetry()
    tele.read_channel_config()

    tele.add_datasource('obd')
    # tele.add_datasource('r3e')
    # tele.add_datasource('rnd')

    tele.telemetry_loop()

    breakpoint()
