import obd
import time

# Connect to ELM
# obd.logger.setLevel(obd.logging.DEBUG)
connection = obd.OBD()

# Check status.
elm_status = connection.status()

elm_connected = False
if elm_status == obd.OBDStatus.CAR_CONNECTED:
    print('Connection successful.')
    elm_connected = True
elif elm_status == obd.OBDStatus.OBD_CONNECTED:
    print('Connected, but ignition off.')
elif elm_status == obd.OBDStatus.ELM_CONNECTED:
    print('Connected to ELM, but not to car.')
else:
    print('Connection failed.')

if elm_connected:
    # Print supported commands.
    for cmd in connection.supported_commands:
        print(f'{cmd.name} ¦ {cmd.desc}')

    print('n')

    # Setup commands.
    COMMANDS = {obd.commands.ACCELERATOR_POS_E: 'ACCELERATOR_POS_E',
                obd.commands.ACCELERATOR_POS_D: 'ACCELERATOR_POS_D',
                obd.commands.SPEED: 'SPEED',
                obd.commands.AMBIANT_AIR_TEMP: 'TEMP'
                }

    # Print values.
    # Init print str len to 0 for first run.
    print_str_len = 0
    while True:
        # Setup print string.
        print_str = ''

        # Get each response and print.
        for cmd in COMMANDS:
            response = connection.query(cmd)
            print_str += f'{COMMANDS[cmd]}: {response.value.magnitude} | '

        # Delete last printed string.
        print('\b' * (print_str_len + 1), end='')

        # Print string.
        print_str_len = len(print_str)
        print(print_str, end='')

        # Wait for next query.
        time.sleep(0.1)
