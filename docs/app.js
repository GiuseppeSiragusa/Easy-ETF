let etfs=[
 {symbol:'VWCE',name:'Vanguard FTSE All-World UCITS',cat:'Azionario globale',quality:94,opp:82,confidence:72,trend:'Demo',dd:'ND',news:50,view:'Demo',rating:'watch',buy:false,why:['Collega il backend per caricare quotazioni e segnali reali']},
 {symbol:'EUNL',name:'iShares Core MSCI World UCITS',cat:'Mercati sviluppati',quality:92,opp:76,confidence:72,trend:'Demo',dd:'ND',news:50,view:'Demo',rating:'watch',buy:false,why:['Collega il backend per caricare quotazioni e segnali reali']},
 {symbol:'VUAA',name:'Vanguard S&P 500 UCITS',cat:'USA large cap',quality:91,opp:67,confidence:72,trend:'Demo',dd:'ND',news:50,view:'Demo',rating:'watch',buy:false,why:['Collega il backend per caricare quotazioni e segnali reali']}
];
let news=[];
let live=false;
let selectedSymbol='VWCE';
const pages={dashboard:['Panoramica','Capisci subito cosa sta succedendo e dove vale la pena approfondire.'],news:['Notizie','Le notizie sono ordinate per impatto potenziale, non semplicemente per popolarità.'],etfs:['ETF','Confronta qualità strutturale e convenienza del momento.'],scanner:['Scanner','Cerca automaticamente gli ETF che meritano un’analisi più profonda.'],signals:['Opportunità','Zone da approfondire quando prezzo, trend, rischio e notizie sono coerenti.'],reports:['Report','Una spiegazione completa del perché un ETF è stato segnalato.'],settings:['Impostazioni','Configura fonti, universo ETF e profondità dell’analisi.']};
const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const fmt=v=>v===null||v===undefined?'ND':v;
function ratingText(r,view){return view|| (r==='good'?'Interessante':r==='watch'?'Da monitorare':'Attendere')}
function setLiveState(ok,msg=''){
 live=ok; document.documentElement.dataset.liveBackend=ok?'online':'offline';
 const dot=document.querySelector('.last-update i'); if(dot) dot.style.background=ok?'var(--green)':'var(--amber)';
 const b=document.querySelector('#updated-at'); if(b) b.textContent=ok?'live':'offline';
 const hero=document.querySelector('.market-hero .pill'); if(hero) hero.textContent=ok?'DATI REALI':'MODALITÀ OFFLINE';
 if(msg) console.info(msg);
}
function topEtfs(){document.querySelector('#top-etfs').innerHTML=etfs.slice(0,3).map(e=>`<article class="op-card" onclick="openReport('${esc(e.symbol)}')"><div class="op-top"><div><div class="ticker">${esc(e.symbol)}</div><div class="fund-name">${esc(e.name)}</div></div><span class="rating ${esc(e.rating)}">${esc(ratingText(e.rating,e.view))}</span></div><div class="dual-score"><div class="score-box"><span>QUALITÀ ETF</span><strong>${fmt(e.quality)}</strong><small>/100</small></div><div class="score-box"><span>OPPORTUNITÀ ORA</span><strong>${fmt(e.opp)}</strong><small>/100</small></div></div><div class="why-list">${e.why.map(w=>`<span>${esc(w)}</span>`).join('')}</div><div class="op-bottom"><span>${esc(e.cat)}</span><b>Affidabilità ${fmt(e.confidence)}% →</b></div></article>`).join('')}
function impactNews(){const items=news.slice(0,4);document.querySelector('#impact-news').innerHTML=items.length?items.map(n=>`<div class="news-row"><div class="row-top"><div><div class="news-title">${esc(n.title)}</div><div class="muted">${esc(n.source||n.region||'')} · ${esc((n.themes||[]).join(' · ')||n.topic||'Mercati')}</div></div><span class="impact-badge ${n.impact==='high'?'impact-high':'impact-mid'}">${n.impact==='high'?'ALTO':'MEDIO'}</span></div><div class="expert-only muted" style="margin-top:7px">Impact score ${fmt(n.score)}/100 · Sentiment ${esc(n.sent)}</div></div>`).join(''):'<div class="muted" style="padding:18px 0">Nessuna news reale caricata. Configura Alpha Vantage nel backend.</div>'}
function newsList(){document.querySelector('#news-list').innerHTML=news.length?news.map(n=>`<div class="news-row" data-impact="${esc(n.impact)}" data-sent="${esc(n.sent)}"><div class="row-top"><div><div class="news-title">${esc(n.title)}</div><div class="muted">${esc(n.source||'')} · ${esc((n.themes||[]).join(' · ')||'Mercati')}</div></div><span class="impact-badge ${n.impact==='high'?'impact-high':'impact-mid'}">${n.impact==='high'?'ALTO':'MEDIO'}</span></div><p class="muted" style="font-size:13px;line-height:1.55">${esc(n.why||n.summary||'')}</p><div class="expert-only muted">Sentiment: ${esc(n.sent)} · Impact score: ${fmt(n.score)}/100</div></div>`).join(''):'<div class="panel"><b>News non disponibili</b><p class="muted">Il backend è attivo ma il provider news non è configurato o non ha restituito risultati.</p></div>'}
function etfCards(){document.querySelector('#etf-cards').innerHTML=etfs.map(e=>`<article class="etf-detail-card" onclick="openReport('${esc(e.symbol)}')"><div class="etf-detail-top"><div><div class="ticker">${esc(e.symbol)}</div><div class="fund-name">${esc(e.name)}</div></div><span class="rating ${esc(e.rating)}">${esc(ratingText(e.rating,e.view))}</span></div><div class="score-lines"><div class="score-line"><label><span>Qualità ETF</span><b>${fmt(e.quality)}/100</b></label><div class="bar"><i style="width:${Number(e.quality)||0}%"></i></div></div><div class="score-line opportunity"><label><span>Opportunità attuale</span><b>${fmt(e.opp)}/100</b></label><div class="bar"><i style="width:${Number(e.opp)||0}%"></i></div></div></div><div class="why-list" style="margin-top:14px">${e.why.slice(0,3).map(w=>`<span>${esc(w)}</span>`).join('')}</div><div class="expert-meta expert-only"><div><span>Trend</span><b>${esc(e.trend)}</b></div><div><span>Drawdown</span><b>${esc(e.dd)}</b></div><div><span>Confidence</span><b>${fmt(e.confidence)}%</b></div></div></article>`).join('')}
function etfTable(){document.querySelector('#etf-table').innerHTML=etfs.map(e=>`<tr><td><b>${esc(e.symbol)}</b><div class="muted">${esc(e.name)}</div></td><td>${esc(e.cat)}</td><td>${fmt(e.quality)}</td><td>${fmt(e.opp)}</td><td>${esc(e.trend)}</td><td>${esc(e.dd)}</td><td>${fmt(e.news)}/100</td></tr>`).join('')}
function signals(){const buys=etfs.filter(e=>e.buy);document.querySelector('#signals-list').innerHTML=buys.length?buys.map(e=>`<div class="signal-row"><div class="signal-title"><div><div class="ticker">${esc(e.symbol)}</div><div class="fund-name">${esc(e.name)}</div></div><span class="rating good">BUY ZONE WATCH</span></div><p><b>Perché è interessante:</b> ${esc(e.why.join('. '))}.</p><div class="report-summary"><div class="report-box"><span>QUALITÀ</span><strong>${fmt(e.quality)}/100</strong></div><div class="report-box"><span>OPPORTUNITÀ</span><strong>${fmt(e.opp)}/100</strong></div><div class="report-box"><span>AFFIDABILITÀ</span><strong>${fmt(e.confidence)}%</strong></div></div><span class="tag">Ingresso a tranche</span><span class="tag">Rivalutare dopo news macro</span><span class="tag">No leva</span></div>`).join(''):'<div class="panel"><b>Nessuna Buy Zone confermata</b><p class="muted">Il motore non vede abbastanza coerenza tra prezzo, trend, notizie e affidabilità dei dati.</p></div>'}
function reportLocal(symbol='VWCE'){selectedSymbol=symbol;const e=etfs.find(x=>x.symbol===symbol)||etfs[0];document.querySelector('#report-preview').innerHTML=`<div class="report"><div class="row-top"><div><h3>${esc(e.symbol)} — ${esc(e.name)}</h3><div class="muted">${live?'Report derivato dai dati reali disponibili':'Anteprima offline — nessun dato di mercato inventato'}</div></div><span class="rating ${esc(e.rating)}">${esc(ratingText(e.rating,e.view))}</span></div><div class="report-summary"><div class="report-box"><span>QUALITÀ ETF</span><strong>${fmt(e.quality)}/100</strong></div><div class="report-box"><span>OPPORTUNITÀ</span><strong>${fmt(e.opp)}/100</strong></div><div class="report-box"><span>AFFIDABILITÀ</span><strong>${fmt(e.confidence)}%</strong></div></div><p><b>Motivazioni:</b> ${esc(e.why.join('. '))}.</p><div class="expert-only"><p><b>Dati tecnici:</b> trend ${esc(e.trend)}, drawdown ${esc(e.dd)}, news impact ${fmt(e.news)}/100.</p></div></div>`}
async function report(symbol='VWCE'){
 reportLocal(symbol);
 if(!live||!window.EWI) return;
 try{
  const r=await window.EWI.report(symbol);
  const reasons=(r.reasons||[]).map(x=>`<li>${esc(x)}</li>`).join('');
  const comps=Object.entries(r.score_components||{}).map(([k,v])=>`<span class="tag">${esc(k)} ${v>=0?'+':''}${fmt(v)}</span>`).join('');
  const top=(r.news_impact?.top_news||[]).map(n=>`<div class="news-row"><div class="news-title">${esc(n.title)}</div><div class="muted">${esc(n.source)} · impatto ${fmt(n.impact)}</div></div>`).join('');
  document.querySelector('#report-preview').innerHTML=`<div class="report"><div class="row-top"><div><h3>${esc(r.title)}</h3><div class="muted">Generato ${new Date(r.generated_at).toLocaleString('it-IT')} · Giuseppe Siragusa</div></div><span class="rating ${r.summary.signal==='Attendere'?'wait':'good'}">${esc(r.summary.signal)}</span></div><div class="report-summary"><div class="report-box"><span>QUALITÀ ETF</span><strong>${fmt(r.summary.quality_score)}/100</strong></div><div class="report-box"><span>OPPORTUNITÀ</span><strong>${fmt(r.summary.opportunity_score)}/100</strong></div><div class="report-box"><span>AFFIDABILITÀ</span><strong>${fmt(r.summary.confidence_score)}%</strong></div></div><p><b>Prezzo:</b> ${fmt(r.market_data.price)} ${esc(r.market_data.currency||'')} · <b>Drawdown:</b> ${fmt(r.market_data.drawdown_pct)}% · <b>Trend:</b> ${esc(r.market_data.trend)}</p><h4>Perché</h4><ul>${reasons}</ul><h4>Componenti dello score</h4><div>${comps}</div>${top?`<h4>Notizie più pertinenti</h4>${top}`:''}<p class="muted"><b>Fonti:</b> ${(r.sources||[]).map(esc).join(', ')}</p><p class="muted">${esc(r.risk_note)}</p></div>`;
 }catch(err){console.warn('Report live:',err.message)}
}

