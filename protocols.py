import simpy
import random

# --- PACKET DEFINITIONS ---
class Packet:
    def __init__(self, sender, dest, packet_id, p_type="DATA", size=1500): # <-- packet_id MUST be right here
        self.sender = sender
        self.dest = dest
        self.packet_id = packet_id
        self.p_type = p_type 
        self.size = size

class SlottedAlohaProtocol:
    """
    Slotted ALOHA restricts transmissions to specific time boundaries.
    """
    def __init__(self, node, slot_length=0.001):
        self.node = node
        self.env = node.env
        self.slot_length = slot_length

    def attempt_transmission(self, packet):
        """
        Spawns a SimPy process to handle the transmission timing.
        """
        self.env.process(self._tx_process(packet))

    def _tx_process(self, packet):
        # 1. Calculate time until the next exact slot boundary
        current_time = self.env.now
        time_to_boundary = self.slot_length - (current_time % self.slot_length)
        
        # 2. Wait until the slot begins (yield pauses this specific function)
        yield self.env.timeout(time_to_boundary)
        
        # 3. Yell into Mayank's physical channel
        self.node.channel.broadcast(sender=self.node, packet=packet)
        print(f"[{self.env.now:.6f}] MAC (ALOHA): Node {self.node.node_id} transmitted in slot boundary.")

    def handle_incoming_signal(self, packet):
        # ALOHA doesn't carrier sense, it only cares if it gets an ACK back.
        # For this simulation, collision calculation is usually centralized at the receiver.
        pass


class CSMACaProtocol:
    """
    CSMA/CA with simplified Carrier Sensing and Backoff.
    """
    def __init__(self, node, difs=0.00005, slot_time=0.00002):
        self.node = node
        self.env = node.env
        self.difs = difs           # Distributed Inter-Frame Space (Wait time before sending)
        self.slot_time = slot_time # Time slot for random backoff
        
        # State variables
        self.channel_busy = False  # Updated physically by the antenna
        self.cw = 4                # Contention Window (starts small)

    def attempt_transmission(self, packet):
        self.env.process(self._tx_process(packet))

    def _tx_process(self, packet):
        # Step 1: Wait for DIFS (Standard quiet period)
        yield self.env.timeout(self.difs)
        
        # Step 2: Carrier Sense & Backoff
        while self.channel_busy:
            # If busy, pick a random backoff time based on Contention Window
            backoff_slots = random.randint(1, self.cw)
            wait_time = backoff_slots * self.slot_time
            print(f"[{self.env.now:.6f}] MAC (CSMA): Node {self.node.node_id} sensed busy channel. Backing off for {wait_time:.6f}s.")
            
            yield self.env.timeout(wait_time)
            
            # Increase contention window exponentially on failure (Binary Exponential Backoff)
            self.cw = min(self.cw * 2, 1024) 
            
            # Wait DIFS again before re-sensing
            yield self.env.timeout(self.difs)

        # Step 3: Channel is free, transmit RTS or DATA
        # (In a full implementation, you send RTS here, wait for CTS, then send DATA. 
        # We broadcast DATA directly here to integrate simply with Mayank's current channel).
        print(f"[{self.env.now:.6f}] MAC (CSMA): Node {self.node.node_id} sensed idle channel. Transmitting.")
        self.node.channel.broadcast(sender=self.node, packet=packet)
        
        # Reset Contention Window after successful transmit
        self.cw = 4

    def handle_incoming_signal(self, packet):
        """
        Called by Mayank's NetworkNode when RF energy hits the antenna.
        """
        # When a signal is physically received, the MAC layer marks the channel as busy.
        # In a real simulation, this would stay busy for the duration of the packet transmission.
        self.channel_busy = True
        
        # For simulation simplicity, we simulate the channel clearing after the packet time
        packet_duration = packet.size * 8 / 1_000_000 # Assuming 1 Mbps rate
        self.env.process(self._clear_channel(packet_duration))
        
    def _clear_channel(self, delay):
        yield self.env.timeout(delay)
        self.channel_busy = False