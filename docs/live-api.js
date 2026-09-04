/* ETF World Intelligence - secure backend bridge */
(() => {
  const DEFAULT_BASE = localStorage.getItem('ewi_api_base') || '';
  window.EWI = {
    apiBase: DEFAULT_BASE,
    setApiBase(url) {
      this.apiBase = String(url || '').trim().replace(/\/$/, '');
      localStorage.setItem('ewi_api_base', this.apiBase);
    },
    async get(path) {
      if (!this.apiBase) throw new Error('Backend HTTPS non ancora configurato');
      const ctl = new AbortController();
      const timer = setTimeout(() => ctl.abort(), 15000);
      try {
        const r = await fetch(this.apiBase + path, {headers:{Accept:'application/json'}, signal:ctl.signal});
        if (!r.ok) {
          let message = `HTTP ${r.status}`;
          try { const d = await r.json(); message = d.detail || message; } catch (_) {}
          throw new Error(message);
        }
        return await r.json();
      } finally { clearTimeout(timer); }
    },
    health(){ return this.get('/api/health'); },
    dashboard(){ return this.get('/api/dashboard'); },
    news(limit=30){ return this.get(`/api/news?limit=${encodeURIComponent(limit)}`); },
    scanner(params={}){ const q=new URLSearchParams(params).toString(); return this.get('/api/scanner'+(q?'?'+q:'')); },
    scannerUniverse(search=''){ const q=search?`?search=${encodeURIComponent(search)}`:''; return this.get('/api/scanner/universe'+q); },
    intelligence(symbol, exchange=''){
      const q=exchange?`?exchange=${encodeURIComponent(exchange)}`:'';
      return this.get(`/api/intelligence/${encodeURIComponent(symbol)}${q}`);
    },
    report(symbol, exchange=''){
      const q=exchange?`?exchange=${encodeURIComponent(exchange)}`:'';
      return this.get(`/api/report/${encodeURIComponent(symbol)}${q}`);
    }
  };
})();
