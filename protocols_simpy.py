import random

class SlottedAlohaProtocol:
    def __init__(self, env, node_id, channel, slot_time=1.0):
        self.env = env
        self.node_id = node_id
        self.channel = channel
        self.slot_time = slot_time

    def run(self, packet_generator):
        """Main loop for Slotted ALOHA."""
        while True:
            # Wait for a packet to be available in the node's queue
            packet = yield packet_generator.get()
            
            success = False
            while not success:
                # 1. Sync to the next slot boundary
                time_until_next_slot = self.slot_time - (self.env.now % self.slot_time)
                yield self.env.timeout(time_until_next_slot)

                # 2. Attempt transmission via the shared channel
                # We yield to the channel's transmit process which handles collisions
                success = yield self.env.process(self.channel.transmit(packet, self.node_id))

                if not success:
                    # 3. Collision: Backoff by a random number of slots
                    backoff_slots = random.randint(1, 4)
                    yield self.env.timeout(backoff_slots * self.slot_time)

class CSMACaProtocol:
    def __init__(self, env, node_id, channel, difs=0.1, sifs=0.05):
        self.env = env
        self.node_id = node_id
        self.channel = channel
        self.difs = difs  # Distributed Inter-Frame Spacing (Initial wait)
        self.sifs = sifs  # Short Inter-Frame Spacing (Wait between RTS/CTS/Data)

    def run(self, packet_generator):
        """Main loop for CSMA/CA with RTS/CTS."""
        while True:
            packet = yield packet_generator.get()
            
            success = False
            while not success:
                # 1. Sensing: Wait until the channel is idle for 'difs' amount of time
                while self.channel.is_busy():
                    yield self.env.timeout(0.1) # Check again shortly
                yield self.env.timeout(self.difs)

                # 2. RTS/CTS Handshake
                # Send RTS and wait for CTS response
                rts_success = yield self.env.process(self.channel.request_reservation(self.node_id))
                
                if rts_success:
                    # 3. Data Transmission (Channel is now reserved)
                    yield self.env.timeout(self.sifs)
                    success = yield self.env.process(self.channel.transmit(packet, self.node_id))
                    # 4. Post-transmission ACK wait
                    yield self.env.timeout(self.sifs)
                else:
                    # 5. Handshake failed (Collision or Hidden Terminal busy)
                    backoff = random.uniform(0.1, 1.0)
                    yield self.env.timeout(backoff)
