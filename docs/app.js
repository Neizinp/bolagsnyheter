const sources = document.querySelector('#sources');
const sourceSearch = document.querySelector('#source-search');
const reportSearch = document.querySelector('#report-search');
const reportsElement = document.querySelector('#reports');
const empty = document.querySelector('#empty');
const moreWrap = document.querySelector('#more-wrap');
const more = document.querySelector('#more');
const selectionLabel = document.querySelector('#selection-label');
const resultsCount = document.querySelector('#results-count');
const sourceCount = document.querySelector('#source-count');
const refresh = document.querySelector('#refresh');
const status = document.querySelector('#updated');
const cacheKey = 'rapport-cache-v1';
let reports = [];
let companies = [];
let selected = '';
let limit = 50;

const normalize = value => value.toLocaleLowerCase('sv-SE');
const dateFormat = new Intl.DateTimeFormat('sv-SE', { day: 'numeric', month: 'short', year: 'numeric' });

function periodKey(report) {
  const title = normalize(report.title);
  const year = title.match(/20\d{2}/)?.[0];
  const quarter = title.match(/\bq\s*([1-4])\b|\b([1-4])(?:a|:e)?\s+kvartal|\b(första|andra|tredje|fjärde)\s+kvartal/);
  const names = { första: '1', andra: '2', tredje: '3', fjärde: '4' };
  let value = quarter && (quarter[1] || quarter[2] || names[quarter[3]]);
  if (!value) value = Object.entries({ mars: '1', juni: '2', september: '3', december: '4' }).find(([month]) => title.includes(month))?.[1];
  if (!value && title.includes('bokslutskommuniké')) value = '4';
  return value && year ? `${year}-q${value}` : report.url;
}

function mergeReports(...lists) {
  const seen = new Set();
  const counts = new Map();
  return lists.flat().filter(report => report && report.id && report.title && report.url && Number.isFinite(Date.parse(report.published)))
    .sort((first, second) => Date.parse(second.published) - Date.parse(first.published))
    .filter(report => {
      const key = `${report.id}:${periodKey(report)}`;
      const count = counts.get(report.id) || 0;
      if (seen.has(key) || count >= 4) return false;
      seen.add(key);
      counts.set(report.id, count + 1);
      return true;
    });
}

