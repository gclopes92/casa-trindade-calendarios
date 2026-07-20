window.SYNC_DATA = {
 "engine_version": "3.4",
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
      "manual_blocks": []
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
        "platform": "Flatio",
        "url": "https://app.flatio.com/en/front/calendar/export?hash=ma40jkvo5t30arr84w5s.ics"
       },
       {
        "platform": "HousingAnywhere",
        "url": ""
       }
      ],
      "manual_blocks": []
     }
    ]
   }
  ]
 },
 "generated_at": "2026-07-20T19:10:10+00:00",
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
       "start": "2026-07-19",
       "end": "2026-08-08",
       "sources": [
        "HousingAnywhere"
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
     ]
    },
    {
     "id": "quarto-2",
     "name": "Quarto 2",
     "ics": "casa-trindade/quarto-2.ics",
     "ok": true,
     "sources": [
      {
       "platform": "Spotahome",
       "state": "OK",
       "events": 1
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
       "end": "2026-08-08",
       "sources": [
        "Flatio"
       ]
      },
      {
       "start": "2026-09-01",
       "end": "2027-01-31",
       "sources": [
        "Spotahome"
       ]
      }
     ]
    }
   ]
  }
 ]
};
