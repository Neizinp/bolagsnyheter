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
let reports = [];
let companies = [];
let selected = '';
let limit = 50;

const normalize = value => value.toLocaleLowerCase('sv-SE');
const dateFormat = new Intl.DateTimeFormat('sv-SE', { day: 'numeric', month: 'short', year: 'numeric' });

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

fetch('./reports.json', { cache: 'no-cache' }).then(response => {
  if (!response.ok) throw new Error('Rapportdata kunde inte hämtas.');
  return response.json();
}).then(data => {
  reports = data.reports;
  const byId = new Map();
  for (const report of reports) {
    if (!byId.has(report.id)) byId.set(report.id, { id: report.id, name: report.name, count: 0 });
    byId.get(report.id).count++;
  }
  companies = [...byId.values()].sort((first, second) => first.name.localeCompare(second.name, 'sv'));
  sourceCount.textContent = String(companies.length);
  document.querySelector('#updated').textContent = `Uppdaterad ${dateFormat.format(new Date(data.updatedAt))}`;
  renderSources();
  renderReports();
}).catch(() => {
  document.querySelector('#updated').textContent = 'Kunde inte hämta rapporter';
  empty.hidden = false;
  empty.textContent = 'Rapportdata kunde inte hämtas. Försök igen senare.';
});