"""
Sincronizador de calendarios para arrendamento por quartos (multi-casa).

Le calendars.json, vai buscar os feeds iCal de cada plataforma, normaliza tudo
para intervalos de datas ocupadas, funde-os por quarto e escreve:

  output/<casa>/<quarto>.ics   ficheiro unico por quarto, pronto a importar
  output/dashboard.js          dados do painel (index.html)
  status.json                  estado da ultima sincronizacao
  cache/...                    ultima leitura boa de cada plataforma

Principios de seguranca (evitar overbooking):
  1. Cache local: se uma plataforma falhar, usa-se a ultima leitura boa.
  2. Nunca publica menos do que sabia: sem resposta e sem cache, o ficheiro
     anterior NAO e sobrescrito e o processo termina com erro.
  3. Anti-loop: eventos gerados por este script sao ignorados quando voltam a
     entrar por outra plataforma.

Sem dependencias externas. Corre com: python merge_calendars.py

─────────────────────────────────────────────────────────────────────────────
MANUTENCAO — LER ANTES DE ALTERAR ESTE FICHEIRO
─────────────────────────────────────────────────────────────────────────────
Quem alterar isto a seguir, pessoa ou modelo de linguagem, fica com estas
obrigacoes. Nao sao sugestoes: se forem ignoradas, o programa publica
disponibilidade errada e alguem reserva um quarto que ja esta ocupado.

0. ANTES DE ENTREGAR: correr `python verificar.py` e `python merge_calendars.py`
   (os autotestes correm sozinhos no arranque e param tudo se falharem).

1. VERSAO E HISTORICO. Subir VERSAO e acrescentar uma linha ao HISTORICO, em
   linguagem de utilizador. A versao vai no PRODID de cada .ics e no painel,
   e serve para saber que versao gerou um ficheiro quando algo correr mal.

2. FORMATO DOS DADOS (calendars.json). E editado a mao pelo utilizador:
     - OS `id` DE CASA E DE QUARTO NUNCA SE RENOMEIAM. O id define o caminho
       do .ics, que ja foi colado nas plataformas. Renomear = link morto =
       a plataforma deixa de ver as reservas e revende as datas.
     - Campos novos entram no fim e toleram valor vazio.
     - Formatos antigos continuam a ser lidos (ver load_config); nao remover
       essa compatibilidade sem migrar o ficheiro do utilizador.

3. NUNCA PUBLICAR MENOS DO QUE SE SABIA. Se uma fonte falha e nao ha cache, o
   .ics NAO e escrito nem sobrescrito. Um calendario em falta faz a plataforma
   ignorar a importacao; um calendario vazio faz a plataforma aceitar reservas
   por cima das existentes. Esta regra ja foi quebrada uma vez — ver ponto 6.

4. SEMANTICA DE DATAS. DTEND e SEMPRE exclusivo: o dia de saida fica livre.
   Toda a aritmetica de datas assume isto. Alterar esta convencao sem alterar
   os autotestes correspondentes desloca silenciosamente todas as reservas.

5. AUTOTESTES. Correm no arranque, so em memoria, e abortam o programa se
   falharem. NAO REMOVER nenhum: cada um corresponde a uma avaria real. Ao
   corrigir uma avaria nova, acrescentar aqui o teste que a teria apanhado.

6. REGISTO DE AVARIAS — o que ja correu mal, para nao repetir:
   v1.0  Extracao de eventos por expressao regular perdia linhas dobradas e
         aceitava reservas canceladas. -> parser proprio + testes 1, 2 e 11.
   v1.0  A mesma reserva vinda de duas plataformas gerava dois eventos
         sobrepostos. -> merge_intervals + testes 8 e 9.
   v2.0  Plataforma em baixo na primeira execucao escrevia um .ics vazio: o
         quarto aparecia livre em todas as outras plataformas. -> com falha
         sem cache nao se escreve nada (ver process_room).
   v2.0  Feed devolvido por outra plataforma reentrava e duplicava blocos em
         ciclo. -> marca X-CT-ORIGIN e dominio de UID proprio + teste 4.
   v3.7  A marca de origem so apanhava ecos que voltassem com o nosso UID. As
         plataformas que importam e reexportam com identificadores proprios
         passavam, e a mesma estadia aparecia duas vezes: uma real e uma
         devolvida por nos. -> guardar o que se publicou a cada plataforma e
         descartar o que volta contido nisso (ver e_eco e teste 21).
   v3.0  A mensagem "= N bloco(s) em ..." aparecia mesmo quando o ficheiro
         nao chegava a ser escrito. -> print movido para dentro do ramo que
         escreve.

7. PENDENTE — ideias adiadas e decisoes de nao fazer, com a razao:
   - Cor do Idealista por confirmar (as outras vieram dos logos). Corrigir em
     PLATAFORMAS no index.html.
   - Inventario partilhado entre quartos (bloquear os dois em conjunto para
     poder trocar hospedes de quarto) — REJEITADO pelo utilizador em 2026-07.
     A regra e: cada hospede fica no quarto do anuncio onde reservou. Isto so
     se aguenta com a sincronizacao de pe; sem ela, duas plataformas vendem o
     mesmo quarto e alguem tem de ser mudado a forca — foi o que aconteceu em
     julho de 2026 com duas reservas sobrepostas no anuncio do Quarto 2.
   - HousingAnywhere e Spacest tem cores de marca parecidas; ficam parecidas na
     fita. Nao se altera a cor de marca sem o utilizador pedir — o verificador
     avisa quando as duas estao em uso ao mesmo tempo.
   - Editor de ligacoes do painel nao grava: monta o texto e a pessoa cola no
     GitHub. Gravar exigiria um servidor ou um token no browser — rejeitado,
     um token num repositorio publico da acesso de escrita a quem o encontre.
   - Aviso quando entra uma reserva nova — adiado; o GitHub ja envia email
     quando a sincronizacao falha, que e o caso urgente.
   - Suporte a RRULE (eventos recorrentes) — rejeitado; nenhuma plataforma de
     arrendamento exprime reservas como recorrencia, e o custo e alto.
   - Guardar os dados dos inquilinos no repositorio — REJEITADO em definitivo.
     O repositorio e publico e o historico do Git guarda o que la entra: um
     commit com numeros de documento nao se desfaz. O inquilinos.html le um
     ficheiro que fica no computador do utilizador, e o verificar.py recusa
     ficheiros de inquilinos dentro do repositorio.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone

VERSAO = "3.16"

HISTORICO = [
    "3.16 - deteccao de eco: as plataformas que importam o nosso calendario e o "
    "reexportam como se fosse delas deixaram de duplicar reservas; o programa "
    "guarda o que publicou a cada uma e ignora o que lhe volta igual",
    "3.15 - a agenda para o calendario pessoal passou a ter um evento por "
    "periodo ocupado, em vez de um por plataforma: uma banda por quarto",
    "3.14 - na fita, cada reserva passa a ser pintada nas datas em que existe; "
    "antes, um bloco com varias plataformas era dividido em partes iguais e "
    "dava a entender datas que nao eram as verdadeiras",
    "3.13 - a Ajuda passou a ter os atalhos para o painel, para o registo e "
    "para os sitios do GitHub onde se mexe na configuracao",
    "3.12 - site_url na configuracao: os links passam a estar certos mesmo com "
    "a pagina aberta a partir do disco",
    "3.11 - titulos da agenda encurtados: a nota completa passou para a "
    "descricao do evento, em vez de ocupar a linha toda no calendario",
    "3.10 - as duas paginas passaram a ter ligacao uma para a outra, para se "
    "perceber que sao o mesmo sitio",
    "3.9 - o verificador avisa quando um bloqueio manual ja terminou e pode "
    "ser retirado da configuracao",
    "3.8 - agenda para o calendario pessoal: um link por quarto e um por casa, "
    "com quarto e plataforma no titulo e sem nomes de hospedes",
    "3.7 - cada quarto passou a ter um calendario por plataforma, sem as "
    "reservas dessa plataforma: importar as proprias reservas de volta fazia a "
    "plataforma bloquear por cima delas e podia anular a importacao inteira",
    "3.6 - registo de inquilinos (inquilinos.html): substitui a folha de Excel, "
    "le e grava um ficheiro no computador e nunca envia nada para a internet",
    "3.5 - cada quarto pode ter foto: basta por o ficheiro em "
    "fotos/<casa>/<quarto>.jpg; o editor de ligacoes passou a ter, em cada "
    "quarto, um campo sempre visivel para colar o link novo",
    "3.4 - as cores das plataformas passaram a ser as dos logos; o verificador "
    "avisa quando duas plataformas em uso ficam com cores parecidas",
    "3.3 - a ajuda passou a explicar a etiqueta da versao e como atualizar os "
    "ficheiros, que era o unico sitio da interface sem explicacao",
    "3.2 - cada plataforma passou a ter a sua cor na fita; o painel ganhou menu "
    "de ajuda e um editor para colar os links das plataformas",
    "3.1 - o programa passou a testar-se a si proprio no arranque e ganhou "
    "verificador estatico; a versao aparece no painel e nos ficheiros gerados",
    "3.0 - suporte a varias casas; painel de disponibilidade; um calendario "
    "por quarto em output/<casa>/<quarto>.ics",
    "2.0 - deixou de publicar calendarios incompletos quando uma plataforma "
    "esta em baixo; reservas repetidas passaram a aparecer uma so vez",
    "1.0 - primeira versao: juntar os links de cada plataforma num ficheiro",
]

CONFIG_FILE = "calendars.json"
OUTPUT_DIR = "output"
CACHE_DIR = "cache"
FOTOS_DIR = "fotos"
PUBLICADO_DIR = os.path.join(CACHE_DIR, "publicado")
STATUS_FILE = "status.json"
DASHBOARD_FILE = os.path.join(OUTPUT_DIR, "dashboard.js")

TIMEOUT_SECONDS = 25
RETRIES = 3
RETRY_BACKOFF = 4

DEFAULT_SETTINGS = {
    # Em iCal o DTEND de um evento de dia inteiro e exclusivo: o dia de saida
    # fica livre para uma entrada nova. True bloqueia tambem o dia de saida.
    "block_checkout_day": False,
    "keep_past_days": 7,
    "months_ahead": 24,
    "use_cache_on_failure": True,
    "event_summary": "Nao disponivel",
    "dashboard_days": 210,
    # Endereco publico do site, para os links funcionarem mesmo com a pagina
    # aberta a partir do disco. Vazio = calculado a partir do endereco atual.
    "site_url": "",
}

ORIGIN_TAG = "casa-trindade"
UID_DOMAIN = "casa-trindade.local"
MANUAL_LABEL = "Bloqueio manual"


def slug(text: str) -> str:
    lowered = text.lower()
    for accented, plain in (
        ("áàâã", "a"), ("éê", "e"), ("í", "i"), ("óôõ", "o"), ("ú", "u"), ("ç", "c")
    ):
        for char in accented:
            lowered = lowered.replace(char, plain)
    return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-") or "item"


# --------------------------------------------------------------------------- #
# Fetch
# --------------------------------------------------------------------------- #
def fetch(url: str) -> str | None:
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": f"CalendarSync/{VERSAO}",
                    "Accept": "text/calendar,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            if "BEGIN:VCALENDAR" not in text:
                last_error = "resposta sem conteudo iCal"
            else:
                return text
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        if attempt < RETRIES:
            time.sleep(RETRY_BACKOFF * attempt)
    print(f"      ! falhou ({last_error})")
    return None


# --------------------------------------------------------------------------- #
# Parsing iCal
# --------------------------------------------------------------------------- #
def unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def parse_events(text: str) -> list[dict]:
    events: list[dict] = []
    current: dict | None = None
    for line in unfold(text):
        stripped = line.strip()
        if stripped == "BEGIN:VEVENT":
            current = {}
            continue
        if stripped == "END:VEVENT":
            if current is not None:
                events.append(current)
            current = None
            continue
        if current is None or ":" not in stripped:
            continue
        head, _, value = stripped.partition(":")
        current[head.split(";")[0].upper()] = value
    return events


def parse_dt(value: str | None) -> date | None:
    if not value:
        return None
    match = re.match(r"^(\d{4})(\d{2})(\d{2})", value.strip())
    if not match:
        return None
    try:
        return date(*(int(group) for group in match.groups()))
    except ValueError:
        return None


def parse_duration_days(value: str) -> int:
    match = re.match(r"^P(?:(\d+)W)?(?:(\d+)D)?", value.strip())
    if not match:
        return 1
    return (int(match.group(1) or 0) * 7 + int(match.group(2) or 0)) or 1


def event_to_interval(event: dict, block_checkout_day: bool):
    """(inicio, fim_exclusivo) ou None se o evento nao bloqueia nada."""
    if (event.get("STATUS") or "").upper() in {"CANCELLED", "TENTATIVE"}:
        return None
    if (event.get("TRANSP") or "").upper() == "TRANSPARENT":
        return None
    if event.get("X-CT-ORIGIN") == ORIGIN_TAG or event.get("UID", "").endswith(
        "@" + UID_DOMAIN
    ):
        return None  # anti-loop

    start = parse_dt(event.get("DTSTART"))
    if start is None:
        return None
    end = parse_dt(event.get("DTEND"))
    if end is None:
        duration = event.get("DURATION")
        end = start + timedelta(days=parse_duration_days(duration) if duration else 1)
    if end <= start:
        end = start + timedelta(days=1)
    if block_checkout_day:
        end += timedelta(days=1)
    return start, end


def merge_intervals(intervals):
    """Funde intervalos sobrepostos ou encostados, guardando as origens."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: (item[0], item[1]))
    merged = [[ordered[0][0], ordered[0][1], {ordered[0][2]}]]
    for start, end, source in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
            last[2].add(source)
        else:
            merged.append([start, end, {source}])
    return [(s, e, sorted(sources)) for s, e, sources in merged]


