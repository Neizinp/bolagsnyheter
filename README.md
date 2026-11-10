# Rapport

En avskalad läsare för bolagens rapportmeddelanden från Cisions svenska RSS-sökning. Visar högst fyra rapporter per nyhetsrum och länkar till originalet. Data hämtas endast manuellt med knappen Hämta. Välj ett bolag för att söka dess rapporter; med Alla bolag valt hämtas de senaste träffarna globalt. Rapporter sparas lokalt i webbläsaren mellan hämtningar och delas inte mellan enheter. Hämtningen går via r.jina.ai eftersom Cision inte tillåter direkt åtkomst från webbläsaren.

## Begränsningar

Cisions nyhetsrum är inte en lista över Nasdaq Stockholm. Andra marknadsplatser och onoterade bolag kan förekomma, och bolag som använder andra distributörer kan saknas. Ingen fullständig börstäckning eller fyra tillgängliga rapporter per bolag kan garanteras. Nyhetsrumsnamn skapas från Cisions adresser och kan därför vara ofullständiga. Sökning, rapportidentifiering och dubblettkontroll är automatiska och kan missa eller felklassificera meddelanden. Utdragen är Cisions ingress, inte normaliserade finansiella nyckeltal. Kontrollera alltid originalrapporten.

## Lokalt

Kör `python3 -m http.server 8000 --directory docs` och öppna `http://localhost:8000`. Uppdatera den gemensamma datafilen manuellt med `python3 scripts/fetch_reports.py 5` eller ett enskilt nyhetsrum med `python3 scripts/fetch_reports.py --company sandvik`. Fyll på nyhetsrum som har färre än fyra rapporter med `python3 scripts/fetch_reports.py --backfill` (valfritt ett startnamn som andra argument för att återuppta). Hämtningen återanvänder tidigare rapporter och behåller högst fyra per nyhetsrum. Vid ett avbrott sparas lokala delresultat men kommandot returnerar ett fel.

## Publicering

GitHub Pages kan publicera från `main` och katalogen `/docs`. Cisions RSS är en extern tjänst och ändringar, driftstörningar eller villkor kan påverka tillgängligheten.