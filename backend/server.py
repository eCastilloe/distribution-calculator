import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from calculator import solve

# La página está en frontend/, una carpeta arriba de backend/.
# Cuando corre como .exe, PyInstaller deja los archivos en sys._MEIPASS
PROJECT_FOLDER = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
PAGE = PROJECT_FOLDER / "frontend" / "index.html"
MAX_BODY_BYTES = 10_000
INVALID_DATA = "Los datos enviados no son válidos."


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
        path = self.path.split("?")[0]
        if path == "/health":
            self.send_body(200, "text/plain; charset=utf-8", b"ok")
        elif path in ("/", "/index.html"):
            self.send_body(200, "text/html; charset=utf-8", PAGE.read_bytes())
        else:
            self.send_json(404, {"error": "Página no encontrada."})

    def read_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return None
        if not 0 < length <= MAX_BODY_BYTES:
            return None
        return self.rfile.read(length)

    def do_POST(self):
        if self.path != "/api/calculate":
            self.send_json(404, {"error": "Ruta no encontrada."})
            return
        body = self.read_body()
        if body is None:
            self.send_json(400, {"error": INVALID_DATA})
            return
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError(INVALID_DATA)
            self.send_json(200, solve(data))
        except json.JSONDecodeError:
            self.send_json(400, {"error": INVALID_DATA})
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
        except Exception:
            message = "Ocurrió un error inesperado. Revisa los datos e intenta de nuevo."
            self.send_json(500, {"error": message})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Programa disponible en el puerto {port}  (Ctrl+C para detenerlo)")
    server.serve_forever()