# --------------------------------------------------------------------------- #
# Escrita do .ics
# --------------------------------------------------------------------------- #
def fold(line: str) -> str:
    out = []
    while len(line.encode("utf-8")) > 74:
        cut = 74
        while len(line[:cut].encode("utf-8")) > 74:
            cut -= 1
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def titulo_detalhado(room_name: str, sources: list) -> str:
    """Titulo de um evento na agenda pessoal: quarto e de onde veio a reserva.

    NUNCA leva nomes de hospedes: este ficheiro e publico. Os nomes vivem no
    registo de inquilinos, que fica no computador do utilizador.

    Funcao pura: verificada nos autotestes.
    """
    origens = [rotulo_curto(s.split("manual:", 1)[-1]) if s.startswith("manual:") else s
               for s in sources]
    return f"{room_name} · " + " + ".join(origens)


def rotulo_curto(texto: str, limite: int = 22) -> str:
    """Primeira parte de uma nota, para caber no titulo de um evento.

    "Nahla - reservou no anuncio do Q2, alojada aqui" -> "Nahla".
    A nota completa vai na descricao do evento, que nao ocupa espaco no ecra.
    """
    corte = re.split(r"\s[-–]\s|,|\(", texto.strip(), maxsplit=1)[0].strip()
    corte = corte or texto.strip()
    return corte if len(corte) <= limite else corte[: limite - 1].rstrip() + "…"


