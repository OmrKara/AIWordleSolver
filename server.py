from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
import mimetypes
import threading
import webbrowser


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8766
ALLOWED_FILES = {
    "/index.html": "index.html",
    "/style.css": "style.css",
    "/app.js": "app.js",
    "/solver.worker.js": "solver.worker.js",
    "/answers.txt": "answers.txt",
    "/eng_dict.txt": "eng_dict.txt",
}


class LocalWordleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/":
            path = "/index.html"

        file_name = ALLOWED_FILES.get(path)
        if file_name is None:
            self.send_error(404, "Not found")
            return

        content = (ROOT / file_name).read_bytes()
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        if file_name.endswith((".js", ".css", ".txt", ".html")):
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print(f"[{self.log_date_time_string()}] {format_string % args}")


def main():
    server = ThreadingHTTPServer((HOST, PORT), LocalWordleHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"Wordle hazır: {url}")
    print("Durdurmak için Ctrl+C kullan.")
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    webbrowser.open(url)
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nYerel Wordle sunucusu durduruldu.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
