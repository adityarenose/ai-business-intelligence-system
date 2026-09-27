const API = {
  summary: "/api/summary",
  trend: "/api/sales/trend",
  categories: "/api/sales/categories",
  products: "/api/sales/products",
  cities: "/api/sales/cities",
  segments: "/api/customers/segments",
  churn: "/api/customers/churn",
  predict: "/api/predict-churn",
  ask: "/api/ask",
};

const state = { summary: null, trend: [], categories: [], products: [], cities: [], segments: {}, churn: null };
const currency = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });
const $ = (selector) => document.querySelector(selector);

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { Accept: "application/json", ...(options.headers || {}) }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error?.message || `Request failed (${response.status})`);
  return payload.data;
}

function setGlobalError(message = "") {
  const element = $("#global-error");
  element.textContent = message;
  element.hidden = !message;
}

function setLoading(loading) {
  $("#loading-banner").hidden = !loading;
  $("#refresh-button").disabled = loading;
}

function safe(value, fallback = "--") { return value === null || value === undefined ? fallback : value; }
function formatDate() { return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date()); }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[character])); }

function renderMetrics() {
  const summary = state.summary;
  const churnRate = summary?.churn_statistics?.churn_rate_percent;
  const metrics = [
    ["Total revenue", currency.format(summary?.total_revenue || 0), "Across all recorded orders"],
    ["Total orders", number.format(summary?.total_orders || 0), "Completed order records"],
    ["Total customers", number.format(summary?.total_customers || 0), "Customer records"],
    ["Average order value", currency.format(summary?.average_order_value || 0), "Revenue per order"],
    ["Churn rate", `${decimal.format(churnRate || 0)}%`, "Observed customer churn"],
  ];
  $("#metric-grid").innerHTML = metrics.map(([label, value, foot]) => `<article class="metric-card"><span class="metric-label">${label}</span><div class="metric-value">${value}</div><span class="metric-foot">${foot}</span></article>`).join("");
}

function renderTrend(target, values) {
  const element = $(target);
  if (!values?.length) { element.innerHTML = '<div class="empty-state">No revenue data available.</div>'; return; }
  const width = 720, height = 250, left = 44, right = 15, top = 18, bottom = 34;
  const max = Math.max(...values.map((item) => Number(item.total_revenue) || 0), 1);
  const x = (index) => left + index * ((width - left - right) / Math.max(values.length - 1, 1));
  const y = (value) => top + (height - top - bottom) * (1 - value / max);
  const points = values.map((item, index) => `${x(index)},${y(Number(item.total_revenue) || 0)}`).join(" ");
  const area = `${left},${height - bottom} ${points} ${x(values.length - 1)},${height - bottom}`;
  const grid = [0, .5, 1].map((ratio) => `<line class="chart-grid-line" x1="${left}" y1="${y(max * ratio)}" x2="${width - right}" y2="${y(max * ratio)}"/><text class="chart-label" x="0" y="${y(max * ratio) + 4}">${currency.format(max * ratio)}</text>`).join("");
  const labels = values.map((item, index) => index === 0 || index === values.length - 1 || index === Math.floor(values.length / 2) ? `<text class="chart-label" text-anchor="middle" x="${x(index)}" y="${height - 8}">${escapeHtml(item.month)}</text>` : "").join("");
  const dots = values.map((item, index) => `<circle class="chart-point" cx="${x(index)}" cy="${y(Number(item.total_revenue) || 0)}" r="3.5"><title>${escapeHtml(item.month)}: ${currency.format(item.total_revenue)}</title></circle>`).join("");
  element.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Monthly revenue trend"><defs><linearGradient id="area-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d8b83" stop-opacity=".22"/><stop offset="1" stop-color="#0d8b83" stop-opacity="0"/></linearGradient></defs>${grid}<polygon class="chart-area" points="${area}"/><polyline class="chart-line" points="${points}"/>${dots}${labels}</svg>`;
}

