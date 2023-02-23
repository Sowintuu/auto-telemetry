import os
import logging
import json
import MySQLdb
from datetime import datetime

from r3e_receive import R3eReceive


class AutoTelemetry(object):

    def __init__(self, logfile_dir=''):
        # Init attributes.
        # Values.
        self.values = {}

        # Datasource.
        self.datasource_type = 0
        self.datasource_obj = None
        self.config = {}

        # Database.
        self.db = None
        self.db_curs = None
        self.db_address = 'localhost'
        self.db_password = 'Laendle_MS_sql'
        self.db_name = 'laendle_ms'
        self.db_table_name = ''

        # Datalogging.
        self.logfile_path = ''
        self.logfile_dir = logfile_dir
        self.get_logfile_path()

        # Init logging.
        logging.basicConfig(format='%(asctime)s %(message)s',
                            filename='auto.log',
                            level=logging.DEBUG)

    # Set logfile path from logfile dir and current time.
    # If logfile path is not set yet, set it too.
    def get_logfile_path(self):
        # Get logfile path if not set already.
        if not self.logfile_dir:
            if not self.logfile_dir and os.name == 'nt':
                self.logfile_dir = 'logs'
            else:
                self.logfile_dir = '/home/pi/telemetry/'#

        # Create directory, if not already exists.
        if os.path.isdir(self.logfile_dir):
            os.makedirs(self.logfile_dir)

        # Set the logfile path.
        self.logfile_path = os.path.join(self.logfile_dir, datetime.now().strftime("%y%m%d_%H%M%S_tele.dat"))

    def read_channel_config(self):
        with open(r'..\socket_map.json') as json_file:
            self.config = json.load(json_file)

    def connect_sql(self):
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
            for val in self.config['cannels']:
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
            logging.info(f'Datasource "{source}" unknown.')

    # Get values from any type of datasource.
    def get_values(self):
        # Check if datasource was set.
        if self.datasource_obj is None:
            logging.warning('Set datasource first before asking for values.')
            return

        # Get values from whatever datasource is set.
        self.values = self.datasource_obj.get_values()

    def log_and_send(self):
        # TODO: Check rollback command. Until when and what will be rolled back?
        # TODO: Check sql format for time and date.
        # Log locally.
        # Set string for logging.
        log_string = ''
        for var in self.values:
            log_string += f'{var}:{self.values["var"]},'
        log_string.strip(',')
        log_string += '\n'

        # Write string to file.
        with open(self.logfile_path, 'a') as logfile:
            logfile.write(log_string)

        # Log to DB.
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


if __name__ == '__main__':
    tele = AutoTelemetry()
    tele.read_channel_config()
