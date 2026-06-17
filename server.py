"""
╔══════════════════════════════════════════╗
║   🏆 BOLÃO DA COPA 2026 — SERVIDOR       ║
║   Execute:  python server.py             ║
║   Acesse:   http://localhost:8000        ║
╚══════════════════════════════════════════╝
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from pathlib import Path

# ── CONFIGURAÇÕES ──────────────────────────────────────
HOST = "localhost"
PORT = 8000
DATA_FILE = "dados.json"   # arquivo onde os palpites ficam salvos
HTML_FILE = "index.html"
# ───────────────────────────────────────────────────────


def carregar_dados() -> dict:
    """Carrega os dados do arquivo JSON."""
    if not Path(DATA_FILE).exists():
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_dados(dados: dict) -> None:
    """Salva os dados no arquivo JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


class BolaoHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP para o bolão."""

    def log_message(self, format, *args):
        # Filtra logs para deixar o terminal limpo
        if "GET / " in (args[0] if args else ""):
            print(f"  ⚽ Acesso ao site: {self.address_string()}")

    # ── GET ────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Serve o HTML principal
        if path == "/" or path == "/index.html":
            self._serve_html()

        # API: lista todos os jogadores e pontuações
        elif path == "/api/ranking":
            dados = carregar_dados()
            ranking = sorted(
                [
                    {
                        "nome": nome,
                        "pontos": info.get("points", 0),
                        "acertos": info.get("_ac", 0),
                        "exatos": info.get("_ex", 0),
                    }
                    for nome, info in dados.items()
                ],
                key=lambda x: x["pontos"],
                reverse=True,
            )
            self._json_response(ranking)

        # API: dados de um usuário específico
        elif path.startswith("/api/usuario/"):
            nome = urllib.parse.unquote(path.split("/api/usuario/")[1])
            dados = carregar_dados()
            if nome in dados:
                self._json_response(dados[nome])
            else:
                self._json_response({"erro": "Usuário não encontrado"}, 404)

        else:
            self.send_error(404, "Não encontrado")

    # ── POST ───────────────────────────────────────────
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._ler_body()

        # Salvar/atualizar dados de um usuário (chamado pelo JS)
        if path == "/api/salvar":
            try:
                dados_recebidos = json.loads(body)
                dados = carregar_dados()
                # Mescla os dados recebidos com os existentes
                for nome, info in dados_recebidos.items():
                    dados[nome] = info
                salvar_dados(dados)
                self._json_response({"ok": True})
            except Exception as e:
                self._json_response({"erro": str(e)}, 400)

        else:
            self.send_error(404, "Endpoint não encontrado")

    # ── UTILITÁRIOS ────────────────────────────────────
    def _serve_html(self):
        html_path = Path(HTML_FILE)
        if not html_path.exists():
            self.send_error(404, f"Arquivo {HTML_FILE} não encontrado.")
            return
        content = html_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _json_response(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def _ler_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ── INICIAR SERVIDOR ───────────────────────────────────
def main():
    # Verifica se o HTML existe
    if not Path(HTML_FILE).exists():
        print(f"\n❌ Arquivo '{HTML_FILE}' não encontrado.")
        print(f"   Coloque o arquivo HTML na mesma pasta que este script.\n")
        return

    print("\n" + "═" * 50)
    print("  🏆  BOLÃO DA COPA 2026")
    print("═" * 50)
    print(f"  ✅ Servidor rodando!")
    print(f"  🌐 Acesse: http://{HOST}:{PORT}")
    print(f"  📁 Dados salvos em: {DATA_FILE}")
    print(f"  ⛔ Para parar: Ctrl + C")
    print("═" * 50 + "\n")

    with socketserver.TCPServer((HOST, PORT), BolaoHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n⛔ Servidor encerrado. Até a próxima! 🏆\n")


if __name__ == "__main__":
    main()
