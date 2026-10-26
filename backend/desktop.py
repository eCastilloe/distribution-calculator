import threading
import webbrowser
from http.server import ThreadingHTTPServer

from server import Handler


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_address[1]}"
    threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    print("Calculadora de distribuciones Z, t, chi cuadrada y F", flush=True)
    print(f"Se abrirá en tu navegador: {url}", flush=True)
    print("Para cerrar el programa, cierra esta ventana.", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
