import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote_plus, parse_qs
import socket
import threading
from datetime import datetime


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers.get('Content-Length')))
        self.send_to_socket_server(data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_to_socket_server(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(data, ("localhost", 5000))

    def do_GET(self):
        url = urlparse(self.path)
        match url.path:
            case '/':
                self.send_html("index.html")
            case '/message':
                self.send_html("send_message.html")
            case _:
                file_path = Path(url.path[1:])
                if file_path.exists():
                    self.send_static(str(file_path))
                else:
                    self.send_html("error.html", 404)

    def send_static(self, static_filename):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(static_filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_html(self, html_filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(html_filename, 'rb') as f:
            self.wfile.write(f.read())

    def save_to_json(self, raw_data):
        data = unquote_plus(raw_data.decode())
        dict_data = {key: value for key, value in [el.split("=") for el in data.split("&")]}
        print(dict_data)
        with open('data/data.json', 'w', encoding = 'utf-8') as f:
            json.dump(dict_data, f, ensure_ascii=False)

def run_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, HttpGetHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(("localhost", 5000))
        while True:
            data, addr = server_socket.recvfrom(1024)
            save_data_to_json(data)

def save_data_to_json(data):
    parsed_data = parse_qs(data.decode())
    parsed_data = {k: v[0] for k, v in parsed_data.items()}
    
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    file_path = Path("storage/data.json")
    file_path.parent.mkdir(exist_ok=True)
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)
    else:
        content = {}
        
    content[time_now] = parsed_data
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    threading.Thread(target=run_socket_server).start()