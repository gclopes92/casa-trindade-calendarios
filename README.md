# Sincronizador de calendários (v3.2)

Junta os links iCal de várias plataformas (Spotahome, Flatio, Uniplaces,
HousingAnywhere…) num único `.ics` por quarto, com link público estável,
atualização automática de 15 em 15 minutos e um painel para veres o estado.
Suporta **várias casas, cada uma com vários quartos**.

## Ficheiros

```
merge_calendars.py                    motor de sincronização (sem dependências)
verificar.py                          verificador estático, corre num comando
calendars.json                        casas, quartos e links das plataformas
index.html                            painel de disponibilidade
.github/workflows/sync-calendars.yml  agendamento automático
output/<casa>/<quarto>.ics            gerado — é isto que colas nas plataformas
output/dashboard.js                   gerado — dados que o painel lê
status.json                           gerado — estado da última sincronização
cache/                                gerado — rede de segurança, não apagar
```

## Instalação (uma vez, ~5 minutos)

1. Cria um repositório público no GitHub (o `.ics` só tem datas, sem dados
   pessoais dos hóspedes, e precisa de ser público para as plataformas o lerem).
2. Faz upload dos ficheiros mantendo a pasta `.github/workflows/`.
3. Separador **Actions** → aceita ativar as Actions → "Sync calendars" →
   **Run workflow**.
4. Separador **Settings → Pages** → Source: *Deploy from a branch*,
   Branch: `main`, pasta `/ (root)`. Guarda.
5. Um minuto depois tens:
   - painel: `https://<utilizador>.github.io/<repo>/`
   - calendário de um quarto: `https://<utilizador>.github.io/<repo>/output/casa-trindade/quarto-2.ics`

É o segundo link que colas em qualquer plataforma que aceite importar calendário.


## Antes de alterar seja o que for

O projeto defende-se sozinho de três maneiras, e nenhuma substitui as outras:

```
python verificar.py          lê os ficheiros e procura erros de texto
python merge_calendars.py    corre 15 autotestes antes de publicar seja o que for
abrir o index.html           8 verificações correm ao abrir; falha = aviso vermelho no topo
```

Os autotestes do motor **abortam a publicação** se falharem: mais vale não
atualizar o calendário do que publicar disponibilidade errada. Cada teste
corresponde a uma avaria que já aconteceu — a lista está no bloco de manutenção
no topo do `merge_calendars.py`, e é aí que se acrescenta a próxima.

A versão aparece ao lado do título no painel. Quando reportares um problema com
uma captura de ecrã, é o primeiro número a olhar: se o painel e o motor
estiverem em versões diferentes, a etiqueta fica vermelha.

## Configuração (`calendars.json`)

```json
{
  "settings": { "block_checkout_day": false },
  "properties": [
    {
      "id": "casa-trindade",
      "name": "Casa Trindade",
      "rooms": [
        {
          "id": "quarto-2",
          "name": "Quarto 2",
          "sources": [
            { "platform": "Spotahome", "url": "https://..." },
            { "platform": "Flatio", "url": "https://..." }
          ],
          "manual_blocks": [
            { "start": "2026-08-08", "end": "2026-08-20", "note": "Obras" }
          ]
        }
      ]
    }
  ]
}
```

Para acrescentar uma casa, junta outro objeto a `properties`. Para acrescentar
um quarto, outro objeto a `rooms`. O `id` define o caminho do ficheiro, por isso
não o mudes depois de já teres dado o link às plataformas.

### Opções (`settings`)

| Opção | Por omissão | O que faz |
|---|---|---|
| `block_checkout_day` | `false` | Em iCal o dia de saída fica livre para nova entrada. `true` bloqueia-o também (limpezas, arrendamento mensal). |
| `keep_past_days` | `7` | Dias passados que ficam no ficheiro. |
| `months_ahead` | `24` | Horizonte máximo publicado. |
| `use_cache_on_failure` | `true` | Usa a última leitura boa quando a plataforma não responde. |
| `event_summary` | `Nao disponivel` | Texto dos blocos publicados. |
| `dashboard_days` | `210` | Horizonte inicial da fita no painel. |

### Bloqueios manuais

`manual_blocks` serve para o que não vem de nenhuma plataforma: obras, uso
pessoal, inquilino com contrato direto. O `end` é exclusivo, tal como no iCal.

## Painel

Abre a página do GitHub Pages (ou o `index.html` diretamente, se tiveres o
repositório no computador). Mostra, por casa:

- a fita de disponibilidade — cada quarto uma linha, cada bloco uma reserva;
  cada plataforma tem a sua cor, ocre é bloqueio teu, a marca vermelha é hoje;
  uma barra com duas cores é uma reserva conhecida por duas plataformas;
- por quarto: livre ou ocupado até quando, próxima entrada, ocupação nos
  próximos 90 dias e o botão para copiar o link do calendário;
- botão **Ajuda**: explica a fita, as cores e o que fazer quando algo fica
  vermelho. O texto vive na constante `AJUDA` dentro do `index.html` e
  atualiza-se na mesma alteração que muda o comportamento;
- botão **Ligações**: colas aí os endereços de exportação das plataformas e o
  nome é adivinhado pelo endereço. Não grava nada — monta o texto do
  `calendars.json` para copiares e colares no GitHub;
- o estado de cada plataforma.

## Quando algo corre mal

O workflow fica vermelho e o GitHub envia email. No painel e no `status.json`:

- `OK` — leitura direta da plataforma
- `CACHE` — não respondeu, usou-se a última leitura boa
- `ERRO` — não respondeu e não havia cache; o ficheiro do quarto ficou
  intencionalmente na versão anterior, para nunca publicares disponibilidade
  a mais

## Correr localmente

```
python merge_calendars.py
```

Python 3.9+, sem instalar nada.

## Limites conhecidos

- O atraso real é o intervalo de sincronização (15 min) mais o tempo que cada
  plataforma leva a reler o teu link — algumas só o fazem de hora a hora. O
  Smoobu tem exatamente a mesma limitação, porque o protocolo é o mesmo.
- Reservas com menos de um dia de intervalo entre si aparecem fundidas num só
  bloco. Para efeitos de disponibilidade é equivalente.
