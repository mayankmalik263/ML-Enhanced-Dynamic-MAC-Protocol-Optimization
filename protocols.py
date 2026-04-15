import simpy
import random

class Packet:
    def __init__(self, sender, dest, packet_id, p_type="DATA", size=1500):
        self.sender = sender
        self.dest = dest
        self.packet_id = packet_id
        self.p_type = p_type 
        self.size = size

class SlottedAlohaProtocol:
    def __init__(self, node, slot_length=0.001):
        self.node = node
        self.env = node.env
        self.slot_length = slot_length

    def attempt_transmission(self, packet):
        self.env.process(self._tx_process(packet))

    def _tx_process(self, packet):
        current_time = self.env.now
        time_to_boundary = self.slot_length - (current_time % self.slot_length)
        yield self.env.timeout(time_to_boundary)
        self.node.channel.broadcast(sender=self.node, packet=packet)

    def handle_incoming_signal(self, packet):
        pass


class CSMACaProtocol:
    def __init__(self, node, difs=0.00005, slot_time=0.00002):
        self.node = node
        self.env = node.env
        self.difs = difs
        self.slot_time = slot_time
        
        self.channel_busy = False
        self.cw_min = 32
        self.cw_max = 1024
        self.cw = self.cw_min

    def attempt_transmission(self, packet):
        self.env.process(self._tx_process(packet))

    def _tx_process(self, packet):
        yield self.env.timeout(self.difs)
        
        while self.channel_busy:
            backoff_slots = random.randint(1, self.cw)
            wait_time = backoff_slots * self.slot_time
            yield self.env.timeout(wait_time)
            
            # Equation 4 from IEEE Paper: Binary Exponential Backoff
            self.cw = min(self.cw * 2, self.cw_max)
            
            yield self.env.timeout(self.difs)

        self.node.channel.broadcast(sender=self.node, packet=packet)
        # Reset CW upon successful transmission sequence
        self.cw = self.cw_min

    def handle_incoming_signal(self, packet):
        self.channel_busy = True
        packet_duration = packet.size * 8 / 1_000_000 
        self.env.process(self._clear_channel(packet_duration))
        
    def _clear_channel(self, delay):
        yield self.env.timeout(delay)
        self.channel_busy = False