function renderCategoryList(target, values, limit = 5) {
  const element = $(target);
  if (!values?.length) { element.innerHTML = '<div class="empty-state">No category data available.</div>'; return; }
  const rows = values.slice(0, limit), max = Number(rows[0].revenue) || 1;
  element.innerHTML = rows.map((item) => `<div class="bar-item"><div class="bar-top"><strong>${escapeHtml(item.category)}</strong><span>${currency.format(item.revenue)}</span></div><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3, Number(item.revenue) / max * 100)}%"></div></div></div>`).join("");
}

function renderTables() {
  const products = state.products?.slice(0, 10) || [];
  $("#products-table").innerHTML = products.length ? products.map((item) => `<tr><td>${escapeHtml(item.product_name)}</td><td>${escapeHtml(item.category)}</td><td>${currency.format(item.revenue)}</td><td>${number.format(item.units_sold)}</td></tr>`).join("") : '<tr><td colspan="4" class="empty-cell">No product data.</td></tr>';
  const cities = state.cities || [];
  $("#cities-table").innerHTML = cities.length ? cities.map((item) => `<tr><td>${escapeHtml(item.city)}</td><td>${currency.format(item.revenue)}</td><td>${number.format(item.orders)}</td><td>${number.format(item.customers)}</td></tr>`).join("") : '<tr><td colspan="4" class="empty-cell">No city data.</td></tr>';
}

function renderCustomers() {
  const segments = Object.entries(state.segments || {});
  const colors = ["#0d8b83", "#c9822b", "#17324a", "#c5574d"];
  const total = segments.reduce((sum, [, value]) => sum + Number(value), 0);
  let cursor = 0;
  const stops = segments.map(([, value], index) => { const start = cursor; cursor += total ? Number(value) / total * 360 : 0; return `${colors[index % colors.length]} ${start}deg ${cursor}deg`; }).join(", ");
  $("#segment-total").textContent = total ? number.format(total) : "--";
  $("#segment-donut").style.background = stops ? `conic-gradient(${stops})` : "#d9e6e7";
  $("#segment-legend").innerHTML = segments.length ? segments.map(([name, value], index) => `<div class="legend-item"><span class="legend-swatch" style="background:${colors[index % colors.length]}"></span><span>${escapeHtml(name)}</span><strong>${number.format(value)}</strong></div>`).join("") : '<div class="empty-state">No segment data.</div>';

  const spenders = state.summary?.customer_spending || [];
  const maxSpend = Number(spenders[0]?.total_spent) || 1;
  $("#spending-list").innerHTML = spenders.length ? spenders.slice(0, 6).map((item) => `<div class="bar-item"><div class="bar-top"><strong>Customer #${escapeHtml(item.customer_id)}</strong><span>${currency.format(item.total_spent)}</span></div><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3, Number(item.total_spent) / maxSpend * 100)}%"></div></div></div>`).join("") : '<div class="empty-state">No spending data.</div>';

  const churn = state.churn;
  if (!churn) { $("#churn-distribution").innerHTML = '<div class="empty-state">No churn data.</div>'; return; }
  const rate = Number(churn.churn_rate_percent) || 0;
  $("#churn-distribution").innerHTML = `<div class="churn-rate"><strong>${decimal.format(rate)}%</strong><span>of customers churned</span></div><div class="churn-progress"><span style="width:${Math.min(100, rate)}%"></span></div><div class="churn-meta"><span>${number.format(churn.churned_customers)} churned</span><span>${number.format(churn.total_customers - churn.churned_customers)} retained</span></div>`;
}

function renderAll() {
  renderMetrics();
  renderTrend("#overview-trend", state.trend);
  renderTrend("#sales-trend", state.trend);
  renderCategoryList("#overview-categories", state.categories, 5);
  renderCategoryList("#category-list", state.categories, 8);
  renderTables();
  renderCustomers();
}

