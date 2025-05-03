import socket
import sys
import glob
import os
import time
import csv
import traceback
from threading import Thread

host = "127.0.0.1"
packets_table = "input/packets.csv"

# The purpose of this function is to perform a bitwise NOT on an unsigned integer.
def bit_not(n, numbits=32):
    return (1 << numbits) - 1 - n

# The purpose of this function is to setup a socket connection.
def create_socket(host, port):
    # 1. Create a socket
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 2. Try connecting the socket to the host and port.
    try:
        soc.connect((host, port))
    except Exception as e:
        print(f"Connection Error to port {port}: {e}")
        sys.exit()
    
    # 3. Return the connected socket.
    return soc

# The purpose of this function is to read in a CSV file.
def read_csv(path):
    # 1. Open the file for reading.
    table_file = open(path, 'r')
    # 2. Store each line.
    table = table_file.readlines()
    # 3. Create an empty list to store each processed row.
    table_list = []
    # 4. For each line in the file:
    for line in table:
        # 5. split it by delimeter.
        elements = line.strip().split(",")
        # 6. Remove any leading or trailing spaces in each element, and
        cleaned_elements = [element.strip() for element in elements]
        # 7. append the resulting list to table_list
        table_list.append(cleaned_elements)
    # 8. Close the file and return the table_list
    table_file.close()
    return table_list

# The purpose of this function is to find the default port 
# when no match is found in the forwarding table for a packet's destination IP.
def find_default_gateway(table):
    # 1. Traverse the table, row by row,
    for row in table:
        # 2. and if the network destination of that row matches 0.0.0.0,
        
        if row[0] == "0.0.0.0":
            # 3. then return the interface of that row.
            if row[3].isdigit():
                return row[3]
            
# The purpose of this function is to find the range of IPs inside a given destination IP address/subnet mask pair.
def find_ip_range(network_dst, netmask):
    # 1. Perform a bitwise AND on the network destination and netmask
    # to get the minimum IP address in the range.
    bitwise_and = network_dst & netmask
    
    # 2. Perform a bitwise NOT on the netmask
    # to get the number of total IPs in this range.
    compliment = bit_not(netmask)
    min_ip = bitwise_and
    
    # 3. Add the total number of IPs to the minimum IP
    # to get the maximum IP address in the range.
    max_ip = min_ip + compliment
    
    # 4. Return a list containing the miniumum and maximum IP in the range.
    return [min_ip, max_ip]
        
# The purpose of this function is to convert a string IP to its binary representation.
def ip_to_bin(ip):
    # 1. Split the IP into octets.
    ip_octets = ip.strip().split(".")
    # 2. Create an empty string to store each binary octet.
    ip_bin_string = ""
    # 3. Traverse the IP, octet by octet
    for octet in ip_octets:
        # 4. and convert the octet to an int,
        int_octet = int(octet)
        # 5. convert the decimal int to binary,
        bin_octet = bin(int_octet)[2:]
        # 6. pad the binary representation to ensure it's 8 bits long
        bin_octet_string = bin_octet.zfill(8)
        # 7. Append the binary octet to ip_bin_string.
        ip_bin_string += bin_octet_string
    # 8. Convert the binary string to an integer
    ip_int = int(ip_bin_string, 2)
    # 9. Return the binary representation of this int.
    return ip_int
        
# The purpose of this function is to generate a forwarding table that includes the IP range for a given interface.
# In other words, this table will help the router answer the question:
# Given this packet's destination IP, which interface (i.e., port) should I send it out on?
def generate_forwarding_table_with_range(table):
    # 1. Create an empty list to store the new forwarding table.
    new_table = []
    # 2. Traverse the old forwarding table row by row
    for row in table:
        # 3. and process each network destination other than 0.0.0.0
        if row[0] != "0.0.0.0":
            try:
                # 4. Store the network destination and netmask.
                network_dst_string = row[0]
                netmask_string = row[1]
                
                # 5. Convert both string into their binary representations.
                network_dst_bin = ip_to_bin(network_dst_string)
                netmask_bin = ip_to_bin(netmask_string)
                
                # 6. Find the IP range.
                ip_range = find_ip_range(network_dst_bin, netmask_bin)
                
                # Get interface
                interface = row[3]
                
                # Build new row
                new_row = [ip_range, interface]
                
                # 8. Append the new row to new_table.
                new_table.append(new_row)
            except ValueError:
                continue
    # 9. Return the new table
    return new_table

# The purpose of this function is to receive and process an incoming packet.
def receive_packet(router_id, connection, max_buffer_size):
    data = connection.recv(max_buffer_size)
    packet_size = sys.getsizeof(receive_packet)
    if packet_size > max_buffer_size:
        print(f"The packet size is greater than expected. {packet_size}")
        
    decoded_packet = data.decode("utf-8").strip()
    if not decoded_packet or decoded_packet.count(",") != 3:
        print(f"Skipping invalid packet: '{decoded_packet}'")
        return []
    print(f"Received packet, {decoded_packet}")
    write_to_file(f"output/received_by_router_{router_id}.txt", decoded_packet)
    packet = decoded_packet.split(",")
    return packet if len(packet) == 4 else []