def build_ics(calname: str, blocks, settings: dict, detalhe: bool = False) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//Calendar Sync {VERSAO}//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        fold(f"X-WR-CALNAME:{calname}"),
        "X-WR-TIMEZONE:Europe/Lisbon",
        f"X-GENERATED-AT:{stamp}",
    ]
    for item in blocks:
        start, end, sources = item[0], item[1], item[2]
        rotulo = item[3] if len(item) > 3 else ""
        digest = hashlib.sha1(
            f"{calname}|{start.isoformat()}|{end.isoformat()}|{rotulo}|"
            f"{'+'.join(sources)}".encode()
        ).hexdigest()[:16]
        if detalhe:
            resumo = titulo_detalhado(rotulo, sources)
            origens_completas = [s.split("manual:", 1)[-1] if s.startswith("manual:") else s
                                 for s in sources]
            descricao = (f"{(end - start).days} noites. "
                         + " / ".join(origens_completas))
        else:
            resumo = settings["event_summary"]
            descricao = None
        lines += [
            "BEGIN:VEVENT",
            f"UID:{digest}@{UID_DOMAIN}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
            fold(f"SUMMARY:{resumo}"),
        ]
        if descricao:
            lines.append(fold(f"DESCRIPTION:{descricao}"))
        lines += [
            "TRANSP:OPAQUE",
            "STATUS:CONFIRMED",
            f"X-CT-ORIGIN:{ORIGIN_TAG}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


# --------------------------------------------------------------------------- #
# Configuracao
# --------------------------------------------------------------------------- #
def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as handle:
        data = json.load(handle)

    settings = dict(DEFAULT_SETTINGS)
    if isinstance(data.get("settings"), dict):
        settings.update(data["settings"])

    if "properties" in data:
        raw_properties = data["properties"]
    else:  # formatos antigos
        rooms = data.get("rooms") or {k: v for k, v in data.items() if k != "settings"}
        raw_properties = [{"id": "casa", "name": "A minha casa", "rooms": rooms}]

    properties = []
    for prop in raw_properties:
        name = prop.get("name") or prop.get("id") or "Casa"
        rooms_raw = prop.get("rooms", [])
        if isinstance(rooms_raw, dict):
            rooms_raw = [
                {
                    "id": key,
                    "name": key.replace("-", " ").capitalize(),
                    **(value if isinstance(value, dict) else {"sources": value}),
                }
                for key, value in rooms_raw.items()
            ]
        rooms = []
        for room in rooms_raw:
            room_name = room.get("name") or room.get("id") or "Quarto"
            rooms.append(
                {
                    "id": slug(room.get("id") or room_name),
                    "name": room_name,
                    "sources": [s for s in room.get("sources", []) if s.get("url")],
                    "manual_blocks": room.get("manual_blocks", []),
                    "photo": room.get("photo"),
                }
            )
        properties.append(
            {"id": slug(prop.get("id") or name), "name": name, "rooms": rooms}
        )
    return settings, properties


# --------------------------------------------------------------------------- #
# Processamento
# --------------------------------------------------------------------------- #



def e_eco(intervalo, publicados: list) -> bool:
    """O intervalo cabe inteiro dentro de algo que ja lhe demos a ler?

    Se sim, e o nosso proprio bloqueio a voltar: varias plataformas importam o
    nosso calendario e reexportam-no como se fosse delas, com identificadores
    proprios, por isso a marca de origem nao chega para os apanhar.

    E seguro descartar: se aquelas datas estao bloqueadas nessa plataforma
    porque nos as bloqueamos, ela nao pode ter recebido reserva para elas.

    Funcao pura: verificada nos autotestes.
    """
    inicio, fim = intervalo
    return any(pub_inicio <= inicio and fim <= pub_fim for pub_inicio, pub_fim in publicados)


def ler_publicado(prop_id: str, room_id: str, plataforma: str) -> list:
    caminho = os.path.join(PUBLICADO_DIR, prop_id, f"{room_id}--{slug(plataforma)}.json")
    try:
        with open(caminho, encoding="utf-8") as handle:
            return [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in json.load(handle)]
    except Exception:  # noqa: BLE001
        return []


def guardar_publicado(prop_id: str, room_id: str, plataforma: str, blocos) -> None:
    caminho = os.path.join(PUBLICADO_DIR, prop_id, f"{room_id}--{slug(plataforma)}.json")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as handle:
        json.dump([[b[0].isoformat(), b[1].isoformat()] for b in blocos], handle)


def feeds_de_um_quarto(plataformas: list, room_id: str) -> list:
    """Que ficheiros .ics gerar para um quarto.

    O ficheiro geral serve para plataformas novas. Alem dele, um por cada
    plataforma que ja e origem, sem as reservas dessa mesma plataforma:
    importar para a Spotahome as reservas da Spotahome faz a plataforma
    bloquear por cima da reserva que ela propria tem.

    Funcao pura: nao toca no disco, para poder ser verificada nos autotestes.
    """
    feeds = [{"excluir": None, "ficheiro": f"{room_id}.ics", "para": "Qualquer plataforma nova"}]
    for plataforma in sorted(set(plataformas)):
        feeds.append({
            "excluir": plataforma,
            "ficheiro": f"{room_id}--para-{slug(plataforma)}.ics",
            "para": plataforma,
        })
    return feeds


def candidatos_de_foto(prop_id: str, room_id: str) -> list:
    """Nomes de ficheiro aceites para a foto de um quarto, por ordem.

    Funcao pura: nao toca no disco, para poder ser verificada nos autotestes.
    """
    return [
        f"{FOTOS_DIR}/{prop_id}/{room_id}.{extensao}"
        for extensao in ("jpg", "jpeg", "png", "webp")
    ]


def encontrar_foto(prop_id: str, room_id: str, escolha: str | None) -> str | None:
    if escolha:  # caminho indicado a mao no calendars.json manda sempre
        return escolha if os.path.exists(escolha) else None
    for caminho in candidatos_de_foto(prop_id, room_id):
        if os.path.exists(caminho):
            return caminho
    return None


def process_room(prop: dict, room: dict, settings: dict, status: dict) -> dict:
    intervals = []
    source_report = []
    hard_failure = False

    for source in room["sources"]:
        platform = source.get("platform", "Desconhecido")
        cache_path = os.path.join(
            CACHE_DIR, prop["id"], f"{room['id']}--{slug(platform)}.ics"
        )
        print(f"    [{platform}]")

        text = fetch(source["url"])
        used_cache = False
        if text is None and settings["use_cache_on_failure"] and os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as handle:
                text = handle.read()
            used_cache = True
            print("      ~ a usar a ultima leitura guardada")

        if text is None:
            hard_failure = True
            source_report.append({"platform": platform, "state": "ERRO", "events": 0})
            continue

        if not used_cache:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as handle:
                handle.write(text)

        publicados = ler_publicado(prop["id"], room["id"], platform)
        count = 0
        ecos = 0
        for event in parse_events(text):
            interval = event_to_interval(event, settings["block_checkout_day"])
            if not interval:
                continue
            if e_eco(interval, publicados):
                ecos += 1  # bloqueio nosso, devolvido por esta plataforma
                continue
            intervals.append((interval[0], interval[1], platform))
            count += 1
        print(f"      -> {count} reserva(s)"
              + (f", {ecos} eco(s) ignorado(s)" if ecos else ""))
        source_report.append(
            {
                "platform": platform,
                "state": "CACHE" if used_cache else "OK",
                "events": count,
                "ecos": ecos,
            }
        )

    for block in room["manual_blocks"]:
        try:
            start = date.fromisoformat(block["start"])
            end = date.fromisoformat(block["end"])
            if settings["block_checkout_day"]:
                end += timedelta(days=1)
            intervals.append((start, end, "manual:" + (block.get("note") or MANUAL_LABEL)))
        except Exception:  # noqa: BLE001
            print(f"      ! bloqueio manual invalido: {block}")

    today = date.today()
    floor = today - timedelta(days=settings["keep_past_days"])
    ceiling = today + timedelta(days=int(settings["months_ahead"] * 30.5))
    clipped = [
        (max(s, floor), min(e, ceiling), src)
        for s, e, src in intervals
        if e > floor and s < ceiling
    ]
    blocks = merge_intervals([item for item in clipped if item[1] > item[0]])

    plataformas = [s.get("platform", "") for s in room["sources"] if s.get("platform")]
    feeds = feeds_de_um_quarto(plataformas, room["id"])
    calname_base = f"{prop['name']} - {room['name']}"
    feeds_publicados = []

    if hard_failure:
        print("      !! fonte em falha e sem cache -> ficheiros nao tocados "
              "(publicar dados incompletos daria overbooking)")
        for feed in feeds:
            caminho = os.path.join(OUTPUT_DIR, prop["id"], feed["ficheiro"])
            if os.path.exists(caminho):
                feeds_publicados.append(
                    {"platform": feed["excluir"], "para": feed["para"],
                     "path": f"{prop['id']}/{feed['ficheiro']}"}
                )
    else:
        os.makedirs(os.path.join(OUTPUT_DIR, prop["id"]), exist_ok=True)
        for feed in feeds:
            usados = [item for item in clipped if item[2] != feed["excluir"]]
            blocos_feed = merge_intervals([i for i in usados if i[1] > i[0]])
            nome = calname_base + ("" if feed["excluir"] is None
                                   else f" (sem {feed['excluir']})")
            caminho = os.path.join(OUTPUT_DIR, prop["id"], feed["ficheiro"])
            with open(caminho, "w", encoding="utf-8") as handle:
                handle.write(build_ics(nome, blocos_feed, settings))
            feeds_publicados.append(
                {"platform": feed["excluir"], "para": feed["para"],
                 "path": f"{prop['id']}/{feed['ficheiro']}", "blocos": len(blocos_feed)}
            )
            if feed["excluir"]:
                guardar_publicado(prop["id"], room["id"], feed["excluir"], blocos_feed)
            etiqueta = "geral" if feed["excluir"] is None else f"sem {feed['excluir']}"
            print(f"    = {len(blocos_feed)} bloco(s) [{etiqueta}] em {caminho}")

    rel_path = f"{prop['id']}/{room['id']}.ics"

    # A agenda pessoal leva UM evento por periodo ocupado, nao um por plataforma:
    # no calendario, tres bandas para a mesma estadia sao ruido. As plataformas
    # de origem vao no titulo e na descricao.        // uma banda por quarto
    detalhe_itens = []
    if not hard_failure:
        for inicio, fim, origens in blocks:
            detalhe_itens.append((inicio, fim, origens, room["name"]))
        caminho_detalhe = os.path.join(OUTPUT_DIR, prop["id"], f"{room['id']}--detalhe.ics")
        with open(caminho_detalhe, "w", encoding="utf-8") as handle:
            handle.write(build_ics(f"{calname_base} (detalhe)", detalhe_itens,
                                   settings, detalhe=True))
        feeds_publicados.append(
            {"platform": None, "para": "Agenda pessoal deste quarto", "detalhe": True,
             "path": f"{prop['id']}/{room['id']}--detalhe.ics", "blocos": len(detalhe_itens)}
        )
        print(f"    = {len(detalhe_itens)} evento(s) [detalhe] em {caminho_detalhe}")

    for report in source_report:
        status["sources"].append(
            {"casa": prop["name"], "quarto": room["name"], **report}
        )

    return {
        "id": room["id"],
        "name": room["name"],
        "ics": rel_path,
        "feeds": feeds_publicados,
        "detalhe_itens": detalhe_itens,
        "intervalos": [
            {"start": i[0].isoformat(), "end": i[1].isoformat(), "source": i[2][0]}
            for i in detalhe_itens
        ],
        "photo": encontrar_foto(prop["id"], room["id"], room.get("photo")),
        "ok": not hard_failure,
        "sources": source_report,
        "blocks": [
            {"start": s.isoformat(), "end": e.isoformat(), "sources": src}
            for s, e, src in blocks
        ],
    }


def write_dashboard(properties_data: list, settings: dict, ok: bool) -> None:
    # a configuracao viaja para o painel para o editor de ligacoes a poder
    # mostrar; sao os mesmos dados que ja estao no repositorio publico
    try:
        with open(CONFIG_FILE, encoding="utf-8") as handle:
            config_bruta = json.load(handle)
    except Exception:  # noqa: BLE001
        config_bruta = None

    payload = {
        "engine_version": VERSAO,
        "site_url": (settings.get("site_url") or "").rstrip("/"),
        "config": config_bruta,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result": "OK" if ok else "COM ERROS",
        "horizon_days": settings["dashboard_days"],
        "properties": properties_data,
    }
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as handle:
        handle.write("window.SYNC_DATA = ")
        json.dump(payload, handle, ensure_ascii=False, indent=1)
        handle.write(";\n")


# --------------------------------------------------------------------------- #
# AUTOTESTES
#
# Cada teste corresponde a uma avaria que ja chegou ao utilizador ou a uma
# regra de negocio que, se partir, publica disponibilidade errada sem dar erro.
# Correm no arranque, so em memoria (nada de disco nem de rede) e abortam o
# programa se falharem. NAO REMOVER nenhum: se um teste incomodar, e porque a
# alteracao quebrou aquilo que ele protege.
# --------------------------------------------------------------------------- #
def _evento(**campos) -> dict:
    return {chave.upper().replace("_", "-"): valor for chave, valor in campos.items()}


def _t01_dtend_exclusivo():
    intervalo = event_to_interval(_evento(DTSTART="20260901", DTEND="20260903"), False)
    if intervalo != (date(2026, 9, 1), date(2026, 9, 3)):
        return f"esperado 1 a 3 set, obtido {intervalo}"
    if (intervalo[1] - intervalo[0]).days != 2:
        return "o dia de saida deixou de estar livre"


def _t02_cancelada_ignorada():
    if event_to_interval(
        _evento(DTSTART="20260901", DTEND="20260903", STATUS="CANCELLED"), False
    ) is not None:
        return "reserva cancelada continua a bloquear datas"


def _t03_transparente_ignorado():
    if event_to_interval(
        _evento(DTSTART="20260901", DTEND="20260903", TRANSP="TRANSPARENT"), False
    ) is not None:
        return "evento marcado como livre continua a bloquear datas"


def _t04_anti_loop():
    proprio = _evento(DTSTART="20260901", DTEND="20260903", UID="abc@" + UID_DOMAIN)
    if event_to_interval(proprio, False) is not None:
        return "bloco proprio devolvido por outra plataforma volta a entrar"
    marcado = {"DTSTART": "20260901", "DTEND": "20260903", "X-CT-ORIGIN": ORIGIN_TAG}
    if event_to_interval(marcado, False) is not None:
        return "bloco com marca de origem propria volta a entrar"


def _t05_duracao():
    intervalo = event_to_interval(_evento(DTSTART="20270201", DURATION="P90D"), False)
    if intervalo != (date(2027, 2, 1), date(2027, 5, 2)):
        return f"DURATION mal convertida: {intervalo}"


def _t06_sem_dtend():
    intervalo = event_to_interval(_evento(DTSTART="20260901"), False)
    if intervalo != (date(2026, 9, 1), date(2026, 9, 2)):
        return "reserva sem data de fim deixou de valer uma noite"


def _t07_dtend_invalido():
    intervalo = event_to_interval(_evento(DTSTART="20260905", DTEND="20260901"), False)
    if intervalo != (date(2026, 9, 5), date(2026, 9, 6)):
        return "datas invertidas deixaram de ser corrigidas"


def _t08_dia_de_saida_opcional():
    intervalo = event_to_interval(_evento(DTSTART="20260901", DTEND="20260903"), True)
    if intervalo[1] != date(2026, 9, 4):
        return "block_checkout_day deixou de acrescentar o dia de saida"


def _t09_funde_sobreposto_e_encostado():
    fundido = merge_intervals([
        (date(2026, 9, 1), date(2026, 9, 10), "A"),
        (date(2026, 9, 5), date(2026, 9, 20), "B"),
        (date(2026, 9, 20), date(2026, 9, 25), "C"),
    ])
    if len(fundido) != 1 or fundido[0][1] != date(2026, 9, 25):
        return f"reservas sobrepostas deixaram de ser fundidas: {fundido}"
    if fundido[0][2] != ["A", "B", "C"]:
        return "a origem das reservas perdeu-se ao fundir"


def _t10_nao_funde_com_folga():
    fundido = merge_intervals([
        (date(2026, 9, 1), date(2026, 9, 5), "A"),
        (date(2026, 9, 6), date(2026, 9, 8), "B"),
    ])
    if len(fundido) != 2:
        return "uma noite livre entre duas reservas foi bloqueada por engano"


def _t11_linha_dobrada():
    texto = (
        "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART;VALUE=DATE:20260901\r\n"
        "SUMMARY:Reserva muito long\r\n a que continua na linha seguinte\r\n"
        "DTEND;VALUE=DATE:20260903\r\nEND:VEVENT\r\nEND:VCALENDAR"
    )
    eventos = parse_events(texto)
    if len(eventos) != 1:
        return "linha dobrada partiu o evento em dois"
    if eventos[0].get("DTEND") != "20260903":
        return "a propriedade a seguir a uma linha dobrada perdeu-se"


def _t12_dobrar_e_desdobrar():
    original = "SUMMARY:" + "reserva com nome muito comprido " * 5
    voltou = "".join(unfold(fold(original)))
    if voltou != original:
        return "dobrar e desdobrar uma linha longa alterou o conteudo"


def _t13_uid_estavel():
    blocos = [(date(2026, 9, 1), date(2026, 9, 3), ["A"])]
    definicoes = dict(DEFAULT_SETTINGS)
    primeiro = [l for l in build_ics("q", blocos, definicoes).splitlines() if l.startswith("UID:")]
    segundo = [l for l in build_ics("q", blocos, definicoes).splitlines() if l.startswith("UID:")]
    if primeiro != segundo:
        return "o UID mudou entre execucoes: as plataformas recriam os eventos"


def _t14_slug():
    if slug("Suíte João / 2º") != "suite-joao-2":
        return f"slug mal formado: {slug('Suíte João / 2º')}"
    if slug("!!!") != "item":
        return "um nome sem letras deixou de ter caminho valido"


def _t16_caminhos_de_foto():
    caminhos = candidatos_de_foto("casa-trindade", "quarto-2")
    if caminhos[0] != "fotos/casa-trindade/quarto-2.jpg":
        return f"caminho de foto inesperado: {caminhos[0]}"
    if len({c.rsplit(".", 1)[1] for c in caminhos}) != len(caminhos):
        return "extensoes repetidas na procura da foto"


def _t17_feeds_por_plataforma():
    feeds = feeds_de_um_quarto(["Spotahome", "Flatio", "Spotahome"], "quarto-2")
    if len(feeds) != 3:
        return f"esperava 3 ficheiros (geral + 2 plataformas), obtive {len(feeds)}"
    if feeds[0]["excluir"] is not None or feeds[0]["ficheiro"] != "quarto-2.ics":
        return "o ficheiro geral deixou de ser o primeiro"
    nomes = {f["ficheiro"] for f in feeds}
    if "quarto-2--para-spotahome.ics" not in nomes:
        return "falta o ficheiro sem as reservas da Spotahome"
    if len(nomes) != len(feeds):
        return "dois feeds a escrever no mesmo ficheiro"


def _t18_feed_exclui_a_propria_plataforma():
    intervalos = [
        (date(2026, 9, 1), date(2026, 9, 10), "Spotahome"),
        (date(2026, 10, 1), date(2026, 10, 5), "Flatio"),
    ]
    sem_spotahome = merge_intervals([i for i in intervalos if i[2] != "Spotahome"])
    if len(sem_spotahome) != 1 or sem_spotahome[0][0] != date(2026, 10, 1):
        return "o calendario para a Spotahome ainda leva as reservas da Spotahome"
    manual = [(date(2026, 12, 1), date(2026, 12, 5), "manual:Obras")]
    sem = merge_intervals([i for i in intervalos + manual if i[2] != "Spotahome"])
    if len(sem) != 2:
        return "os bloqueios manuais deixaram de ir em todos os calendarios"


def _t20_agenda_uma_banda_por_periodo():
    """Duas plataformas a cobrir a mesma estadia dao um evento, nao dois."""
    intervalos = [
        (date(2026, 7, 21), date(2026, 8, 31), "HousingAnywhere"),
        (date(2026, 7, 15), date(2026, 8, 8), "Flatio"),
    ]
    fundidos = merge_intervals(intervalos)
    if len(fundidos) != 1:
        return f"esperava um periodo ocupado, obtive {len(fundidos)}"
    itens = [(f[0], f[1], f[2], "Quarto 2") for f in fundidos]
    ics = build_ics("x", itens, dict(DEFAULT_SETTINGS), detalhe=True)
    if ics.count("BEGIN:VEVENT") != 1:
        return "a agenda voltou a criar um evento por plataforma"
    if "Flatio" not in ics or "HousingAnywhere" not in ics:
        return "o evento unico perdeu a origem das reservas"


def _t21_eco_de_volta():
    publicados = [(date(2026, 7, 15), date(2026, 8, 8))]
    if not e_eco((date(2026, 7, 15), date(2026, 8, 8)), publicados):
        return "o bloqueio devolvido igual ao que publicamos nao foi apanhado"
    if not e_eco((date(2026, 7, 20), date(2026, 8, 1)), publicados):
        return "um pedaco do nosso bloqueio devolvido nao foi apanhado"
    if e_eco((date(2026, 7, 10), date(2026, 8, 8)), publicados):
        return "uma reserva que comeca antes do nosso bloqueio foi descartada"
    if e_eco((date(2026, 9, 1), date(2026, 10, 1)), publicados):
        return "uma reserva noutras datas foi descartada"
    if e_eco((date(2026, 7, 15), date(2026, 8, 8)), []):
        return "sem nada publicado, uma reserva foi descartada"


def _t19_titulo_sem_nomes():
    if rotulo_curto("Nahla - reservou no anuncio do Q2, alojada aqui") != "Nahla":
        return "a nota longa deixou de ser encurtada para o titulo"
    if rotulo_curto("Obras") != "Obras":
        return "uma nota curta foi alterada sem necessidade"
    if len(rotulo_curto("x" * 40)) > 22:
        return "um rotulo sem separadores nao foi cortado"
    titulo = titulo_detalhado("Quarto 2", ["Spotahome", "manual:Hyunjoo - reserva HA"])
    if not titulo.startswith("Quarto 2 · "):
        return f"titulo inesperado: {titulo}"
    if "Spotahome" not in titulo:
        return "a origem da reserva desapareceu do titulo"
    detalhe = build_ics("x", [(date(2026, 9, 1), date(2026, 9, 3), ["Flatio"], "Quarto 1")],
                        dict(DEFAULT_SETTINGS), detalhe=True)
    if "SUMMARY:Quarto 1 · Flatio" not in detalhe:
        return "o evento com detalhe perdeu o titulo"
    simples = build_ics("x", [(date(2026, 9, 1), date(2026, 9, 3), ["Flatio"])],
                        dict(DEFAULT_SETTINGS))
    if "Flatio" in simples:
        return "o calendario publico das plataformas passou a revelar a origem"


def _t15_ics_completo():
    ics = build_ics("Casa - Quarto", [(date(2026, 9, 1), date(2026, 9, 3), ["A"])],
                    dict(DEFAULT_SETTINGS))
    if ics.count("BEGIN:VEVENT") != ics.count("END:VEVENT"):
        return "eventos abertos e fechados em numero diferente"
    if not ics.rstrip().endswith("END:VCALENDAR"):
        return "o ficheiro nao fecha o calendario"
    if "DTEND;VALUE=DATE:20260903" not in ics:
        return "a data de fim nao foi escrita como data"


AUTOTESTES = [
    ("o dia de saida fica livre (v1.0)", _t01_dtend_exclusivo),
    ("reserva cancelada nao bloqueia (v1.0)", _t02_cancelada_ignorada),
    ("evento transparente nao bloqueia (v1.0)", _t03_transparente_ignorado),
    ("bloco proprio nao reentra em ciclo (v2.0)", _t04_anti_loop),
    ("reserva expressa em duracao (v3.0)", _t05_duracao),
    ("reserva sem data de fim (v1.0)", _t06_sem_dtend),
    ("datas invertidas (v1.0)", _t07_dtend_invalido),
    ("bloquear o dia de saida quando pedido (v2.0)", _t08_dia_de_saida_opcional),
    ("reservas repetidas aparecem uma vez (v1.0)", _t09_funde_sobreposto_e_encostado),
    ("uma noite livre nao e bloqueada (v2.0)", _t10_nao_funde_com_folga),
    ("linha dobrada nao parte o evento (v1.0)", _t11_linha_dobrada),
    ("dobrar e desdobrar nao altera texto (v3.0)", _t12_dobrar_e_desdobrar),
    ("o UID nao muda entre execucoes (v2.0)", _t13_uid_estavel),
    ("nomes com acentos dao caminhos validos (v3.0)", _t14_slug),
    ("o .ics gerado fecha bem (v1.0)", _t15_ics_completo),
    ("a foto do quarto e procurada pelo nome (v3.5)", _t16_caminhos_de_foto),
    ("um calendario por plataforma (v3.7)", _t17_feeds_por_plataforma),
    ("a agenda pessoal nao leva nomes (v3.8)", _t19_titulo_sem_nomes),
    ("uma banda por periodo ocupado (v3.15)", _t20_agenda_uma_banda_por_periodo),
    ("o nosso bloqueio devolvido e ignorado (v3.16)", _t21_eco_de_volta),
    ("cada calendario exclui a sua plataforma (v3.7)", _t18_feed_exclui_a_propria_plataforma),
]


def correr_autotestes() -> list:
    falhas = []
    for nome, verificacao in AUTOTESTES:
        try:
            queixa = verificacao()
        except Exception as exc:  # noqa: BLE001
            queixa = f"rebentou: {exc}"
        if queixa:
            falhas.append(f"{nome} -> {queixa}")
    return falhas


def main() -> int:
    falhas = correr_autotestes()
    if falhas:
        print("!" * 70)
        print("AUTOTESTES FALHARAM — nada foi publicado.")
        for falha in falhas:
            print("  - " + falha)
        print("!" * 70)
        return 2
    print(f"Calendar Sync {VERSAO} · {len(AUTOTESTES)} autotestes ok\n")

    settings, properties = load_config()
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": [],
    }
    properties_data = []
    ok = True

    for prop in properties:
        print(f"[{prop['name']}]")
        rooms_data = []
        for room in prop["rooms"]:
            print(f"  ({room['name']})")
            if not room["sources"] and not room["manual_blocks"]:
                print("    sem links configurados, a saltar")
                continue
            room_data = process_room(prop, room, settings, status)
            ok = room_data["ok"] and ok
            rooms_data.append(room_data)
        if rooms_data:
            agenda = []
            for quarto in rooms_data:
                agenda.extend(quarto.pop("detalhe_itens", []))
            if agenda:
                caminho = os.path.join(OUTPUT_DIR, prop["id"], "agenda.ics")
                os.makedirs(os.path.dirname(caminho), exist_ok=True)
                with open(caminho, "w", encoding="utf-8") as handle:
                    handle.write(build_ics(f"{prop['name']} (agenda)", sorted(agenda),
                                           settings, detalhe=True))
                print(f"  = {len(agenda)} evento(s) na agenda de {prop['name']}: {caminho}")
                for quarto in rooms_data:
                    quarto["agenda"] = f"{prop['id']}/agenda.ics"
        if rooms_data:
            properties_data.append(
                {"id": prop["id"], "name": prop["name"], "rooms": rooms_data}
            )

    write_dashboard(properties_data, settings, ok)
    status["result"] = "OK" if ok else "COM ERROS"
    with open(STATUS_FILE, "w", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2, ensure_ascii=False)

    if not ok:
        print("\nTerminou COM ERROS: ha pelo menos uma plataforma inacessivel.")
        return 1
    print("\nTudo sincronizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