function scannerCard(e,idx){return `<article class="scanner-card" onclick="openReport('${esc(e.symbol)}')"><div class="scanner-head"><div class="scanner-title"><div class="scanner-rank">${idx+1}</div><div><div class="ticker">${esc(e.symbol)}</div><div class="fund-name">${esc(e.name)}</div><div class="muted">${esc(e.cat)}</div></div></div><span class="rating ${esc(e.rating)}">${esc(ratingText(e.rating,e.view))}</span></div><div class="scanner-scores"><div class="scanner-score"><span>QUALITÀ</span><b>${fmt(e.quality)}</b></div><div class="scanner-score"><span>OPPORTUNITÀ</span><b>${fmt(e.opp)}</b></div><div class="scanner-score"><span>CONFIDENCE</span><b>${fmt(e.confidence)}%</b></div></div><div class="why-list">${(e.why||[]).slice(0,2).map(w=>`<span>${esc(w)}</span>`).join('')}</div></article>`}
async function runScanner(){
 const box=document.querySelector('#scanner-results'), st=document.querySelector('#scanner-status'), btn=document.querySelector('#run-scanner');
 if(!window.EWI||!live){box.innerHTML='<div class="scanner-empty">Collega il backend con Twelve Data per usare lo scanner reale.</div>';return;}
 btn.disabled=true;btn.textContent='Scansione…';st.innerHTML='<span class="pill soft">ANALISI</span><p>Filtro rapido e analisi profonda dei candidati migliori.</p>';
 try{
  const d=await window.EWI.scanner({category:document.querySelector('#scanner-category').value,min_quality:document.querySelector('#scanner-quality').value,min_opportunity:document.querySelector('#scanner-opportunity').value,max_results:12});
  const items=(d.items||[]).map(mapLiveEtf);
  st.innerHTML=`<span class="pill soft">COMPLETATO</span><p>${fmt(d.scanned)} ETF filtrati · ${fmt(d.deep_analysed)} analizzati in profondità · ${items.length} risultati.</p>`;
  box.innerHTML=items.length?items.map(scannerCard).join(''):'<div class="scanner-empty">Nessun ETF supera i filtri scelti. Prova ad abbassare la soglia di opportunità.</div>';
 }catch(err){st.innerHTML=`<span class="pill soft">ERRORE</span><p>${esc(err.message)}</p>`;box.innerHTML='<div class="scanner-empty">Scanner non disponibile.</div>';}finally{btn.disabled=false;btn.innerHTML='Avvia scansione <span>→</span>';}
}

