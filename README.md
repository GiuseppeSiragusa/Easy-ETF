# Easy ETF — ETF World Intelligence

Progetto e ideazione: **Giuseppe Siragusa**

Web app/PWA per l'analisi informativa di ETF UCITS. Include Smart Scanner, Opportunity Score, Confidence Score e Decision Report.

## Stato

Il frontend in `docs/` funziona anche offline ed è predisposto per GitHub Pages. I dati reali richiedono il backend FastAPI in `backend/`, pubblicato tramite HTTPS e configurato con chiavi provider lato server.

## Sicurezza

Le chiavi API non devono essere inserite nel frontend o salvate nel repository. Copiare `backend/.env.example` in `backend/.env` soltanto nell'ambiente server.

## Avvio backend

```bash
cd backend
cp .env.example .env
docker compose up --build
```

Impostare quindi nella pagina Impostazioni della PWA l'URL HTTPS del backend.

## Avvertenza

I punteggi e i report sono strumenti informativi e non costituiscono consulenza finanziaria né previsioni garantite.
