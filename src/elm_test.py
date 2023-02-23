import obd

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

# Print supported commands.
if elm_connected:
    print(connection.supported_commands)

    for cmd in connection.supported_commands:
        print(f'{cmd.name} ¦ {cmd.desc}')

breakpoint()
