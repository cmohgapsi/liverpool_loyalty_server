const BASE_URL = "http://localhost:9876";

// ── Definición de campos configurables ────────────────────────────────────────
const FIELD_DEFS = [
  {
    key:     "TARGET_BASE_PATH",
    label:   "Base path del BFF",
    type:    "select",
    options: ["pocket-bff", "web-bff"],
  },
  {
    key:     "COUPONS_LIST_SUFFIX",
    label:   "Cupones de lealtad",
    type:    "select",
    options: ["empty", "full"],
  },
  {
    key:     "COUPONS_REDEEMED_SUFFIX",
    label:   "Cupones canjeados",
    type:    "select",
    options: ["empty", "full"],
  },
  {
    key:     "CHECKOUT_COUPONS_SUFFIX",
    label:   "Cupones de checkout",
    type:    "select",
    options: ["cart", "no_cart_error"],
  },
  {
    key:   "LOYALTY_MEMBER_ID",
    label: "Loyalty Member ID",
    type:  "text",
  },
  {
    key:   "USER_ID",
    label: "User ID",
    type:  "number",
  },
];

// ── Labels ────────────────────────────────────────────────────────────────────
const STATUS_LABEL = {
  enrolled:    "Enrolado",
  notEnrolled: "No enrolado",
  unenrolled:  "Desenrolado",
  declined:    "Rechazado",
};
const ACTION_LABEL = {
  none:                "Ninguna",
  displayWelcomeModal: "Mostrar bienvenida",
  displayEnrollModal:  "Mostrar enrolamiento",
};
const GENDER_LABEL = { male: "Masculino", female: "Femenino", M: "Masculino", F: "Femenino" };

// ── Normalización de valores del log (almacenados en MAYÚSCULAS) ─────────────
const STATUS_KEY = {
  ENROLLED:    "enrolled",
  NOTENROLLED: "notEnrolled",
  UNENROLLED:  "unenrolled",
  DECLINED:    "declined",
};
const ACTION_KEY = {
  NONE:                "none",
  DISPLAYWELCOMEMODAL: "displayWelcomeModal",
  DISPLAYENROLLMODAL:  "displayEnrollModal",
};
const toStatusKey = v => STATUS_KEY[v] ?? (v ? v.toLowerCase() : null);
const toActionKey = v => ACTION_KEY[v] ?? (v ? v.toLowerCase() : null);

// ── Estado local ──────────────────────────────────────────────────────────────
let config      = null;
let panelOpen   = false;
let logPanelOpen = false;
let logEntries  = [];   // entradas filtradas (sin /log ni /configuration)

// ── Render helpers ────────────────────────────────────────────────────────────
function field(label, value, cls = "") {
  const display = value != null && value !== "" ? value : "—";
  return `
    <div class="field ${cls}">
      <div class="field-label">${label}</div>
      <div class="field-value ${display === "—" ? "empty" : ""}">${display}</div>
    </div>`;
}

function statusBadge(status) {
  const label = STATUS_LABEL[status] ?? status ?? "Desconocido";
  const raw   = status ? ` <span style="opacity:.75;font-weight:500">(${status})</span>` : "";
  return `<span class="status-badge ${status ?? ""}">${label}${raw}</span>`;
}

function actionBadge(action) {
  const label = ACTION_LABEL[action] ?? action ?? "—";
  const raw   = action && ACTION_LABEL[action] ? ` <span style="opacity:.75;font-weight:500">(${action})</span>` : "";
  return `<span class="action-badge">${label}${raw}</span>`;
}

// ── Header ────────────────────────────────────────────────────────────────────
function renderHeader(data) {
  const l = data?.loyaltyData ?? {};
  document.getElementById("header-summary").innerHTML = `
    ${statusBadge(l.status)}
    ${actionBadge(l.action)}
    <span class="header-field">Miembro desde: <span>${l.memberSince ?? "—"}</span></span>
    <span class="header-field">Usuario: <span>${[data?.firstName, data?.lastName].filter(Boolean).join(" ") || "—"}</span></span>
  `;
}

function renderHeaderError(msg) {
  document.getElementById("header-summary").innerHTML =
    `<span id="header-error">⚠️ ${msg}</span>`;
}

