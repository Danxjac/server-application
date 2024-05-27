#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024

void serve_html(int client_socket) {
    FILE *html_file = fopen("index.html", "r");
    if (!html_file) {
        perror("Failed to open HTML file");
        return;
    }

    char buffer[BUFFER_SIZE];
    size_t bytes_read;
    char response_header[] = "HTTP/1.1 200 OK\r\n"
                             "Content-Type: text/html\r\n"
                             "Connection: close\r\n\r\n";
    send(client_socket, response_header, strlen(response_header), 0);

    while ((bytes_read = fread(buffer, 1, BUFFER_SIZE, html_file)) > 0) {
        send(client_socket, buffer, bytes_read, 0);
    }

    fclose(html_file);
    close(client_socket);
}

void handle_client(int client_socket) {
    char buffer[BUFFER_SIZE];
    read(client_socket, buffer, sizeof(buffer) - 1);
    serve_html(client_socket);
}

int main() {
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == 0) {
        perror("Socket failed");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in address;
    int addrlen = sizeof(address);
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_socket, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    if (listen(server_socket, 3) < 0) {
        perror("Listen failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    printf("HTML server listening on port %d\n", PORT);

    while (1) {
        int client_socket = accept(server_socket, (struct sockaddr *)&address, (socklen_t*)&addrlen);
        if (client_socket < 0) {
            perror("Accept failed");
            close(server_socket);
            exit(EXIT_FAILURE);
        }
        handle_client(client_socket);
    }

    close(server_socket);
    return 0;
}

