import random
import time
from math import sin


class DatasourceRnd:

    def __init__(self):
        self.channels = {}
        self.values = {}

    # Init random factors for all assigned channels.
    def init_random(self):
        for ch_id, ch in enumerate(self.channels):
            if 'rnd' in self.channels[ch]['src_prio']:
                # Get two random factors: amplitude and phase shift.
                # Initialise for amplitude using the channel name.
                random.seed(a=ch)
                amplitude = random.randint(-100, 100)

                # Initialise for phase shift using the channel id.
                random.seed(a=ch_id)
                phase_shift = random.random() * 15

                # Store the values.
                self.channels[ch]['rnd_factors'] = [amplitude, phase_shift]

    # Generate random values for all assigned channels.
    def get_values(self):
        # Re-Init values dict.
        self.values = {}

        # Loop over channels to get the random values.
        for ch in self.channels:
            if 'rnd_factors' in self.channels[ch]:
                amplitude = self.channels[ch]['rnd_factors'][0]
                phase_shift = self.channels[ch]['rnd_factors'][1]
                self.values[ch] = amplitude + sin((time.time() + phase_shift) / 15)

        # Return the values.
        return self.values