function readCache() {
  try {
    const saved = JSON.parse(localStorage.getItem(cacheKey) || '[]');
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function applyReports(incoming) {
  reports = incoming;
  const byId = new Map();
  for (const report of reports) {
    if (!byId.has(report.id)) byId.set(report.id, { id: report.id, name: report.name, count: 0 });
    byId.get(report.id).count++;
  }
  companies = [...byId.values()].sort((first, second) => first.name.localeCompare(second.name, 'sv'));
  sourceCount.textContent = String(companies.length);
  renderSources();
  renderReports();
}

function parseFeed(text, company) {
  const xml = new DOMParser().parseFromString(text, 'application/xml');
  if (xml.querySelector('parsererror')) throw new Error('Ogiltigt RSS-flöde');
  return [...xml.querySelectorAll('item')].flatMap(item => {
    const get = name => item.querySelector(name)?.textContent?.trim() || '';
    const title = get('title');
    if (!/delårsrapport|kvartalsrapport|bokslutskommuniké|\bq[1-4]\s*20\d{2}\s+resultat|resultat för (?:första|andra|tredje|fjärde) kvartalet/i.test(title) || /kallelse|inbjudan|webcast|presentation|publicer(?:as|ing)|tidigarelägg|senarelägg|datum|påminnelse|kalender/i.test(title)) return [];
    let url;
    try { url = new URL(get('link')); } catch { return []; }
    const parts = url.pathname.split('/').filter(Boolean);
    if (url.hostname !== 'news.cision.com' || parts[0] !== 'se' || parts[2] !== 'r' || (company && parts[1] !== company)) return [];
    const published = new Date(get('pubDate'));
    if (!Number.isFinite(published.getTime()) || published > new Date()) return [];
    const id = parts[1];
    const name = companies.find(item => item.id === id)?.name || id.replace('--publ-', '').replaceAll('-', ' ').trim().replace(/\b\w/g, letter => letter.toUpperCase());
    return [{ id, name, title, url: url.href, published: published.toISOString(), description: get('description').replace(/\s+/g, ' ').slice(0, 350) }];
  });
}

async function refreshReports() {
  const company = selected;
  refresh.disabled = true;
  status.textContent = 'Hämtar rapporter';
  const results = await Promise.allSettled(['delårsrapport', 'kvartalsrapport', 'bokslutskommuniké'].map(async query => {
    const params = new URLSearchParams({ format: 'rss', q: query });
    if (company) params.set('n', company);
    const response = await fetch(`https://r.jina.ai/https://news.cision.com/se/ListItems?${params}`, { headers: { 'X-Return-Format': 'html', 'X-No-Cache': 'true' }, signal: AbortSignal.timeout(30000) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return parseFeed(await response.text(), company);
  }));
  const successful = results.filter(result => result.status === 'fulfilled');
  if (!successful.length) {
    status.textContent = 'Kunde inte hämta rapporter';
  } else {
    applyReports(mergeReports(reports, ...successful.map(result => result.value)));
    try {
      localStorage.setItem(cacheKey, JSON.stringify(reports));
      status.textContent = successful.length === results.length ? 'Hämtat och sparat' : 'Delvis hämtat och sparat';
    } catch {
      status.textContent = 'Hämtat, men kunde inte sparas';
    }
  }
  refresh.disabled = false;
}

function renderSources() {
  const query = normalize(sourceSearch.value.trim());
  sources.replaceChildren();
  const visible = companies.filter(company => normalize(company.name).includes(query));
  const all = document.createElement('button');
  all.className = `source${selected === '' ? ' active' : ''}`;
  all.type = 'button';
  all.textContent = 'Alla bolag';
  all.setAttribute('aria-pressed', String(selected === ''));
  all.onclick = () => selectCompany('');
  sources.append(all);
  for (const company of visible) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `source${selected === company.id ? ' active' : ''}`;
    button.setAttribute('aria-pressed', String(selected === company.id));
    const name = document.createElement('span');
    name.textContent = company.name;
    const count = document.createElement('span');
    count.className = 'source-count';
    count.textContent = company.count;
    button.append(name, count);
    button.onclick = () => selectCompany(company.id);
    sources.append(button);
  }
}

function selectCompany(id) {
  selected = id;
  limit = 50;
  renderSources();
  renderReports();
}

function renderReports() {
  const query = normalize(reportSearch.value.trim());
  const filtered = reports.filter(report => (!selected || report.id === selected) && (!query || normalize(`${report.name} ${report.title} ${report.description}`).includes(query)));
  const company = companies.find(item => item.id === selected);
  selectionLabel.textContent = company ? company.name.toLocaleUpperCase('sv-SE') : 'ALLA BOLAG';
  resultsCount.textContent = `${filtered.length} RAPPORTER`;
  reportsElement.replaceChildren();
  for (const report of filtered.slice(0, limit)) {
    const row = document.createElement('article');
    row.className = 'report';
    const source = document.createElement('div');
    source.className = 'report-company';
    const sourceButton = document.createElement('button');
    sourceButton.textContent = report.name;
    sourceButton.type = 'button';
    sourceButton.onclick = () => selectCompany(report.id);
    source.append(sourceButton);
    const main = document.createElement('div');
    main.className = 'report-main';
    const title = document.createElement('a');
    title.className = 'report-title';
    title.href = report.url;
    title.target = '_blank';
    title.rel = 'noopener noreferrer';
    title.textContent = report.title;
    main.append(title);
    if (report.description) {
      const description = document.createElement('p');
      description.className = 'report-description';
      description.textContent = report.description + (report.description.length >= 350 ? '…' : '');
      main.append(description);
    }
    const date = document.createElement('time');
    date.className = 'report-date';
    date.dateTime = report.published;
    date.textContent = dateFormat.format(new Date(report.published));
    const label = document.createElement('span');
    label.textContent = 'CISION ↗';
    date.append(label);
    row.append(source, main, date);
    reportsElement.append(row);
  }
  empty.hidden = filtered.length !== 0;
  moreWrap.hidden = filtered.length <= limit;
}

sourceSearch.addEventListener('input', renderSources);
reportSearch.addEventListener('input', () => { limit = 50; renderReports(); });
more.addEventListener('click', () => { limit += 50; renderReports(); });
refresh.addEventListener('click', refreshReports);

fetch('./reports.json', { cache: 'no-cache' }).then(response => {
  if (!response.ok) throw new Error('Rapportdata kunde inte hämtas.');
  return response.json();
}).then(data => {
  applyReports(mergeReports(data.reports, readCache()));
  status.textContent = `Hämtat ${dateFormat.format(new Date(data.updatedAt))}`;
}).catch(() => {
  const cached = readCache();
  status.textContent = 'Kunde inte hämta rapportdata';
  if (cached.length) {
    applyReports(mergeReports(cached));
  } else {
    empty.hidden = false;
    empty.textContent = 'Rapportdata kunde inte hämtas. Försök igen senare.';
  }
});