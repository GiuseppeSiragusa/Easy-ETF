# ETF World Intelligence — Live Data Backend

Autore/progetto: **Giuseppe Siragusa**

Questo backend mantiene le API key fuori dall'APK e fornisce dati reali alla UI.

## Provider previsti
- Twelve Data: quotazioni, storico e directory ETF.
- Alpha Vantage: notizie finanziarie e sentiment, ETF profile/holdings (fase successiva).
- FRED: macro USA/globali.
- ECB: macro/cambi europei via SDMX.

## Avvio locale
1. `python -m venv .venv`
2. Attiva l'ambiente virtuale.
3. `pip install -r requirements.txt`
4. Copia `.env.example` in `.env` e inserisci le API key.
5. Esporta le variabili oppure avvia con un loader `.env`.
6. `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
7. Apri `http://127.0.0.1:8000/docs` per testare gli endpoint.

## Principio di sicurezza
Non inserire mai le API key in `app.js`, `index.html`, `BuildConfig` o nel repository pubblico.
