# do not import anything else from loss_socket besides LossyUDP

from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from concurrent.futures import ThreadPoolExecutor
from threading import Timer
import threading
import time
import hashlib
import struct


class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port

        # Maintains the sequence number of the packet at the receiver's end
        self.receive_buffer = {}

        # Maintains the sequence number of the packet at the sender's end
        self.send_buffer = {}

        # Maintains the sequence number of the packet that have been sent and await acknowledgement from receiver's end
        self.sent_ack_buffer = {}

        # Maintains the current sequence number for both the hosts. It is incremented each time a new
        # packet is created and sent over the network
        self.curr_sequence_number = 0

        # The sequence number of the closing packet that would be sent out
        self.close_sequence_number = None

        # Boolean variable which maintains the status of receiving a FIN packet from the receiver
        self.closed_from_recv = False

        # Boolean variable which maintains the status of receiving an ACK FIN packet from the receiver
        self.closed_ack = False
        self.closed = False

        # Empty bytes string that is sent as a data in ACK, FIN, and ACK FIN packets
        self.empty_bytes = b''

        # A buffer which handles the queues smaller packets and sends them when queue is full
        # Used to implement Nagle's Algorithm
        self.nagle_send_buffer = self.empty_bytes

        # Maintains a previous version of the buffer which is used to check if
        # the application has sent all available data to the program
        self.old_data = self.empty_bytes

        # Timer to check if the buffer has reached the limit
        # Used to implement Nagle's Algorithm
        self.nagle_timer = threading.Timer(0.5, self.run_nagle_algo)  #

        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.listener)

    def send(self, data_bytes: bytes) -> None:
        """
        :param data_bytes: The data bytes received from the application that needs to be
        sent over the network
        :return: None

        The function receives all the data that needs to be sent over and adds it to the buffer.
        Upon receiving data from application, it triggers Nagle's Algorithm
        """
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        # for now I'm just sending the raw application-level data in one UDP payload

        self.nagle_send_buffer += data_bytes
        self.run_nagle_algo()

    def run_nagle_algo(self):
        """
        :return: None

        The method is called periodically from the timer and the send method.
        When there is no more data to be added to the buffer, the buffer is chunked into the smaller supported packet size.
        The checksum is calculated on the chunked data and appended at the beginning of packet bytes.
        The SEQ number is incremented and the program calls the retransmission logic for the packets.
        The chunk size is calculated as follows:
            Chunk size  = 1472 - 16(checksum bytes) - 4(sequence number bytes) - 2(boolean bytes for ACK and FIN)
                        = 1450 bytes


        """
        if self.nagle_send_buffer == self.empty_bytes:
            return

        chunk_size = 1450
        if self.old_data == self.nagle_send_buffer:
            # Cancel the timer at the time of sending the packets
            self.nagle_timer.cancel()
            segmented_bytes = [self.nagle_send_buffer[bytes_index:bytes_index + chunk_size] for bytes_index in
                               range(0, len(self.nagle_send_buffer), chunk_size)]

            for chunked_data in segmented_bytes:
                sequence_number = self.curr_sequence_number
                self.sent_ack_buffer[sequence_number] = False
                tcp_packet = self.create_tcp_packet(sequence_number, chunked_data, False, False)
                checksum = self.calculate_checksum(tcp_packet)
                tcp_packet = checksum + tcp_packet
                # print("Sending TCP Packet with SEQ = ", sequence_number)

                self.socket.sendto(tcp_packet, (self.dst_ip, self.dst_port))
                self.send_buffer[sequence_number] = tcp_packet
                Timer(0.25, self.handle_packet_retransmission, [sequence_number, tcp_packet]).start()
                self.curr_sequence_number += 1

        else:
            # Update the data buffer and start the timer again which would check in regular intervals
            # that the buffer has no more updates/additions
            self.old_data = self.nagle_send_buffer
            if not self.nagle_timer.is_alive():
                self.nagle_timer.start()

    @staticmethod
    def create_tcp_packet(sequence_header: int, data_bytes: bytes, is_ack: bool, is_fin: bool) -> bytes:
        """
        :param sequence_header: SEQ number of the packet
        :param data_bytes: Data bytes of the packet
        :param is_ack: Flag for the packet if it's an ACK packet
        :param is_fin: Flag for the packet if it's an FIN packet
        :return: TCP Packet in packed format

        Packing format -
            i = Integer
            ? = Boolean
            s = Bytes

        Packs the data into a format to send to the receiver.
        """
        packing_format = '!i??' + str(len(data_bytes)) + 's'
        return struct.pack(packing_format, sequence_header, is_ack, is_fin, data_bytes)

    @staticmethod
    def unpack_tcp_packet(received_bytes: bytes):
        """
        :param received_bytes: Data packet in packed format received from the sender
        :return: Unpacked format of data

        Unpacks the data into a format defined as received from the sender.
        """
        packing_format = '!i??' + str(len(received_bytes) - 6) + 's'
        return struct.unpack(packing_format, received_bytes)

    @staticmethod
    def calculate_checksum(packet_data: bytes):
        """
        :param packet_data: Data bytes on which the checksum needs to be calculated
        :return: MD5 hash of the bytes
        """
        return hashlib.md5(packet_data).digest()

    def send_tcp_ack_packet(self, sequence_header: int, data_bytes: bytes):
        """
        :param sequence_header: SEQ number of the packet
        :param data_bytes: Data bytes of the ACK packet
        :return: None

        Creates a TCP ACK packet for the data packet received from the sender.
        This packet is then sent back to the sender.
        is_ack flag is set to True.
        """
        tcp_ack_packet = self.create_tcp_packet(sequence_header, data_bytes, True, False)
        checksum = self.calculate_checksum(tcp_ack_packet)
        tcp_ack_packet = checksum + tcp_ack_packet
        # print("ACK SENT for SEQ = ", sequence_header)
        self.socket.sendto(tcp_ack_packet, (self.dst_ip, self.dst_port))

    def retransmit_pack(self, tcp_packet: bytes):
        """
        :param tcp_packet: TCP Packet to be retransmitted
        :return: None

        Retransmits the TCP packet which may have been lost / corrupted at the time of transfer.
        """
        self.socket.sendto(tcp_packet, (self.dst_ip, self.dst_port))

    def handle_packet_retransmission(self, sequence_number: int, tcp_packet: bytes):
        """
        :param sequence_number: TCP packet SEQ number
        :param tcp_packet: TCP packet containing the data, header and checksum
        :return: None

        If the ACK for the pack sent is not received within the time frame, the packet is retransmitted.
        It checks the ack_buffer which maintains the boolean status of the ACK for the packets that been sent.
        Is called every 0.25 seconds until an ACK packet is received against the SEQ number.
        """
        if self.closed:
            return
        if not self.sent_ack_buffer[sequence_number]:
            try:
                self.retransmit_pack(tcp_packet)
            except Exception as e:
                print("Exception = ", e)
            else:
                # print("Retransmitting Hit. Sending packet again with SEQ = ", sequence_number)
                Timer(0.25, self.handle_packet_retransmission, [sequence_number, tcp_packet]).start()
        else:
            # When the ACK is received, delete its entry from ack_buffer
            del self.sent_ack_buffer[sequence_number]

    def send_close_packet(self, sequence_number: int, data_bytes: bytes):
        """
        :param sequence_number: SEQ number of the FIN packet
        :param data_bytes: Data bytes of the packet
        :return: None

        Once the transmission is complete from the machine/host's end,
        FIN packet is sent indicating the closing of the transmission.
        is_fin flag is set as true
        """
        tcp_close_packet = self.create_tcp_packet(sequence_number, data_bytes, False, True)
        checksum = self.calculate_checksum(tcp_close_packet)
        tcp_ack_packet = checksum + tcp_close_packet
        self.socket.sendto(tcp_ack_packet, (self.dst_ip, self.dst_port))

    def send_close_ack_packet(self, sequence_number: int, data_bytes: bytes):
        """
        :param sequence_number: SEQ number of  ACK FIN packet
        :param data_bytes: Data bytes of the packet
        :return: None

        Upon receiving a FIN packet, an ACK FIN packet is sent back and the connection close process is started
        """
        tcp_close_ack_packet = self.create_tcp_packet(sequence_number, data_bytes, True, True)
        checksum = self.calculate_checksum(tcp_close_ack_packet)
        tcp_ack_packet = checksum + tcp_close_ack_packet
        self.socket.sendto(tcp_ack_packet, (self.dst_ip, self.dst_port))

    def recv(self) -> bytes:
        """
        :return: The data received from the sender

        Continuously runs to listen to any data which is received.
        Maintains the order by using the curr_sequence_number which increments and returns data back to the application
        only when the packet data in the receive buffer is in correct order.
        """

        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        # this sample code just calls the recvfrom method on the LossySocket
        while True:
            if self.curr_sequence_number in self.receive_buffer:
                data = self.receive_buffer[self.curr_sequence_number]
                del self.receive_buffer[self.curr_sequence_number]
                self.curr_sequence_number += 1
                return data
            else:
                # If the buffer is empty or the correct order packet is yet to be received the program waits
                time.sleep(0.1)

    def listener(self):
        """
        :return: None

        A thread function which continuously listens for data being received
        Handles the unpacking, checksum matching, closing of connection, and packet parsing function
        """
        while not self.closed:  # a later hint will explain self.closed
            try:
                received_data, address = self.socket.recvfrom()
                if len(received_data) == 0:
                    continue

                packet_check_sum = received_data[0:16]
                received_data = received_data[16:]
                if received_data == b'':
                    continue
                tcp_packet = self.unpack_tcp_packet(received_data)
                packet_seq_number = tcp_packet[0] # Packet SEQ number
                is_ack = tcp_packet[1] # ACK flag in the packet
                is_fin = tcp_packet[2] # FIN flag in the packet
                data_bytes = tcp_packet[3]

                # print("TCP PACKET received SEQ = ", packet_seq_number, "IS ACK = ", is_ack, "IS FIN = ", is_fin)

                computed_check_sum = self.calculate_checksum(received_data)
                # Matching the checksum to ensure data bytes are not corrupted. Packet is ignored if it is corrupted
                if packet_check_sum != computed_check_sum:
                    # print("Received TCP Packet with corrupted data for SEQ number = ", packet_seq_number)
                    continue

                if is_ack and is_fin:
                    # Packet is ACK FIN packet
                    self.closed_ack = True
                    # print("ACK FIN received")

                elif is_ack:
                    # Packet is ACK packet
                    self.sent_ack_buffer[packet_seq_number] = True
                    # print("Received ACK from other machine for SEQ = ", packet_seq_number)

                elif is_fin:
                    # Packet is FIN packet
                    data = b'-1'
                    self.send_close_ack_packet(packet_seq_number, data)
                    self.closed_from_recv = True
                    # print("FIN packet received")

                else:
                    # Packet is Data packet
                    ack_data = b'-1'
                    # print("Data packet received with SEQ = ", packet_seq_number)

                    # ACK is sent with a timer of 0.05 seconds
                    Timer(0.05, self.send_tcp_ack_packet, [packet_seq_number, ack_data]).start()
                    if packet_seq_number not in self.receive_buffer:
                        # Packet is added to receive buffer if it is not previously present
                        # This may be the case when the packet is retransmitted when the intended ACK is lost
                        self.receive_buffer[packet_seq_number] = data_bytes
                        # print("Sending ACK for SEQ = ", packet_seq_number)

            except Exception as e:
                print("listener died!")
                print(e)
        return True

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.

        # If there are packets in the nagle buffer still waiting to be transmitted, the program goes to sleep
        while self.nagle_timer.is_alive():
            time.sleep(1)

        # If there are packets which are yet to receive their ACK, the program waits before closing
        # the connection
        while len(self.sent_ack_buffer) != 0:
            time.sleep(0.05)

        is_fin_packet_transmitted = False
        close_data_bytes = b'-1'
        self.close_sequence_number = self.curr_sequence_number
        while True:
            # If FIN packet and FIN ACK is received, then close the socket connection
            if self.closed_from_recv and self.closed_ack:
                break

            if not is_fin_packet_transmitted:
                self.send_close_packet(self.close_sequence_number, close_data_bytes)
                packet_send_time = time.time()
                is_fin_packet_transmitted = True
                # print("Sending FIN packet")
            else:
                # Retransmission logic for FIN packet after 0.25 seconds
                if time.time() - packet_send_time >= 0.25:
                    # print("Sending FIN packet")
                    self.send_close_packet(self.close_sequence_number, close_data_bytes)
                    packet_send_time = time.time()

        # Closing the connection and giving 2 seconds to perform any tasks currently ongoing before closing the socket
        time.sleep(2)
        self.closed = True
        self.socket.stoprecv()
        time.sleep(1)
        self.socket.close()

