"""
Verificador estatico do projeto Calendar Sync.

Le os ficheiros como texto e procura os erros que nao se veem a correr o
programa. Complementa os autotestes: os autotestes verificam a logica, isto
verifica o texto dos ficheiros. Nenhum dos dois ve se o painel ficou
desalinhado — para isso e preciso abri-lo.

Corre com: python verificar.py            (sem instalar nada)
Devolve 0 se estiver tudo bem, 1 se houver problemas.

─────────────────────────────────────────────────────────────────────────────
MANUTENCAO
─────────────────────────────────────────────────────────────────────────────
Cada verificacao aqui nasceu de um erro real. Ao corrigir uma avaria nova,
pergunte se ela era visivel no texto do ficheiro; se era, acrescente aqui a
verificacao que a teria apanhado. NAO REMOVER verificacoes sem apagar tambem
a linha correspondente do registo de avarias no merge_calendars.py.
"""

import ast
import json
import os
import re
import sys

MOTOR = "merge_calendars.py"
PAINEL = "index.html"
CONFIG = "calendars.json"

problemas: list[str] = []
avisos: list[str] = []


def problema(texto: str) -> None:
    problemas.append(texto)


def aviso(texto: str) -> None:
    avisos.append(texto)


def ler(caminho: str):
    if not os.path.exists(caminho):
        problema(f"{caminho} nao existe")
        return None
    with open(caminho, encoding="utf-8") as handle:
        return handle.read()


# --------------------------------------------------------------------------- #
# Motor
# --------------------------------------------------------------------------- #
def verificar_motor(texto: str) -> str | None:
    try:
        arvore = ast.parse(texto)
    except SyntaxError as exc:
        problema(f"{MOTOR}: erro de sintaxe na linha {exc.lineno} — {exc.msg}")
        return None

    # nomes definidos duas vezes ao nivel do modulo: a segunda apaga a primeira
    vistos: dict[str, int] = {}
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if no.name in vistos:
                problema(
                    f"{MOTOR}: '{no.name}' definido duas vezes "
                    f"(linhas {vistos[no.name]} e {no.lineno}) — a segunda apaga a primeira"
                )
            vistos[no.name] = no.lineno

    # a lista de autotestes tem de existir e nao encolher em silencio
    testes = re.findall(r"^\s*\(\"[^\"]+\", (_t\d+_\w+)\),", texto, re.M)
    definidos = {nome for nome in vistos if nome.startswith("_t")}
    if not testes:
        problema(f"{MOTOR}: a lista AUTOTESTES desapareceu")
    for nome in testes:
        if nome not in definidos:
            problema(f"{MOTOR}: o autoteste '{nome}' esta na lista mas nao existe")
    orfaos = definidos - set(testes)
    if orfaos:
        problema(
            f"{MOTOR}: {', '.join(sorted(orfaos))} — teste escrito mas fora da lista "
            "AUTOTESTES, portanto nunca corre"
        )

    versao = re.search(r'^VERSAO = "([\d.]+)"', texto, re.M)
    if not versao:
        problema(f"{MOTOR}: VERSAO desapareceu")
        return None
    if f"{versao.group(1)} -" not in texto:
        problema(
            f"{MOTOR}: a versao {versao.group(1)} nao tem linha no HISTORICO — "
            "o comportamento mudou e a lista de alteracoes ficou para tras"
        )

    # regra 3 do bloco de manutencao: nao publicar quando falta informacao
    if "if hard_failure:" not in texto:
        problema(
            f"{MOTOR}: desapareceu a protecao que impede publicar um calendario "
            "incompleto quando uma plataforma esta em baixo (avaria da v2.0)"
        )
    return versao.group(1)


# --------------------------------------------------------------------------- #
# Painel
# --------------------------------------------------------------------------- #
def verificar_painel(texto_completo: str, versao_motor: str | None) -> None:
    # o bloco de manutencao fala de fetch e de localStorage para os proibir:
    # se nao o retirarmos, o verificador acusa o proprio aviso (v3.1)
    texto = re.sub(r"<!--.*?-->", "", texto_completo, flags=re.DOTALL)
    # variaveis CSS usadas mas nunca definidas (o erro --suave:#5D7framework)
    definidas = set(re.findall(r"^\s*--([a-z0-9-]+)\s*:", texto, re.M))
    usadas = set(re.findall(r"var\(--([a-z0-9-]+)\)", texto))
    for nome in sorted(usadas - definidas):
        problema(f"{PAINEL}: a cor var(--{nome}) e usada mas nunca foi definida")
    for valor in re.findall(r"^\s*--[a-z0-9-]+\s*:\s*([^;]+);", texto, re.M):
        valor = valor.strip()
        if not re.fullmatch(r"(#[0-9A-Fa-f]{3,8}|[\d.]+(px|em|rem|%)?|[a-z-]+\([^)]*\))", valor):
            problema(f"{PAINEL}: valor de estilo suspeito — '{valor}'")

    # regras do bloco de manutencao desta pagina
    if "localStorage" in texto or "sessionStorage" in texto:
        problema(f"{PAINEL}: armazenamento no browser — proibido, ver o bloco de manutencao")
    if re.search(r"\bfetch\s*\(", texto):
        problema(
            f"{PAINEL}: fetch() — os dados entram por <script src>, senao a pagina "
            "deixa de abrir a partir do disco"
        )
    if "<script src=\"output/dashboard.js\"" not in texto:
        problema(f"{PAINEL}: a linha que carrega os dados desapareceu")

    versao = re.search(r'const PAINEL_VERSAO = "([\d.]+)"', texto)
    if not versao:
        problema(f"{PAINEL}: PAINEL_VERSAO desapareceu")
    elif versao_motor and versao.group(1) != versao_motor:
        problema(
            f"painel na versao {versao.group(1)} e motor na {versao_motor} — "
            "um dos dois ficou por atualizar"
        )

    if "const TESTES = [" not in texto:
        problema(f"{PAINEL}: a lista de autotestes desapareceu")

    # etiquetas mal fechadas por truncagem a meio de uma alteracao
    for etiqueta in ("script", "style", "html", "body"):
        if texto.count(f"<{etiqueta}") != texto.count(f"</{etiqueta}>"):
            problema(f"{PAINEL}: <{etiqueta}> aberto e fechado em numero diferente")
    if len(texto_completo) < 8000:
        problema(f"{PAINEL}: so tem {len(texto_completo)} bytes — parece truncado")


