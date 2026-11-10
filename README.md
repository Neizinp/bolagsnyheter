# Rapport

En avskalad läsare för bolagens rapportmeddelanden från Cisions svenska RSS-sökning. Visar högst fyra rapporter per nyhetsrum och länkar till originalet. GitHub Actions uppdaterar data var sjätte timme.

## Begränsningar

Cisions nyhetsrum är inte en lista över Nasdaq Stockholm. Andra marknadsplatser och onoterade bolag kan förekomma, och bolag som använder andra distributörer kan saknas. Ingen fullständig börstäckning eller fyra tillgängliga rapporter per bolag kan garanteras. Nyhetsrumsnamn skapas från Cisions adresser och kan därför vara ofullständiga. Sökning, rapportidentifiering och dubblettkontroll är automatiska och kan missa eller felklassificera meddelanden. Utdragen är Cisions ingress, inte normaliserade finansiella nyckeltal. Kontrollera alltid originalrapporten.

## Lokalt

Kör `python3 -m http.server 8000 --directory docs` och öppna `http://localhost:8000`. Uppdatera data med `python3 scripts/fetch_reports.py 5`; argumentet anger antal sidor per sökterm. Hämtningen återanvänder tidigare rapporter och behåller högst fyra per nyhetsrum. Vid ett avbrott sparas lokala delresultat men kommandot returnerar ett fel; arbetsflödet publicerar inte en misslyckad uppdatering.

## Publicering

GitHub Pages kan publicera från `main` och katalogen `/docs`. Arbetsflödet uppdaterar rapportfilen automatiskt. Cisions RSS är en extern tjänst och ändringar, driftstörningar eller villkor kan påverka tillgängligheten.