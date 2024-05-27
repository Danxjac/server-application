# -*- coding: utf-8 -*-
"""
Created on Mon May 20 13:07:10 2024
"""

import socket
import threading
import os
import time
from urllib.parse import urlparse, parse_qs

stations = {
    "BusportC": 4005,
    "JunctionB": 4003,
    "JunctionF": 4011,
    "StationD": 4007,
    "TerminalA": 4001,
    "TerminalE": 4009,
}

timetables = {station: {} for station in stations}

def load_timetable(station):
    filename = f"{station}.txt"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(',')
                    if len(parts) == 5:
                        departure_time, route_name, departing_from, arrival_time, arrival_station = parts
                        if arrival_station not in timetables[station]:
                            timetables[station][arrival_station] = []
                        timetables[station][arrival_station].append((departure_time, arrival_time, route_name, departing_from))

def monitor_timetable(station):
    filename = f"{station}.txt"
    last_modified = os.path.getmtime(filename)
    while True:
        time.sleep(1)
        new_modified = os.path.getmtime(filename)
        if new_modified != last_modified:
            load_timetable(station)
            last_modified = new_modified

def handle_client(client_socket, station):
    request = client_socket.recv(1024).decode()
    headers = request.split("\r\n")
    query_line = headers[0]
    if query_line.startswith("GET"):
        parsed_url = urlparse(query_line.split(" ")[1])
        params = parse_qs(parsed_url.query)
        destination = params.get("to", [None])[0]
        leave_after = params.get("leave", [None])[0]

        response_body = ""
        if destination and leave_after:
            response_body = find_route(station, destination, leave_after)
        else:
            response_body = "<html><body><h1>Invalid parameters.</h1></body></html>"

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{response_body}"
        )

        client_socket.sendall(response.encode())
        client_socket.close()

def find_route(station, destination, leave_after):
    result_html = """
    <html>
    <head>
        <title>Route Information</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                color: #333;
                margin: 0;
                padding: 20px;
            }
            .box {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            h2 {
                text-align: center;
            }
            .box p {
                margin: 5px 0;
            }
        </style>
    </head>
    
    <body>
      
    """

    route_found = False
    if destination in timetables[station]:
        for departure, arrival, route_name, departing_from in sorted(timetables[station][destination]):
            if departure >= leave_after:
                result_html += f"""
                <div class="box">
                    <p>Catch <strong>{route_name}</strong> from <strong>{station}</strong> at <strong>{departure}</strong>, arriving at <strong>{destination}</strong> at <strong>{arrival}</strong>.</p>
                </div>
                """
                route_found = True
                break
    
    if not route_found:
        # Check for routes with transfers
        for intermediate_station in timetables[station]:
            for departure, arrival, route_name, departing_from in sorted(timetables[station][intermediate_station]):
                if departure >= leave_after:
                    intermediate_result = find_route(intermediate_station, destination, arrival)
                    if "Catch" in intermediate_result:
                        result_html += f"""
                        <div class="box">
                            <p>Catch <strong>{route_name}</strong> from <strong>{station}</strong> at <strong>{departure}</strong>, arriving at <strong>{intermediate_station}</strong> at <strong>{arrival}</strong>.</p>
                            {intermediate_result}
                        </div>
                        """
                        route_found = True
                        break
            if route_found:
                break
    
    if not route_found:
        result_html += f"""
        <div class="box">
            <p>There is no journey from <strong>{station}</strong> to <strong>{destination}</strong> leaving after <strong>{leave_after}</strong> today.</p>
        </div>
        """
    
    result_html += "</body></html>"
    return result_html

def start_server(station, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', port))
    server_socket.listen(5)
    print(f"{station} server listening on port {port}")

    threading.Thread(target=monitor_timetable, args=(station,)).start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Received connection from {addr} at {station} server")
        threading.Thread(target=handle_client, args=(client_socket, station)).start()

for station in stations:
    load_timetable(station)

for station, port in stations.items():
    threading.Thread(target=start_server, args=(station, port)).start()