async function loadDashboard() {
  setGlobalError(""); setLoading(true);
  try {
    const [summary, trend, categories, products, cities, segments, churn] = await Promise.all([
      request(API.summary), request(API.trend), request(API.categories), request(API.products),
      request(API.cities), request(API.segments), request(API.churn),
    ]);
    Object.assign(state, { summary, trend, categories, products, cities, segments, churn });
    renderAll();
    $("#last-updated").textContent = `Updated ${formatDate()}`;
  } catch (error) {
    setGlobalError(`Unable to load live dashboard data. ${error.message}`);
  } finally { setLoading(false); }
}

function formPayload(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  ["age", "tenure_months", "monthly_spend", "support_calls", "purchase_frequency", "total_orders", "total_spent", "avg_order_value"].forEach((key) => { data[key] = Number(data[key]); });
  return data;
}

function renderPrediction(result) {
  const riskClass = String(result.risk_level || "").toLowerCase();
  $("#prediction-result").innerHTML = `<div class="result-output"><div class="result-risk ${riskClass}"><p>Risk level</p><strong>${escapeHtml(result.risk_level)}</strong></div><div class="result-stats"><div class="result-stat"><span>Churn probability</span><strong>${decimal.format(Number(result.churn_probability) * 100)}%</strong></div><div class="result-stat"><span>Predicted churn class</span><strong>${Number(result.predicted_class) === 1 ? "Likely to churn" : "Not likely to churn"}</strong></div></div></div>`;
}

async function submitPrediction(event) {
  event.preventDefault();
  const form = event.currentTarget, button = $("#predict-button"), error = $("#prediction-error");
  error.hidden = true; button.disabled = true; button.innerHTML = '<span class="spinner" aria-hidden="true"></span> Assessing...';
  if (!form.checkValidity()) { form.reportValidity(); button.disabled = false; button.innerHTML = 'Predict churn risk <span aria-hidden="true">→</span>'; return; }
  try { renderPrediction(await request(API.predict, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formPayload(form)) })); }
  catch (requestError) { error.textContent = requestError.message; error.hidden = false; }
  finally { button.disabled = false; button.innerHTML = 'Predict churn risk <span aria-hidden="true">→</span>'; }
}

async function submitAssistant(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = $("#assistant-button");
  const error = $("#assistant-error");
  const question = new FormData(form).get("question");
  error.hidden = true;
  button.disabled = true;
  button.innerHTML = '<span class="spinner" aria-hidden="true"></span> Thinking...';
  try {
    const result = await request(API.ask, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
    const insights = result.insights?.length ? `<div class="assistant-list"><strong>Insights</strong><ul>${result.insights.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>` : "";
    const recommendations = result.recommendations?.length ? `<div class="assistant-list"><strong>Recommendations</strong><ul>${result.recommendations.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>` : "";
    $("#assistant-result").innerHTML = `<p class="assistant-result-label">Verified response</p><p class="assistant-result-text">${escapeHtml(result.answer)}</p>${insights}${recommendations}<p class="assistant-data-note">${result.data?.length || 0} verified record(s) retrieved</p>`;
  } catch (requestError) {
    error.textContent = requestError.message;
    error.hidden = false;
  } finally {
    button.disabled = false;
    button.innerHTML = 'Ask assistant <span aria-hidden="true">→</span>';
  }
}

function setupNavigation() {
  document.querySelectorAll(".nav-item").forEach((link) => link.addEventListener("click", () => { document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("is-active")); link.classList.add("is-active"); $("#sidebar").classList.remove("is-open"); $("#menu-toggle").setAttribute("aria-expanded", "false"); }));
  $("#menu-toggle").addEventListener("click", () => { const open = $("#sidebar").classList.toggle("is-open"); $("#menu-toggle").setAttribute("aria-expanded", String(open)); });
}

setupNavigation();
$("#refresh-button").addEventListener("click", loadDashboard);
$("#prediction-form").addEventListener("submit", submitPrediction);
$("#assistant-form").addEventListener("submit", submitAssistant);
loadDashboard();
