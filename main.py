import os
import socket
import sys
import threading
import time
import zlib

Format = 'utf-8'
Port_client = 1234

wrong_fragments = [2]

Server_thread = False
stop_event = threading.Event()


Thread_on = True

Check = True
stop_event.clear()


sec = 5


def print_the_message(final_message):
    message = ''.join(final_message)
    print(message)


def checksum(fragment):
    crc = zlib.crc32(fragment)
    return crc


def check_fragment_size():
    while True:
        try:
            fragment_size = int(input("Enter the size of the fragment (1-1459): "))
            if 1 <= fragment_size <= 1459:
                return fragment_size
            else:
                print("Invalid fragment size. Please enter a value between 1 and 1459.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


def create_header(flag, sequence_num, fragment_size, data, num_of_fragments):
    header = {
        'flag': flag,
        'sequence_num': sequence_num.to_bytes(3, 'big'),
        'fragment_size': fragment_size.to_bytes(2, 'big'),
        'checksum': checksum(data).to_bytes(4, 'big'),
        'num_of_fragments': num_of_fragments.to_bytes(3, 'big')
    }
    return header


def keep_alive(client_socket, server_address):
    global Thread_on, sec, Check
    counter = 0

    while Thread_on:
        if stop_event.is_set():
            Thread_on = False
            stop_event.set()
            Check = False
            break
        time.sleep(1)

        flag = 5

        header = create_header(flag, 0, 10, b"", 0)

        header_bytes = (
                bytes([header['flag']]) +
                header['sequence_num'] +
                header['fragment_size'] +
                header['checksum'] +
                header['num_of_fragments']
        )
        try:
            client_socket.sendto(header_bytes, server_address)
        except OSError:
            pass

        try:
            try:
                data, server_address = client_socket.recvfrom(2048)
            except OSError:
                print("Server is unreachable2")
                Thread_on = False
                stop_event.set()
                Check = False
                break
            if stop_event.is_set():
                Thread_on = False
                stop_event.set()
                Check = False
                break
            header = {
                'flag': int.from_bytes(data[:1], 'big'),
                'sequence_num': data[1:4],
                'fragment_size': data[4:6],
                'checksum': int.from_bytes(data[6:10], 'big'),
                'num_of_fragments': data[10:13]
            }

            if header['flag'] == 5:

                # print("KA reply from server")
                counter += 1

            if header['flag'] == 2:
                Thread_on = False
                stop_event.set()
                print("Server is off")

                counter = 0
        except socket.timeout or OSError:
            # counter += 1
            Thread_on = False
            stop_event.set()
            Check = False
            break

        if counter == 6:

            flag = 2

            header = create_header(flag, 0, 10, b"", 0)

            header_bytes = (
                    bytes([header['flag']]) +
                    header['sequence_num'] +
                    header['fragment_size'] +
                    header['checksum'] +
                    header['num_of_fragments']
            )
            try:
                client_socket.sendto(header_bytes, server_address)
            except OSError:
                print("Server is unreachable3")
            Thread_on = False
            print("No answer from server in 30 s")
            Thread_on = False
            stop_event.set()
            Check = False
            break

        if not stop_event.is_set():

            time.sleep(sec)

    sys.exit()



def switch_s_c(client_socket, seq_num, fragment_size, server_address):
    try:
        ack_data, _ = client_socket.recvfrom(2048)
    except OSError:
        print("Server is unreachable")
    ack_header = {
        'flag': int.from_bytes(ack_data[:1], 'big'),
        'sequence_num': ack_data[1:4],
        'fragment_size': ack_data[4:6],
        'checksum': int.from_bytes(ack_data[6:10], 'big'),
        'num_of_fragments': ack_data[10:13]
    }
    if ack_header['flag'] == 8:
        print("Switch request received from the server. "
              "Print \"y\" to confirm or anything else to continue as a client")
        sw_inp = input()
        if sw_inp == 'y':
            flag = 8

            header = create_header(flag, seq_num, fragment_size, b"", 0)

            header_bytes = (
                    bytes([header['flag']]) +
                    header['sequence_num'] +
                    header['fragment_size'] +
                    header['checksum'] +
                    header['num_of_fragments']
            )
            try:
                client_socket.sendto(header_bytes, server_address)
            except OSError:
                print("Server is unreachable")

            client_socket.close()
            print("Client socket was closed.")
            print("Switch request was send. Client was readdressed to server.")
            server()
        else:
            flag = 4

            header = create_header(flag, seq_num, fragment_size, b"", 0)

            header_bytes = (
                    bytes([header['flag']]) +
                    header['sequence_num'] +
                    header['fragment_size'] +
                    header['checksum'] +
                    header['num_of_fragments']
            )
            try:
                client_socket.sendto(header_bytes, server_address)
            except OSError:
                print("Server is unreachable")
            print("Continue in a client mode")


def client():
    global Thread_on, stop_event, Check
    Check = True
    stop_event.clear()
    IP_server = input("Enter server's IP: ")
    Port_server = int(input("Enter server's port: "))

    IP_client = socket.gethostbyname(socket.gethostname())

    while True:

        server_address = (IP_server, Port_server)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.bind((IP_client, Port_client))

        thread_ka = threading.Thread(target=keep_alive, args=(client_socket, server_address), daemon=True)
        # Thread_on = True
        # thread_ka.start()

        flag = 1
        seq_num = 1

        header = create_header(flag, seq_num, 0, b"", 0)

        header_bytes = (
                bytes([header['flag']]) +
                header['sequence_num'] +
                header['fragment_size'] +
                header['checksum']
        )
        try:
            client_socket.sendto(header_bytes, server_address)
        except OSError:
            print("Server's address is not valid. Return to the main menu.")
            client_socket.close()
            main_choice()
        try:
            data, server_address = client_socket.recvfrom(2048)
        except OSError:
            print("Server is unreachable")
        header = {
            'flag': int.from_bytes(data[:1], 'big'),
            'sequence_num': data[1:4],
            'fragment_size': data[4:6],
            'checksum': int.from_bytes(data[6:10], 'big'),
            'num_of_fragments': data[10:13]
        }

        if header['flag'] == 9:
            print("Connection established.")
            Thread_on = True
            stop_event.clear()
            thread_ka.start()
            # fragment_size = check_fragment_size()
            Check = True
            stop_event.clear()
            print()
            choice_c = input("Enter 1 to send a message\nEnter 2 to send a file\nEnter 3 to finish the program:\n")
            print()
            if not Check:
                client_socket.close()
                main_choice()

            if choice_c == '1':
                fragment_size = check_fragment_size()
                Thread_on = False
                stop_event.set()
                thread_ka.join()
                send_msg = input("Enter a message: ")


                fragments = []
                for i in range(0, len(send_msg), fragment_size):
                    fragment = send_msg[i:i + fragment_size]
                    fragments.append(fragment)
                if len(fragments[-1]) < fragment_size:
                    fragment_size = len(fragments[-1])
                    print(f"Fragment size was decreased to {fragment_size} for the last fragment")

                num_of_fragments = len(fragments)

                for seq_num, fragment in enumerate(fragments, start=1):
                    print(f"Sending fragment {seq_num} to the server")
                    send_fr = fragment.encode(Format)

                    flag = 7

                    header = create_header(flag, seq_num, fragment_size, send_fr, num_of_fragments)
                    if seq_num in wrong_fragments:
                        send_fr = bytes([0]) * 1 + send_fr[1:]

                    header_bytes = (
                            bytes([header['flag']]) +
                            header['sequence_num'] +
                            header['fragment_size'] +
                            header['checksum'] +
                            header['num_of_fragments']
                    )
                    try:
                        client_socket.sendto(header_bytes + send_fr, server_address)
                    except OSError:
                        print("Server is unreachable")
                    try:
                        ack_data, _ = client_socket.recvfrom(2048)
                    except OSError:
                        print("Server is unreachable")
                    ack_header = {
                        'flag': int.from_bytes(ack_data[:1], 'big'),
                        'sequence_num': ack_data[1:4],
                        'fragment_size': ack_data[4:6],
                        'checksum': int.from_bytes(ack_data[6:10], 'big'),
                        'num_of_fragments': ack_data[10:13]
                    }

                    if ack_header['flag'] == 3 and int.from_bytes(ack_header['sequence_num'], 'big') == seq_num:
                        print(f"ACK: fragment {seq_num} was received by server")
                    elif ack_header['flag'] == 4:
                        print(f"ACK: fragment {seq_num} was NOT received by server")
                        print(f"Sending fragment {seq_num} to the server")
                        send_fr = fragment.encode(Format)

                        flag = 7
                        header = create_header(flag, seq_num, fragment_size, send_fr, num_of_fragments)

                        header_bytes = (
                                bytes([header['flag']]) +
                                header['sequence_num'] +
                                header['fragment_size'] +
                                header['checksum'] +
                                header['num_of_fragments']
                        )
                        try:
                            client_socket.sendto(header_bytes + send_fr, server_address)
                        except OSError:
                            print("Server is unreachable")
                        try:
                            ack_data, _ = client_socket.recvfrom(2048)
                        except OSError:
                            print("Client is unreachable")
                        ack_header = {
                            'flag': int.from_bytes(ack_data[:1], 'big'),
                            'sequence_num': ack_data[1:4],
                            'fragment_size': ack_data[4:6],
                            'checksum': int.from_bytes(ack_data[6:10], 'big'),
                            'num_of_fragments': ack_data[10:13]
                        }

                        if ack_header['flag'] == 3 and int.from_bytes(ack_header['sequence_num'], 'big') == seq_num:
                            print(f"ACK: fragment {seq_num} was received by server")
                            continue
                print("All fragments sent")
                switch_s_c(client_socket, seq_num, fragment_size, server_address)
                Thread_on = True
                Check = True
                stop_event.clear()
                thread_ka = threading.Thread(target=keep_alive, args=(client_socket, server_address), daemon=True)
                thread_ka.start()
                if not Check:
                    client_socket.close()
                    main_choice()


            if choice_c == '2':
                fragment_size = check_fragment_size()
                Thread_on = False
                stop_event.set()
                thread_ka.join()
                filepath1 = "C:\\Users\\Acer\\Desktop\\fiit\\PKS\\comuniction over udp\\"
                filepath2 = input("Enter the path to the file: ")
                filepath = filepath1 + filepath2
                print(filepath)

                flag = 6

                header_filepath = create_header(flag, 0, 100, filepath2.encode(Format), 1)
                header_filepath_bytes = (
                        bytes([header_filepath['flag']]) +
                        header_filepath['sequence_num'] +
                        header_filepath['fragment_size'] +
                        header_filepath['checksum'] +
                        header_filepath['num_of_fragments']
                )
                try:
                    client_socket.sendto(header_filepath_bytes + filepath2.encode(Format), server_address)
                except OSError:
                    print("Server is unreachable")

                if not os.path.exists(filepath):
                    print("File not found")
                    return
                with open(filepath, 'rb') as file:
                    file_data = file.read()
                flag = 6

                fragments = []
                for i in range(0, len(file_data), fragment_size):
                    fragment = file_data[i:i + fragment_size]
                    fragments.append(fragment)

                if len(fragments[-1]) < fragment_size:
                    fragment_size = len(fragments[-1])
                    print(f"Fragment size was decreased to {fragment_size} for the last fragment")

                num_of_fragments = len(fragments)

                for seq_num, fragment in enumerate(fragments, start=1):
                    print(f"Sending fragment {seq_num} to the server")

                    header = create_header(flag, seq_num, fragment_size, fragment, num_of_fragments)
                    if seq_num in wrong_fragments:
                        header['checksum'] = bytes(0)

                    header_bytes = (
                            bytes([header['flag']]) +
                            header['sequence_num'] +
                            header['fragment_size'] +
                            header['checksum'] +
                            header['num_of_fragments']
                    )
                    try:
                        client_socket.sendto(header_bytes + fragment, server_address)
                    except OSError:
                        print("Server is unreachable")
                    try:
                        ack_data, _ = client_socket.recvfrom(2048)
                    except OSError:
                        print("Server is unreachable")
                    ack_header = {
                        'flag': int.from_bytes(ack_data[:1], 'big'),
                        'sequence_num': ack_data[1:4],
                        'fragment_size': ack_data[4:6],
                        'checksum': int.from_bytes(ack_data[6:10], 'big'),
                        'num_of_fragments': ack_data[10:13]
                    }

                    if ack_header['flag'] == 3 and int.from_bytes(ack_header['sequence_num'], 'big') == seq_num:
                        print(f"ACK: fragment {seq_num} was received by server")
                    elif ack_header['flag'] == 4:
                        print(f"ACK: fragment {seq_num} was NOT received by server")
                        print(f"Sending fragment {seq_num} to the server")
                        send_fr = fragment

                        flag = 6

                        header = create_header(flag, seq_num, fragment_size, send_fr, num_of_fragments)

                        header_bytes = (
                                bytes([header['flag']]) +
                                header['sequence_num'] +
                                header['fragment_size'] +
                                header['checksum'] +
                                header['num_of_fragments']
                        )
                        try:
                            client_socket.sendto(header_bytes + send_fr, server_address)
                        except OSError:
                            print("Server is unreachable")
                        try:
                            ack_data, _ = client_socket.recvfrom(2048)
                        except OSError:
                            print("Server is unreachable")
                        ack_header = {
                            'flag': int.from_bytes(ack_data[:1], 'big'),
                            'sequence_num': ack_data[1:4],
                            'fragment_size': ack_data[4:6],
                            'checksum': int.from_bytes(ack_data[6:10], 'big'),
                            'num_of_fragments': ack_data[10:13]
                        }

                        if ack_header['flag'] == 3 and int.from_bytes(ack_header['sequence_num'], 'big') == seq_num:
                            print(f"ACK: fragment {seq_num} was received by server")
                            continue
                print("All fragments sent")
                switch_s_c(client_socket, seq_num, fragment_size, server_address)
                Thread_on = True
                Check = True
                stop_event.clear()
                thread_ka = threading.Thread(target=keep_alive, args=(client_socket, server_address), daemon=True)
                thread_ka.start()
                if not Check:
                    client_socket.close()
                    main_choice()

            if choice_c == '3':
                Thread_on = False
                stop_event.set()
                thread_ka.join()
                flag = 2

                header = create_header(flag, seq_num, 0, b"", 0)

                header_bytes = (
                        bytes([header['flag']]) +
                        header['sequence_num'] +
                        header['fragment_size'] +
                        header['checksum'] +
                        header['num_of_fragments']
                )
                try:
                    client_socket.sendto(header_bytes, server_address)
                except OSError:
                    print("Server is unreachable")

                print("Close request was send to server.")
                client_socket.close()

                print("Client socket was closed.")
                sys.exit()

                # sys.exit()
            while True:
                print()
                choice_cl = input("Enter 1 to change the role\nEnter 2 to proceed in client mode\nEnter 3 to finish the program:\n")
                if choice_cl == '1':
                    Thread_on = False
                    stop_event.set()
                    thread_ka.join()
                    flag = 8

                    header = create_header(flag, seq_num, 0, b"", 0)

                    header_bytes = (
                            bytes([header['flag']]) +
                            header['sequence_num'] +
                            header['fragment_size'] +
                            header['checksum'] +
                            header['num_of_fragments']
                    )
                    try:
                        client_socket.sendto(header_bytes, server_address)
                    except OSError:
                        print("Server is unreachable")
                        continue
                    client_socket.close()
                    print("Client socket was closed.")
                    print("Switch request was send. Client was readdressed to server.")
                    server()

                elif choice_cl == '2':
                    Thread_on = False
                    Check = False
                    stop_event.set()
                    thread_ka.join()

                    client_socket.close()
                    break
                elif choice_cl == '3':
                    Thread_on = False
                    Check = False
                    stop_event.set()
                    thread_ka.join()
                    flag = 2

                    header = create_header(flag, seq_num, 0, b"", 0)

                    header_bytes = (
                            bytes([header['flag']]) +
                            header['sequence_num'] +
                            header['fragment_size'] +
                            header['checksum'] +
                            header['num_of_fragments']
                    )
                    try:
                        client_socket.sendto(header_bytes, server_address)
                    except OSError:
                        print("Server is unreachable")

                    print("Close request was send to server.")
                    client_socket.close()

                    print("Client socket was closed.")
                    sys.exit()


def input_thread(server_socket):
    global Server_thread
    while not Server_thread:
        choice_ser = input()
        if choice_ser == '1':
            server_socket.close()
            print("Server socket was closed")
            break
        else:
            pass


def switch_rep_s_c(final_message, seq_num, num_of_fragments, server_socket, client_address):
    final_message.clear()
    flag = 8
    ack_header = create_header(flag, seq_num, 0, b"", num_of_fragments)
    ack_header_bytes = (
            bytes([ack_header['flag']]) +
            ack_header['sequence_num'] +
            ack_header['fragment_size'] +
            ack_header['checksum'] +
            ack_header['num_of_fragments']
    )
    try:
        server_socket.sendto(ack_header_bytes, client_address)
    except OSError:
        print("Client is unreachable")
    print("Switch request was send to the client")


def server():
    global Server_thread
    Port_server = int(input("Enter the server's port: "))
    IP_server = socket.gethostbyname(socket.gethostname())
    server_address = (IP_server, Port_server)
    final_message = []
    received_fragments = {}
    total_received = 0
    expected = 0
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((IP_server, Port_server))

    input_thread_instance = threading.Thread(target=input_thread, args=(server_socket,), daemon=True)
    input_thread_instance.start()

    print(f"[LISTENING] Server is listening on {server_address}")

    while True:

        try:
            data, client_address = server_socket.recvfrom(2048)

            header = {
                'flag': int.from_bytes(data[:1], 'big'),
                'sequence_num': data[1:4],
                'fragment_size': data[4:6],
                'checksum': int.from_bytes(data[6:10], 'big'),
                'num_of_fragments': data[10:13]
            }

            if header['flag'] == 1:
                print(f"Connection request received from {client_address}")

                flag = 9
                sequence_num = 1
                fragment_size = 0
                header = create_header(flag, sequence_num, fragment_size, b"", 0)
                header_bytes = (
                        bytes([header['flag']]) +
                        header['sequence_num'] +
                        header['fragment_size'] +
                        header['checksum'] +
                        header['num_of_fragments']
                )
                try:
                    server_socket.sendto(header_bytes, client_address)
                except OSError:
                    print("Client is unreachable")

            if header['flag'] == 7:

                seq_num = int.from_bytes(header['sequence_num'], 'big')
                num_of_fragments = int.from_bytes(header['num_of_fragments'], 'big')

                if header['checksum'] == checksum(data[13:]):
                    print(f"Checksum verification successful for fragment {seq_num}.")
                    expected += 1

                    message_part = data[13:].decode(Format)

                    final_message.append(message_part)

                    flag = 3

                    ack_header = create_header(flag, seq_num, 0, b"", num_of_fragments)
                    ack_header_bytes = (
                            bytes([ack_header['flag']]) +
                            ack_header['sequence_num'] +
                            ack_header['fragment_size'] +
                            ack_header['checksum'] +
                            ack_header['num_of_fragments']
                    )
                    try:
                        server_socket.sendto(ack_header_bytes, client_address)
                    except OSError:
                        print("Client is unreachable")

                else:
                    print(f"Checksum verification failed for fragment {seq_num}")
                    flag = 4
                    ack_header = create_header(flag, seq_num, 0, b"", num_of_fragments)
                    ack_header_bytes = (
                            bytes([ack_header['flag']]) +
                            ack_header['sequence_num'] +
                            ack_header['fragment_size'] +
                            ack_header['checksum'] +
                            ack_header['num_of_fragments']
                    )
                    try:
                        server_socket.sendto(ack_header_bytes, client_address)
                    except OSError:
                        print("Client is unreachable")

                if expected == num_of_fragments:
                    expected = 0
                    print(f"Received message:")
                    print_the_message(final_message)
                    switch_rep_s_c(final_message, seq_num, num_of_fragments, server_socket,client_address)

            if header['flag'] == 6:

                seq_num = int.from_bytes(header['sequence_num'], 'big')
                num_of_fragments = int.from_bytes(header['num_of_fragments'], 'big')

                if seq_num == 0:
                    part2 = data[13:].decode(Format)
                    print(f"Received filepath: {part2}")
                    continue

                if header['checksum'] == checksum(data[13:]):
                    print(f"Checksum verification successful for fragment {seq_num}.")
                    total_received += 1

                    flag = 3

                    ack_header = create_header(flag, seq_num, 0, b"", num_of_fragments)
                    ack_header_bytes = (
                            bytes([ack_header['flag']]) +
                            ack_header['sequence_num'] +
                            ack_header['fragment_size'] +
                            ack_header['checksum'] +
                            ack_header['num_of_fragments']
                    )
                    try:
                        server_socket.sendto(ack_header_bytes, client_address)
                    except OSError:
                        print("Client is unreachable")

                else:
                    print(f"Checksum verification failed for fragment {seq_num}")
                    flag = 4
                    ack_header = create_header(flag, seq_num, 0, b"", num_of_fragments)
                    ack_header_bytes = (
                            bytes([ack_header['flag']]) +
                            ack_header['sequence_num'] +
                            ack_header['fragment_size'] +
                            ack_header['checksum'] +
                            ack_header['num_of_fragments']
                    )
                    try:
                        server_socket.sendto(ack_header_bytes, client_address)
                    except OSError:
                        print("Client is unreachable")

                received_fragments[seq_num] = data[13:]
                # print(received_fragments[seq_num])

                if total_received == num_of_fragments:
                    total_received = 0
                    final_message.clear()
                    file_path1 = input("print ENTER\nEnter the path to save the received file: ")
                    print(file_path1)


                    file_path = file_path1 + part2
                    print(file_path)
                    with open(file_path, 'wb') as file:
                        for i in range(1, num_of_fragments + 1):
                            file.write(received_fragments[i])

                    print(f"File received and saved at {file_path}")

                    print()

                    switch_rep_s_c(final_message, seq_num, num_of_fragments, server_socket, client_address)
            if header['flag'] == 5:
                flag = 5
                ack_header = create_header(flag, 0, 0, b"", 0)
                ack_header_bytes = (
                        bytes([ack_header['flag']]) +
                        ack_header['sequence_num'] +
                        ack_header['fragment_size'] +
                        ack_header['checksum'] +
                        ack_header['num_of_fragments']
                )
                try:
                    server_socket.sendto(ack_header_bytes, client_address)
                except OSError:
                    print("Client is unreachable")

            if header['flag'] == 8:
                Server_thread = True
                input_thread_instance.join()
                print("Switch request from client was received.")
                server_socket.close()
                print("Server socket was closed.")
                print("Server was readdressed to client.")
                client()

            if header['flag'] == 4:
                print("ACK: continue in server mode.")

            if header['flag'] == 2:
                Server_thread = True
                input_thread_instance.join()
                print("Close request received from the client. Press Enter")
                server_socket.close()
                print("Server socket was closed.")
                main_choice()
        except OSError as e:
            if e.errno == 10038:
                # WinError 10038 - Socket operation on non-socket
                break  # Exit the loop when the socket is closed
            else:
                raise
    main_choice()


def main_choice():
    choice = input("1 - server\n2 - client\n3 - out\n")
    if choice == '1':
        server()
    if choice == '2':
        client()
    if choice == '3':
        Thread_on = False
        Check = False
        stop_event.set()
        sys.exit()


if __name__ == '__main__':
    main_choice()