// ── Cards de estado / usuario ─────────────────────────────────────────────────
function renderLoyaltyCard(data) {
  const l = data?.loyaltyData ?? {};
  document.getElementById("loyalty-fields").innerHTML =
    field("Estado",        statusBadge(l.status) + "<div style='margin-top:4px;'>" + actionBadge(l.action) + "</div>", "col-2") +
    field("Acción",        ACTION_LABEL[l.action] ?? l.action) +
    field("Miembro desde", l.memberSince);
}

function renderUserCard(data) {
  document.getElementById("user-fields").innerHTML =
    field("Nombre",           data?.firstName) +
    field("Apellido paterno", data?.lastName) +
    field("Apellido materno", data?.maternalName) +
    field("Género",           GENDER_LABEL[data?.gender] ? `${GENDER_LABEL[data.gender]} (${data.gender})` : data?.gender) +
    field("Email",            data?.email) +
    field("Fecha nacimiento", data?.dateOfBirth) +
    field("ID Repositorio",   data?.repositoryId) +
    field("Núm. Monedero",    data?.monederoAccNumber);
}

// ── Dirty state ───────────────────────────────────────────────────────────────
function checkDirty() {
  if (!config) return;
  let dirtyCount = 0;
  for (const def of FIELD_DEFS) {
    const el = document.getElementById(`cfg-${def.key}`);
    if (!el) continue;
    const formVal = def.type === "number" ? Number(el.value) : el.value;
    const isDirty = String(formVal) !== String(config[def.key] ?? "");
    el.classList.toggle("dirty", isDirty);
    if (isDirty) dirtyCount++;
  }
  const notice = document.getElementById("pending-notice");
  if (dirtyCount > 0) {
    const s = dirtyCount > 1 ? "s" : "";
    notice.textContent = `● ${dirtyCount} cambio${s} pendiente${s} de aplicar`;
    notice.classList.add("visible");
  } else {
    notice.textContent = "";
    notice.classList.remove("visible");
  }
}

function attachFormListeners() {
  for (const def of FIELD_DEFS) {
    const el = document.getElementById(`cfg-${def.key}`);
    if (!el) continue;
    el.addEventListener("change", checkDirty);
    if (def.type !== "select") el.addEventListener("input", checkDirty);
  }
}

// ── Config panel ──────────────────────────────────────────────────────────────
function renderConfigPanel(cfg) {
  document.getElementById("panel-server").innerHTML = [
    ["Versión", cfg.version],
    ["Puerto",  cfg.PORT],
  ].map(([k, v]) => `
    <div class="info-row">
      <span class="info-key">${k}</span>
      <span class="info-val">${v ?? "—"}</span>
    </div>`).join("");

  const form = document.getElementById("panel-form");
  form.innerHTML = FIELD_DEFS.map(def => {
    const current = cfg[def.key] ?? "";
    if (def.type === "select") {
      const opts = def.options.map(o =>
        `<option value="${o}" ${o == current ? "selected" : ""}>${o}</option>`
      ).join("");
      return `
        <div class="form-field">
          <label class="form-label" for="cfg-${def.key}">${def.label}</label>
          <select class="form-control" id="cfg-${def.key}">${opts}</select>
        </div>`;
    }
    return `
      <div class="form-field">
        <label class="form-label" for="cfg-${def.key}">${def.label}</label>
        <input class="form-control" id="cfg-${def.key}" type="${def.type}" value="${current}" />
      </div>`;
  }).join("");

  attachFormListeners();
  checkDirty();

  const paths = cfg.paths ?? {};
  document.getElementById("panel-paths").innerHTML = Object.entries(paths)
    .map(([k, v]) => `
      <div class="path-row">
        <span class="path-key">${k}</span>
        <span class="path-val">${v}</span>
      </div>`).join("");
}

function togglePanel() {
  panelOpen = !panelOpen;
  document.getElementById("config-panel").classList.toggle("open", panelOpen);
  document.getElementById("panel-backdrop").classList.toggle("visible", panelOpen);
  document.getElementById("btn-config").classList.toggle("active", panelOpen);
}

