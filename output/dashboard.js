window.SYNC_DATA = {
 "engine_version": "3.12",
 "site_url": "",
 "config": {
  "settings": {
   "block_checkout_day": false,
   "keep_past_days": 7,
   "months_ahead": 24,
   "use_cache_on_failure": true,
   "event_summary": "Nao disponivel",
   "dashboard_days": 210
  },
  "properties": [
   {
    "id": "casa-trindade",
    "name": "Casa Trindade",
    "rooms": [
     {
      "id": "quarto-1",
      "name": "Quarto 1",
      "sources": [
       {
        "platform": "Spotahome",
        "url": "https://api.spotahome.com/public/calendar/1510605.ics?k=97cc43ef79f14f7652d3ceb8742556c2fda2fd0cfddfecbb9602fcd7d4b20ff3"
       },
       {
        "platform": "Flatio",
        "url": "https://app.flatio.com/en/front/calendar/export?hash=rozjo07x0fzsm24zha5j.ics"
       },
       {
        "platform": "HousingAnywhere",
        "url": "https://housinganywhere.com/api/v2/listing/2418108/calendar/9d9ac28226bd68630a91cd4ab792cf8c/en"
       }
      ],
      "manual_blocks": [
       {
        "start": "2026-07-15",
        "end": "2026-08-08",
        "note": "Nahla - reservou no anuncio do Q2, alojada aqui"
       }
      ]
     },
     {
      "id": "quarto-2",
      "name": "Quarto 2",
      "sources": [
       {
        "platform": "Spotahome",
        "url": "https://api.spotahome.com/public/calendar/1510606.ics?k=5f0de050590d7bb153e1215f8f1591cb4270de2e25b970bd2248a8d7a5afddcd"
       },
       {
        "platform": "HousingAnywhere",
        "url": "https://housinganywhere.com/api/v2/listing/2418120/calendar/3c88b00f595f032519419daa6205ae50/en"
       },
       {
        "platform": "Flatio",
        "url": "https://app.flatio.com/en/front/calendar/export?hash=ma40jkvo5t30arr84w5s.ics"
       }
      ],
      "manual_blocks": [
       {
        "start": "2026-07-21",
        "end": "2026-08-31",
        "note": "Hyunjoo - reserva HA no anuncio deste quarto"
       }
      ]
     }
    ]
   }
  ]
 },
 "generated_at": "2026-07-20T22:59:41+00:00",
 "result": "OK",
 "horizon_days": 210,
 "properties": [
  {
   "id": "casa-trindade",
   "name": "Casa Trindade",
   "rooms": [
    {
     "id": "quarto-1",
     "name": "Quarto 1",
     "ics": "casa-trindade/quarto-1.ics",
     "feeds": [
      {
       "platform": null,
       "para": "Qualquer plataforma nova",
       "path": "casa-trindade/quarto-1.ics",
       "blocos": 2
      },
      {
       "platform": "Flatio",
       "para": "Flatio",
       "path": "casa-trindade/quarto-1--para-flatio.ics",
       "blocos": 2
      },
      {
       "platform": "HousingAnywhere",
       "para": "HousingAnywhere",
       "path": "casa-trindade/quarto-1--para-housinganywhere.ics",
       "blocos": 2
      },
      {
       "platform": "Spotahome",
       "para": "Spotahome",
       "path": "casa-trindade/quarto-1--para-spotahome.ics",
       "blocos": 2
      },
      {
       "platform": null,
       "para": "Agenda pessoal deste quarto",
       "detalhe": true,
       "path": "casa-trindade/quarto-1--detalhe.ics",
       "blocos": 4
      }
     ],
     "photo": "fotos/casa-trindade/quarto-1.jpg",
     "ok": true,
     "sources": [
      {
       "platform": "Spotahome",
       "state": "OK",
       "events": 2
      },
      {
       "platform": "Flatio",
       "state": "OK",
       "events": 0
      },
      {
       "platform": "HousingAnywhere",
       "state": "OK",
       "events": 2
      }
     ],
     "blocks": [
      {
       "start": "2026-07-15",
       "end": "2026-08-08",
       "sources": [
        "HousingAnywhere",
        "manual:Nahla - reservou no anuncio do Q2, alojada aqui"
       ]
      },
      {
       "start": "2026-09-01",
       "end": "2026-12-18",
       "sources": [
        "HousingAnywhere",
        "Spotahome"
       ]
      }
     ],
     "agenda": "casa-trindade/agenda.ics"
    },
    {
     "id": "quarto-2",
     "name": "Quarto 2",
     "ics": "casa-trindade/quarto-2.ics",
     "feeds": [
      {
       "platform": null,
       "para": "Qualquer plataforma nova",
       "path": "casa-trindade/quarto-2.ics",
       "blocos": 1
      },
      {
       "platform": "Flatio",
       "para": "Flatio",
       "path": "casa-trindade/quarto-2--para-flatio.ics",
       "blocos": 1
      },
      {
       "platform": "HousingAnywhere",
       "para": "HousingAnywhere",
       "path": "casa-trindade/quarto-2--para-housinganywhere.ics",
       "blocos": 2
      },
      {
       "platform": "Spotahome",
       "para": "Spotahome",
       "path": "casa-trindade/quarto-2--para-spotahome.ics",
       "blocos": 1
      },
      {
       "platform": null,
       "para": "Agenda pessoal deste quarto",
       "detalhe": true,
       "path": "casa-trindade/quarto-2--detalhe.ics",
       "blocos": 6
      }
     ],
     "photo": "fotos/casa-trindade/quarto-2.jpg",
     "ok": true,
     "sources": [
      {
       "platform": "Spotahome",
       "state": "OK",
       "events": 1
      },
      {
       "platform": "HousingAnywhere",
       "state": "OK",
       "events": 3
      },
      {
       "platform": "Flatio",
       "state": "OK",
       "events": 1
      }
     ],
     "blocks": [
      {
       "start": "2026-07-15",
       "end": "2027-01-31",
       "sources": [
        "Flatio",
        "HousingAnywhere",
        "Spotahome",
        "manual:Hyunjoo - reserva HA no anuncio deste quarto"
       ]
      }
     ],
     "agenda": "casa-trindade/agenda.ics"
    }
   ]
  }
 ]
};