# --------------------------------------------------------------------------- #
# Configuracao
# --------------------------------------------------------------------------- #
def verificar_config(texto: str) -> None:
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as exc:
        problema(f"{CONFIG}: JSON invalido na linha {exc.lineno} — {exc.msg}")
        return

    casas = dados.get("properties")
    if casas is None:
        aviso(f"{CONFIG}: formato antigo, ainda lido mas sem casas nem bloqueios manuais")
        return

    caminhos: dict[str, str] = {}
    ids_casa: set[str] = set()
    for casa in casas:
        id_casa = casa.get("id", "")
        nome = casa.get("name", id_casa)
        if not id_casa:
            problema(f"{CONFIG}: a casa '{nome}' nao tem id")
        if id_casa in ids_casa:
            problema(f"{CONFIG}: duas casas com o id '{id_casa}' — escrevem na mesma pasta")
        ids_casa.add(id_casa)
        if not re.fullmatch(r"[a-z0-9-]+", id_casa or "x"):
            problema(
                f"{CONFIG}: o id '{id_casa}' tem maiusculas, acentos ou espacos; "
                "sera convertido e o caminho do .ics deixa de ser o que esta escrito"
            )

        for quarto in casa.get("rooms", []):
            id_quarto = quarto.get("id", "")
            etiqueta = f"{nome} / {quarto.get('name', id_quarto)}"
            if not id_quarto:
                problema(f"{CONFIG}: o quarto '{etiqueta}' nao tem id")
            caminho = f"{id_casa}/{id_quarto}.ics"
            if caminho in caminhos:
                problema(
                    f"{CONFIG}: '{etiqueta}' e '{caminhos[caminho]}' escrevem os dois em "
                    f"output/{caminho} — um apaga o outro"
                )
            caminhos[caminho] = etiqueta

            fontes = quarto.get("sources", [])
            if not fontes and not quarto.get("manual_blocks"):
                aviso(f"{CONFIG}: '{etiqueta}' nao tem nenhuma fonte configurada")
            plataformas = [f.get("platform", "") for f in fontes]
            for plataforma in set(plataformas):
                if plataformas.count(plataforma) > 1:
                    aviso(f"{CONFIG}: '{etiqueta}' tem {plataforma} repetida")
            for fonte in fontes:
                url = fonte.get("url", "")
                plataforma = fonte.get("platform", "?")
                if not url:
                    aviso(f"{CONFIG}: '{etiqueta}' — {plataforma} esta por preencher")
                elif not url.startswith(("http://", "https://")):
                    problema(f"{CONFIG}: '{etiqueta}' — o link de {plataforma} nao e um endereco web")
                elif "/my/" in url or "useUnitType" in url:
                    problema(
                        f"{CONFIG}: '{etiqueta}' — o link de {plataforma} e o endereco da "
                        "pagina do site, nao o de exportacao; devolve HTML e exige sessao iniciada"
                    )

            for bloco in quarto.get("manual_blocks", []):
                try:
                    from datetime import date
                    inicio = date.fromisoformat(bloco["start"])
                    fim = date.fromisoformat(bloco["end"])
                except Exception:  # noqa: BLE001
                    problema(f"{CONFIG}: '{etiqueta}' — bloqueio manual com datas invalidas: {bloco}")
                    continue
                if fim <= inicio:
                    problema(
                        f"{CONFIG}: '{etiqueta}' — bloqueio manual de {inicio} a {fim} "
                        "termina antes de comecar, nao bloqueia nada"
                    )

    # .ics gerados que ja nao correspondem a nenhum quarto: link morto nas plataformas
    if os.path.isdir("output"):
        for raiz, _dirs, ficheiros in os.walk("output"):
            for ficheiro in ficheiros:
                if not ficheiro.endswith(".ics"):
                    continue
                rel = os.path.relpath(os.path.join(raiz, ficheiro), "output").replace(os.sep, "/")
                if rel not in caminhos:
                    problema(
                        f"output/{rel} ja nao corresponde a nenhum quarto do {CONFIG} — "
                        "se este link ja foi dado a uma plataforma, ela deixou de ver as "
                        "reservas e pode revender as datas"
                    )


def main() -> int:
    texto_motor = ler(MOTOR)
    versao = verificar_motor(texto_motor) if texto_motor else None
    texto_painel = ler(PAINEL)
    if texto_painel:
        verificar_painel(texto_painel, versao)
    texto_config = ler(CONFIG)
    if texto_config:
        verificar_config(texto_config)

    for texto in avisos:
        print("  aviso: " + texto)
    for texto in problemas:
        print("  PROBLEMA: " + texto)

    if problemas:
        print(f"\n{len(problemas)} problema(s) a corrigir antes de entregar.")
        return 1
    print(f"\nVerificacao limpa{f' (versao {versao})' if versao else ''}"
          f"{f', {len(avisos)} aviso(s)' if avisos else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