// ── Aplicar configuración ─────────────────────────────────────────────────────
async function applyConfig() {
  const btn      = document.getElementById("btn-apply");
  const feedback = document.getElementById("apply-feedback");
  btn.disabled   = true;
  feedback.textContent = "";
  feedback.className   = "";

  const body = {};
  for (const def of FIELD_DEFS) {
    const el = document.getElementById(`cfg-${def.key}`);
    if (!el) continue;
    body[def.key] = def.type === "number" ? Number(el.value) : el.value;
  }

  try {
    const res  = await fetch(`${BASE_URL}/configuration`, {
      method:  "PUT",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    config = data.configuration;
    renderConfigPanel(config);
    await fetchStatus();
    feedback.textContent = "✓ Configuración aplicada";
    feedback.className   = "ok";
  } catch (err) {
    feedback.textContent = `⚠️ ${err.message}`;
    feedback.className   = "err";
  } finally {
    btn.disabled = false;
    setTimeout(() => { feedback.textContent = ""; feedback.className = ""; }, 3000);
  }
}

// ── Fetch status ──────────────────────────────────────────────────────────────
async function fetchStatus() {
  const btn = document.getElementById("btn-refresh");
  btn.classList.add("loading");
  btn.disabled = true;

  try {
    const statusPath = config?.paths?.status;
    if (!statusPath) throw new Error("Configuración no cargada");
    const res  = await fetch(`${BASE_URL}${statusPath}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderHeader(data);
    renderLoyaltyCard(data);
    renderUserCard(data);
  } catch (err) {
    renderHeaderError(`No se pudo conectar con el servidor (${err.message})`);
  } finally {
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

function refreshStatus() { fetchStatus(); }

// ── Log panel ─────────────────────────────────────────────────────────────────
const LOG_SKIP = new Set(["/log", "/configuration"]);

function shouldShowEntry(entry) {
  const path = (entry.path || "").split("?")[0];
  return !LOG_SKIP.has(path) && !path.startsWith("/events");
}

function formatLogTime(iso) {
  const d = new Date(iso);
  return (
    String(d.getHours()).padStart(2, "0") + ":" +
    String(d.getMinutes()).padStart(2, "0") + ":" +
    String(d.getSeconds()).padStart(2, "0")
  );
}

function renderLogPanel() {
  const container = document.getElementById("log-entries");
  if (logEntries.length === 0) {
    container.innerHTML = `<div class="log-empty">Sin operaciones registradas</div>`;
    return;
  }

  const html = logEntries.map((entry, i) => {
    const hasOp     = entry.new_status != null;
    const code      = entry.http_code;
    const codeClass = code >= 200 && code < 300 ? "ok" : code >= 400 ? "err" : "warn";
    const time      = formatLogTime(entry.request_datetime);

    let transitionHtml = "";
    if (hasOp) {
      const op = entry.action || entry.operation || "";
      const prevStatusBadge = statusBadge(toStatusKey(entry.prev_status));
      const prevActionBadge = actionBadge(toActionKey(entry.prev_action));
      const nextStatusBadge = statusBadge(toStatusKey(entry.new_status));
      const nextActionBadge = actionBadge(toActionKey(entry.new_action));
      transitionHtml = `
        <div class="log-transition">
          <div class="log-state next">${nextStatusBadge}${nextActionBadge}</div>
          <div class="log-arrow-down">↑ <span class="log-op-name">${op}</span></div>
          <div class="log-state prev">${prevStatusBadge}${prevActionBadge}</div>
        </div>`;
    }

    const sep = i < logEntries.length - 1
      ? `<div class="log-separator">↑</div>`
      : "";

    return `
      <div class="log-entry">
        <div class="log-entry-header">
          <span class="log-time">${time}</span>
          <span class="log-method">${entry.method}</span>
          <span class="log-code ${codeClass}">${code}</span>
          <button class="log-info-btn" data-idx="${i}" title="Ver detalle">i</button>
        </div>
        <div class="log-path">${entry.path}</div>
        ${transitionHtml}
      </div>
      ${sep}`;
  }).join("");

  container.innerHTML = html;

  // Attach info button listeners (avoids escaping issues with onclick attribute)
  container.querySelectorAll(".log-info-btn").forEach(btn => {
    btn.addEventListener("click", () => showLogDetail(Number(btn.dataset.idx)));
  });
}

function toggleLogPanel() {
  logPanelOpen = !logPanelOpen;
  document.getElementById("log-panel").classList.toggle("open", logPanelOpen);
  document.getElementById("log-backdrop").classList.toggle("visible", logPanelOpen);
  document.getElementById("btn-log").classList.toggle("active", logPanelOpen);
}

async function clearLog() {
  try {
    await fetch(`${BASE_URL}/log`, { method: "DELETE" });
    logEntries = [];
    renderLogPanel();
  } catch (e) {
    console.error("Error clearing log:", e);
  }
}

async function fetchLog() {
  try {
    const res  = await fetch(`${BASE_URL}/log`);
    const data = await res.json();
    logEntries = data.filter(shouldShowEntry);
    renderLogPanel();
  } catch (e) {
    console.error("Error fetching log:", e);
  }
}

// ── Modal detalle ─────────────────────────────────────────────────────────────
function showLogDetail(index) {
  const entry = logEntries[index];
  if (!entry) return;

  const CODE_FIELDS = new Set(["curl", "response"]);

  const rows = Object.entries(entry)
    .filter(([k]) => !CODE_FIELDS.has(k))
    .map(([k, v]) => `
      <div class="detail-row">
        <span class="detail-key">${k}</span>
        <span class="detail-val">${v != null ? String(v) : "—"}</span>
      </div>`).join("");

  const makeCodeSection = (label, text, id) => `
    <div class="detail-curl-section">
      <div class="detail-curl-label">${label}</div>
      <div class="detail-curl-wrap">
        <pre class="detail-curl">${text.replace(/</g, "&lt;")}</pre>
        <button class="copy-btn" id="${id}">Copiar</button>
      </div>
    </div>`;

  const responseText = entry.response != null
    ? JSON.stringify(entry.response, null, 2)
    : null;

  const curlSection     = entry.curl     ? makeCodeSection("curl",     entry.curl,  "copy-curl-btn")     : "";
  const responseSection = responseText   ? makeCodeSection("response", responseText, "copy-response-btn") : "";

  document.getElementById("log-detail-body").innerHTML = rows + curlSection + responseSection;

  const attachCopy = (btnId, text) => {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(text).then(() => {
        this.textContent = "✓ Copiado";
        setTimeout(() => { this.textContent = "Copiar"; }, 2000);
      }).catch(() => {
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        this.textContent = "✓ Copiado";
        setTimeout(() => { this.textContent = "Copiar"; }, 2000);
      });
    });
  };

  attachCopy("copy-curl-btn",     entry.curl || "");
  attachCopy("copy-response-btn", responseText || "");

  document.getElementById("log-detail-modal").classList.add("visible");
}

function closeLogDetail() {
  document.getElementById("log-detail-modal").classList.remove("visible");
}

document.getElementById("log-detail-modal").addEventListener("click", function (e) {
  if (e.target === this) closeLogDetail();
});

// ── SSE ───────────────────────────────────────────────────────────────────────
function connectSSE() {
  const indicator = document.getElementById("sse-indicator");
  const es = new EventSource(`${BASE_URL}/events`);

  es.onopen = () => {
    indicator.className = "sse-dot connected";
    indicator.title = "Push activo";
  };
  es.onerror = () => {
    indicator.className = "sse-dot disconnected";
    indicator.title = "Push desconectado — reconectando…";
  };

  es.addEventListener("log-entry", (e) => {
    const entry = JSON.parse(e.data);
    if (shouldShowEntry(entry)) {
      logEntries.unshift(entry);
      renderLogPanel();
    }
    // Auto-refrescar status cuando hay un cambio de estado
    if (entry.new_status != null || (entry.method === "POST" && entry.http_code === 200)) {
      fetchStatus();
    }
  });

  es.addEventListener("log-cleared", () => {
    logEntries = [];
    renderLogPanel();
  });
}

// ── Operations ────────────────────────────────────────────────────────────────

function opFeedback(id, msg, isOk) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `ops-feedback ${isOk ? "ok" : "err"}`;
  setTimeout(() => { el.textContent = ""; el.className = "ops-feedback"; }, 4000);
}

function opBusy(btnId, busy) {
  const btn = document.getElementById(btnId);
  if (btn) btn.disabled = busy;
}

function _findArray(obj) {
  if (Array.isArray(obj)) return obj;
  if (!obj || typeof obj !== "object") return null;
  for (const v of Object.values(obj)) {
    const found = _findArray(v);
    if (found) return found;
  }
  return null;
}

async function fetchCancelReasons() {
  const select = document.getElementById("op-cancel-reason");
  const path   = config?.paths?.cancelReasons;
  if (!path) { select.innerHTML = `<option value="">Config no cargada</option>`; return; }
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { "server-log": "false" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const arr  = _findArray(data);
    if (!arr || arr.length === 0) {
      select.innerHTML = `<option value="">Sin razones disponibles</option>`;
      return;
    }
    select.innerHTML = arr.map(r => {
      const val   = typeof r === "string" ? r : (r.cancelReasonId ?? r.id ?? r.code ?? JSON.stringify(r));
      const label = typeof r === "string" ? r : (r.description ?? r.name ?? r.label ?? String(val));
      return `<option value="${val}">${label}</option>`;
    }).join("");
  } catch (e) {
    select.innerHTML = `<option value="">Error al cargar razones</option>`;
    console.error("fetchCancelReasons:", e);
  }
}

async function opSetStatus() {
  const action = document.getElementById("op-status-action").value;
  const path   = config?.paths?.status;
  if (!path) { opFeedback("fb-set-status", "Config no cargada", false); return; }
  opBusy("btn-op-set-status", true);
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ action, value: true }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.status?.successMessage ?? `HTTP ${res.status}`);
    opFeedback("fb-set-status", "✓ Estado actualizado", true);
  } catch (e) {
    opFeedback("fb-set-status", `⚠️ ${e.message}`, false);
  } finally {
    opBusy("btn-op-set-status", false);
  }
}

async function opCancelEnroll() {
  const cancelReason = document.getElementById("op-cancel-reason").value;
  if (!cancelReason) { opFeedback("fb-cancel-enroll", "Selecciona una razón", false); return; }
  const path = config?.paths?.status;
  if (!path) { opFeedback("fb-cancel-enroll", "Config no cargada", false); return; }
  opBusy("btn-op-cancel", true);
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ action: "unenroll", value: true, cancelReason }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.status?.successMessage ?? `HTTP ${res.status}`);
    opFeedback("fb-cancel-enroll", "✓ Enrolamiento cancelado", true);
  } catch (e) {
    opFeedback("fb-cancel-enroll", `⚠️ ${e.message}`, false);
  } finally {
    opBusy("btn-op-cancel", false);
  }
}

async function opEnroll() {
  const firstName      = document.getElementById("op-first-name").value.trim();
  const lastName       = document.getElementById("op-last-name").value.trim();
  const motherLastName = document.getElementById("op-mother-name").value.trim();
  const gender         = document.getElementById("op-gender").value;
  const dateOfBirth    = document.getElementById("op-dob").value.trim();

  if (!firstName || !lastName || !motherLastName || !gender || !dateOfBirth) {
    opFeedback("fb-enroll", "Todos los campos son obligatorios", false);
    return;
  }

  const path = config?.paths?.enroll;
  if (!path) { opFeedback("fb-enroll", "Config no cargada", false); return; }
  opBusy("btn-op-enroll", true);
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ firstName, lastName, motherLastName, gender, dateOfBirth }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.status?.successMessage ?? `HTTP ${res.status}`);
    opFeedback("fb-enroll", "✓ Enrolamiento exitoso", true);
  } catch (e) {
    opFeedback("fb-enroll", `⚠️ ${e.message}`, false);
  } finally {
    opBusy("btn-op-enroll", false);
  }
}

async function opReEnroll() {
  const path = config?.paths?.enroll;
  if (!path) { opFeedback("fb-reenroll", "Config no cargada", false); return; }
  opBusy("btn-op-reenroll", true);
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({}),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.status?.successMessage ?? `HTTP ${res.status}`);
    opFeedback("fb-reenroll", "✓ Re-enrolamiento exitoso", true);
  } catch (e) {
    opFeedback("fb-reenroll", `⚠️ ${e.message}`, false);
  } finally {
    opBusy("btn-op-reenroll", false);
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  try {
    const res = await fetch(`${BASE_URL}/configuration`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    config = await res.json();
    renderConfigPanel(config);
  } catch (err) {
    renderHeaderError(`No se pudo cargar la configuración (${err.message})`);
    return;
  }
  await Promise.all([fetchStatus(), fetchLog()]);
  fetchCancelReasons();
  connectSSE();
}

init();