function switchPage(page){document.querySelectorAll('.nav,.page').forEach(x=>x.classList.remove('active'));document.querySelectorAll(`.nav[data-page="${page}"]`).forEach(x=>x.classList.add('active'));document.querySelector('#'+page).classList.add('active');document.querySelector('#page-title').textContent=pages[page][0];document.querySelector('#page-subtitle').textContent=pages[page][1];window.scrollTo({top:0,behavior:'smooth'})}
function openReport(symbol){report(symbol);switchPage('reports')}
function renderAll(){topEtfs();impactNews();newsList();etfCards();etfTable();signals();reportLocal(selectedSymbol)}
function mapLiveEtf(x){
 if(x.error)return {symbol:x.symbol,name:x.name||x.symbol,cat:x.category||'ETF',quality:x.quality||75,opp:0,confidence:0,trend:'Errore',dd:'ND',news:50,view:'Errore dati',rating:'wait',buy:false,why:[x.error]};
 return {symbol:x.symbol,name:x.name,cat:x.category,quality:x.quality_score,opp:x.opportunity_score,confidence:x.confidence_score,trend:x.metrics?.trend||'ND',dd:x.metrics?.drawdown_pct==null?'ND':`${x.metrics.drawdown_pct}%`,news:x.news_impact?.score_0_100??50,view:x.signal,rating:x.rating,buy:!!x.buy_zone,why:x.why||[],price:x.quote?.price,currency:x.quote?.currency};
}
function mapLiveNews(n){const s=Number(n.sentiment_score||0);return {title:n.title,source:n.source,summary:n.summary,themes:n.themes_detected||[],impact:(n.impact_score||0)>=75?'high':'mid',sent:s>.15?'positive':s<-.15?'negative':'neutral',score:n.impact_score||50,why:n.summary||'',url:n.url};}
async function loadLive(){
 if(!window.EWI)return;
 try{
  const h=await window.EWI.health(); setLiveState(true,`Backend ${h.version||''} online`);
  const d=await window.EWI.dashboard();
  etfs=(d.etfs||[]).map(mapLiveEtf); news=(d.news||[]).map(mapLiveNews); renderAll();
  const at=document.querySelector('#updated-at'); if(at)at.textContent=new Date(d.updated_at).toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'});
  const risk=d.market?.risk_score; if(risk!=null){document.querySelector('.risk-number').innerHTML=`${risk}<span>/100</span>`;document.querySelector('.risk-track i').style.width=`${risk}%`;document.querySelector('.risk-top .status-pill').textContent=d.market.label;}
  const hero=document.querySelector('.hero-copy p');if(hero&&d.market?.summary)hero.textContent=d.market.summary;
  document.querySelectorAll('.pulse-card strong')[0].textContent=etfs.filter(x=>x.opp>=65).length;
  document.querySelectorAll('.pulse-card strong')[1].textContent=etfs.filter(x=>x.buy).length;
  document.querySelectorAll('.pulse-card strong')[2].textContent=news.filter(x=>x.impact==='high').length;
 }catch(err){setLiveState(false,err.message);renderAll();}
}
function init(){renderAll();document.body.classList.add('simple-mode');const inp=document.querySelector('#api-base');if(inp&&window.EWI)inp.value=window.EWI.apiBase}
document.querySelectorAll('.nav').forEach(b=>b.onclick=()=>switchPage(b.dataset.page));
document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>switchPage(b.dataset.go));
document.querySelectorAll('#mode-switch button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#mode-switch button').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.body.classList.toggle('expert-mode',b.dataset.mode==='expert');document.body.classList.toggle('simple-mode',b.dataset.mode==='simple')});
document.querySelector('#run-scanner').onclick=runScanner;
document.querySelector('#news-filter').onchange=e=>{document.querySelectorAll('#news-list .news-row').forEach(r=>{const v=e.target.value;r.style.display=(v==='all'||r.dataset.impact===v||r.dataset.sent===v)?'block':'none'})};
document.querySelector('#refresh').onclick=async()=>{document.querySelector('#refresh').textContent='…';await loadLive();document.querySelector('#refresh').textContent='✓';setTimeout(()=>document.querySelector('#refresh').textContent='↻',900)};
document.querySelector('#export-report').onclick=()=>{const blob=new Blob([document.querySelector('#report-preview').innerText],{type:'text/plain'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`ETF_World_Intelligence_${selectedSymbol}_Report.txt`;a.click();URL.revokeObjectURL(a.href)};
window.saveApiBase=()=>{const inp=document.querySelector('#api-base');if(inp&&window.EWI){window.EWI.setApiBase(inp.value);loadLive();}};
window.saveAccessKey=()=>{const inp=document.querySelector('#access-password');if(inp&&window.EWI){window.EWI.setAccessKey(inp.value);inp.value='';loadLive();}};
init();window.addEventListener('load',loadLive);
