import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from problems import solve

FRONTEND = (Path(__file__).parent / "frontend").resolve()
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    def send_body(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_body(status, "application/json; charset=utf-8", body)

    def do_GET(self):
        name = self.path.split("?")[0].lstrip("/") or "index.html"
        file = (FRONTEND / name).resolve()
        if file.parent != FRONTEND or not file.is_file():
            self.send_json(404, {"error": "Página no encontrada."})
            return
        content_type = CONTENT_TYPES.get(file.suffix, "application/octet-stream")
        self.send_body(200, content_type, file.read_bytes())

    def do_POST(self):
        if self.path != "/api/calculate":
            self.send_json(404, {"error": "Ruta no encontrada."})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Los datos enviados no son válidos.")
            self.send_json(200, solve(data))
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Los datos enviados no son válidos."})
        except ValueError as error:
            self.send_json(400, {"error": str(error)})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Programa disponible en http://localhost:8000  (Ctrl+C para detenerlo)")
    server.serve_forever()
