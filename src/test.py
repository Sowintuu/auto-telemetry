import thingspeak

channel = thingspeak.Channel(id=2049894, api_key='2I1FRXHC9L811Z09')

response = channel.update({'field1': 45,
                           'field2': 50,
                           'field3': 50,
                           'field4': 5,
                           'field5': 70})

print(response)