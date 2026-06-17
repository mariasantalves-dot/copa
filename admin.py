"""
╔══════════════════════════════════════════╗
║   🏆 BOLÃO DA COPA — PAINEL ADMIN        ║
║   Execute:  python admin.py              ║
╚══════════════════════════════════════════╝

Use este script para:
  - Ver todos os palpites e pontuações
  - Inserir resultado de um jogo
  - Recalcular todos os pontos
  - Exportar relatório em texto
"""

import json
import os
from pathlib import Path

DATA_FILE = "dados.json"

# ── PARTIDAS (espelha as do HTML) ──────────────────────
PARTIDAS = [
    {"id": "m1", "home": "Brasil",       "away": "México",        "hFlag": "🇧🇷", "aFlag": "🇲🇽", "group": "Grupo A", "status": "done",     "hScore": 2, "aScore": 0},
    {"id": "m2", "home": "Argentina",    "away": "Chile",         "hFlag": "🇦🇷", "aFlag": "🇨🇱", "group": "Grupo B", "status": "done",     "hScore": 1, "aScore": 1},
    {"id": "m3", "home": "França",       "away": "Alemanha",      "hFlag": "🇫🇷", "aFlag": "🇩🇪", "group": "Grupo C", "status": "live",     "hScore": 1, "aScore": 0},
    {"id": "m4", "home": "Espanha",      "away": "Portugal",      "hFlag": "🇪🇸", "aFlag": "🇵🇹", "group": "Grupo D", "status": "upcoming", "hScore": None, "aScore": None},
    {"id": "m5", "home": "Inglaterra",   "away": "Itália",        "hFlag": "🏴", "aFlag": "🇮🇹", "group": "Grupo E", "status": "upcoming", "hScore": None, "aScore": None},
    {"id": "m6", "home": "Holanda",      "away": "Bélgica",       "hFlag": "🇳🇱", "aFlag": "🇧🇪", "group": "Grupo F", "status": "upcoming", "hScore": None, "aScore": None},
    {"id": "m7", "home": "Uruguai",      "away": "Colômbia",      "hFlag": "🇺🇾", "aFlag": "🇨🇴", "group": "Grupo G", "status": "upcoming", "hScore": None, "aScore": None},
    {"id": "m8", "home": "Japão",        "away": "Coreia do Sul", "hFlag": "🇯🇵", "aFlag": "🇰🇷", "group": "Grupo H", "status": "upcoming", "hScore": None, "aScore": None},
]

# ── LÓGICA DE PONTUAÇÃO ────────────────────────────────
def calcular_pontos(bh: int, ba: int, rh: int, ra: int) -> int:
    """Calcula os pontos de um palpite vs resultado real."""
    if bh == rh and ba == ra:
        return 10  # Placar exato
    bW = "h" if bh > ba else ("a" if bh < ba else "d")
    rW = "h" if rh > ra else ("a" if rh < ra else "d")
    if bW != rW:
        return 0
    pts = 5  # Vencedor certo
    if abs(bh - ba) == abs(rh - ra):
        pts += 3  # Diferença de gols certa
    return pts