# The purpose of this function is to write packets/payload to file.
def write_to_file(path, packet_to_write, send_to_router=None):
    # 1. Open the output file for appending.
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out_file = open(path, "a")
    # 2. If this router is not sending, then just append the packet to the output file.
    if send_to_router is None:
        out_file.write(packet_to_write + "\n")
    # 3. Else if this router is sending, then append the intended recipient, along with the packet, to the output file.
    else:
        out_file.write(packet_to_write + " " + "to Router " + send_to_router + "\n")
    # 4. Close the output file.
    out_file.close()
                 
# The purpose of this function is to find the next destination for the packet                 
def find_next_hop(packet, socket_to_dest_router_1, socket_to_dest_router_2, forwarding_table_with_range, default_gateway_port, router_id, dest_router_1, dest_port_1, dest_router_2, dest_port_2):
    
    if not packet or len(packet) < 4:
        print(f"invalid packet structure: {packet}")
        return
    
    source_ip = packet[0]
    destination_ip = packet[1]
    payload = packet[2]
    ttl = int(packet[3])
    
    new_ttl = ttl - 1
    new_packet = f"{source_ip},{destination_ip},{payload},{new_ttl}"
    destination_ip_bin = ip_to_bin(destination_ip)
    
    chosen_interface = None
    is_final_hop = False
    
    for row in forwarding_table_with_range:
        ip_range, interface = row
        try:
            if ip_range[0] <= destination_ip_bin <= ip_range[1]:
                if interface == host:
                    print(f"OUT: {payload}")
                    write_to_file(f"output/out_router_{router_id}.txt", payload)
                    return
                else:
                    chosen_interface = int(interface)
                    break
        except ValueError:
            continue
        
    if not is_final_hop and not chosen_interface:
        chosen_interface = default_gateway_port
        
    if new_ttl <= 0:
        print(f"DISCARD: {new_packet}")
        write_to_file(f"output/discarded_by_router_{router_id}.txt", new_packet)
    elif is_final_hop:
        print(f"OUT: {payload}")
        write_to_file(f"output/out_router_{router_id}.txt", payload)
    elif chosen_interface == dest_port_1 and socket_to_dest_router_1:
        print(f"Sending packet {new_packet} to Router {dest_router_1}")
        socket_to_dest_router_1.sendall(new_packet.encode("utf-8"))
        write_to_file(f"output/sent_by_router_{router_id}.txt", new_packet, str(dest_router_1))
    elif chosen_interface == dest_port_2 and socket_to_dest_router_2:
        print(f"Sending packet {new_packet} to Router {dest_router_1}")
        socket_to_dest_router_2.sendall(new_packet.encode("utf-8"))
        write_to_file(f"output/sent_by_router_{router_id}.txt", new_packet, str(dest_router_2))
    else:
        print(f"OUT: {payload}")
        write_to_file(f"output/out_router_{router_id}.txt", payload)
                                
# The purpose of this function is to receive and process incoming packets.
def processing_thread(router_id, connection=None, forwarding_table_with_range=None, default_gateway_port=None, dest_router_1=None, dest_port_1=0, dest_router_2=None, dest_port_2=0, max_buffer_size=5120):
    
    # Create sockets
    socket1 = create_socket(host, dest_port_1) if dest_port_1 > 0 else None
    socket2 = create_socket(host, dest_port_2) if dest_port_2 > 0 else None
    
    # If it's not the starting router
    if int(router_id) > 1:
        # While there are incoming packets
        while True:
            # Retrieve the incoming packet
            packet = receive_packet(router_id, connection, max_buffer_size)
            
            # If packet was retrieved
            if not packet:
                break
            
            # Find the next destination for the packet
            find_next_hop(packet, socket1, socket2, forwarding_table_with_range, default_gateway_port, router_id, dest_router_1, dest_port_1,  dest_router_2, dest_port_2)
    # This is router 1 where the packages are read and sent from
    else:
        
        for packet in read_csv(packets_table):
            
            # Find the next destination for the packet
            find_next_hop(packet, socket1, socket2, forwarding_table_with_range, default_gateway_port, router_id, dest_router_1, dest_port_1, dest_router_2, dest_port_2)
            
            time.sleep(1)
            
# The purpose of this function is to start the server.
def start_server(router_id: str, router_port=0, dest_router_1=None,  dest_port_1=0, dest_router_2=None, dest_port_2=0):
    table_path = f"input/router_{router_id}_table.csv"
    
    forwarding_table = read_csv(table_path)
    default_gateway_port = find_default_gateway(forwarding_table)
    forwarding_table_with_range = generate_forwarding_table_with_range(forwarding_table)
    
    if int(router_id) > 1:
        port = router_port
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Socket Created for Router " + router_id)
        try:
            soc.bind((host, port))
        except:
            print(f"Bind failed. Error: {str(sys.exc_info())}")
            sys.exit()
        soc.listen(5)
        print(f"Socket now listening on port: {port}")
        
        while True:
            connection, address = soc.accept()
            ip, port = address[0], str(address[1])
            print(f"Connected with {ip} : {port}")
            try:
                Thread(target=processing_thread, args=(router_id, connection,forwarding_table_with_range, default_gateway_port, dest_router_1, dest_port_1, dest_router_2, dest_port_2)).start()
            except:
                print("Thread did not start.")
                traceback.print_exc()
    else:
        processing_thread(router_id=router_id, forwarding_table_with_range=forwarding_table_with_range, dest_router_1=dest_router_1, dest_port_1=dest_port_1, dest_router_2=dest_router_2, dest_port_2=dest_port_2)