# ── DADOS ─────────────────────────────────────────────
def carregar() -> dict:
    if not Path(DATA_FILE).exists():
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar(dados: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def partida_por_id(pid: str) -> dict | None:
    return next((p for p in PARTIDAS if p["id"] == pid), None)


# ── RECALCULAR TODOS OS PONTOS ─────────────────────────
def recalcular_tudo(dados: dict) -> dict:
    for nome, info in dados.items():
        total = acertos = exatos = 0
        bets = info.get("bets", {})
        for partida in PARTIDAS:
            if partida["status"] != "done":
                continue
            b = bets.get(partida["id"])
            if not b:
                continue
            pts = calcular_pontos(b["h"], b["a"], partida["hScore"], partida["aScore"])
            if pts > 0:
                acertos += 1
            if pts == 10:
                exatos += 1
            total += pts
        info["points"] = total
        info["_ac"] = acertos
        info["_ex"] = exatos
    return dados


# ── EXIBIR RANKING ─────────────────────────────────────
def exibir_ranking():
    dados = carregar()
    if not dados:
        print("\n  Nenhum jogador cadastrado ainda.\n")
        return

    dados = recalcular_tudo(dados)
    salvar(dados)

    ranking = sorted(
        [{"nome": n, **v} for n, v in dados.items()],
        key=lambda x: x.get("points", 0),
        reverse=True,
    )

    print("\n" + "═" * 52)
    print("  🏅 RANKING ATUAL")
    print("═" * 52)
    medals = ["🥇", "🥈", "🥉"]
    for i, j in enumerate(ranking):
        m = medals[i] if i < 3 else f"  {i+1}."
        nome = j["nome"][:20].ljust(20)
        pts = str(j.get("points", 0)).rjust(4)
        ac = j.get("_ac", 0)
        ex = j.get("_ex", 0)
        print(f"  {m}  {nome}  {pts} pts  ({ac} acertos, {ex} exatos)")
    print("═" * 52 + "\n")


# ── EXIBIR PALPITES DE UM JOGO ─────────────────────────
def exibir_palpites_jogo(pid: str):
    dados = carregar()
    partida = partida_por_id(pid)
    if not partida:
        print(f"\n  ❌ Partida '{pid}' não encontrada.\n")
        return

    print(f"\n  ⚽ {partida['home']} × {partida['away']} ({partida['group']})")
    if partida["status"] == "done":
        print(f"  Resultado real: {partida['hScore']} × {partida['aScore']}")
    elif partida["status"] == "live":
        print(f"  🔴 Ao vivo: {partida.get('hScore','?')} × {partida.get('aScore','?')}")
    else:
        print("  Jogo ainda não aconteceu")
    print()

    encontrou = False
    for nome, info in dados.items():
        b = info.get("bets", {}).get(pid)
        if b:
            pts = ""
            if partida["status"] == "done":
                p = calcular_pontos(b["h"], b["a"], partida["hScore"], partida["aScore"])
                pts = f"  →  +{p} pts"
            print(f"  {nome:<22} apostou: {b['h']} × {b['a']}{pts}")
            encontrou = True

    if not encontrou:
        print("  Nenhum palpite feito para este jogo ainda.")
    print()


# ── INSERIR RESULTADO DE UM JOGO ───────────────────────
def inserir_resultado():
    print("\n  📝 INSERIR RESULTADO DE JOGO")
    print("  (Atualize no arquivo server.py também para refletir no site)\n")

    for p in PARTIDAS:
        status = "✅" if p["status"] == "done" else ("🔴" if p["status"] == "live" else "⏳")
        print(f"  {status}  {p['id']}  —  {p['home']} × {p['away']}")

    pid = input("\n  Digite o ID do jogo (ex: m4): ").strip()
    partida = partida_por_id(pid)
    if not partida:
        print(f"  ❌ Partida '{pid}' não encontrada.")
        return

    print(f"\n  Inserindo resultado para: {partida['home']} × {partida['away']}")
    try:
        h = int(input(f"  Gols {partida['home']}: "))
        a = int(input(f"  Gols {partida['away']}: "))
    except ValueError:
        print("  ❌ Valor inválido.")
        return

    # Atualiza a partida na lista local (para recalcular)
    partida["hScore"] = h
    partida["aScore"] = a
    partida["status"] = "done"

    dados = carregar()
    dados = recalcular_tudo(dados)
    salvar(dados)

    print(f"\n  ✅ Resultado salvo: {partida['home']} {h} × {a} {partida['away']}")
    print("  ⚠️  Lembre de atualizar o status e placar no server.py e index.html também!\n")
    exibir_palpites_jogo(pid)


# ── EXPORTAR RELATÓRIO ─────────────────────────────────
def exportar_relatorio():
    dados = carregar()
    if not dados:
        print("\n  Nenhum dado para exportar.\n")
        return

    dados = recalcular_tudo(dados)
    salvar(dados)
    ranking = sorted(
        [{"nome": n, **v} for n, v in dados.items()],
        key=lambda x: x.get("points", 0),
        reverse=True,
    )

    linhas = ["🏆 BOLÃO DA COPA 2026 — RELATÓRIO\n", "=" * 50]
    for i, j in enumerate(ranking, 1):
        linhas.append(f"{i}. {j['nome']} — {j.get('points',0)} pts ({j.get('_ac',0)} acertos)")
    linhas.append("\n" + "=" * 50 + "\nPALPITES POR JOGO\n")

    for partida in PARTIDAS:
        if partida["status"] != "done":
            continue
        linhas.append(f"\n⚽ {partida['home']} {partida['hScore']} × {partida['aScore']} {partida['away']}")
        for nome, info in dados.items():
            b = info.get("bets", {}).get(partida["id"])
            if b:
                pts = calcular_pontos(b["h"], b["a"], partida["hScore"], partida["aScore"])
                linhas.append(f"   {nome:<20} {b['h']}×{b['a']}  → +{pts} pts")

    filename = "relatorio_bolao.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"\n  ✅ Relatório exportado: {filename}\n")


# ── MENU PRINCIPAL ─────────────────────────────────────
def menu():
    while True:
        print("\n" + "═" * 45)
        print("  🏆  BOLÃO DA COPA 2026 — ADMIN")
        print("═" * 45)
        print("  1  →  Ver ranking")
        print("  2  →  Ver palpites de um jogo")
        print("  3  →  Inserir resultado de jogo")
        print("  4  →  Exportar relatório (.txt)")
        print("  5  →  Recalcular todos os pontos")
        print("  0  →  Sair")
        print("═" * 45)

        op = input("  Escolha: ").strip()

        if op == "1":
            exibir_ranking()
        elif op == "2":
            pid = input("  ID do jogo (m1–m8): ").strip()
            exibir_palpites_jogo(pid)
        elif op == "3":
            inserir_resultado()
        elif op == "4":
            exportar_relatorio()
        elif op == "5":
            dados = carregar()
            dados = recalcular_tudo(dados)
            salvar(dados)
            print("\n  ✅ Pontos recalculados!\n")
            exibir_ranking()
        elif op == "0":
            print("\n  Até a próxima! 🏆\n")
            break
        else:
            print("  ❌ Opção inválida.")


if __name__ == "__main__":
    menu()



