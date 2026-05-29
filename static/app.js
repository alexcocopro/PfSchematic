const state = {
  data: null,
  network: null,
  physics: false,
  labels: true,
  selectedAlias: null,
  visibleRules: [],
  selectedActions: new Set(["pass", "block", "reject", "unknown"]),
};

const els = {
  datasetName: document.getElementById("datasetName"),
  sampleButton: document.getElementById("sampleButton"),
  xmlInput: document.getElementById("xmlInput"),
  fitButton: document.getElementById("fitButton"),
  physicsButton: document.getElementById("physicsButton"),
  labelsButton: document.getElementById("labelsButton"),
  exportButton: document.getElementById("exportButton"),
  exportPngButton: document.getElementById("exportPngButton"),
  exportPdfButton: document.getElementById("exportPdfButton"),
  searchInput: document.getElementById("searchInput"),
  interfaceSelect: document.getElementById("interfaceSelect"),
  protocolSelect: document.getElementById("protocolSelect"),
  metricRules: document.getElementById("metricRules"),
  metricPass: document.getElementById("metricPass"),
  metricBlocked: document.getElementById("metricBlocked"),
  metricInterfaces: document.getElementById("metricInterfaces"),
  metricAliases: document.getElementById("metricAliases"),
  statusText: document.getElementById("statusText"),
  visibleCount: document.getElementById("visibleCount"),
  rulePanelCount: document.getElementById("rulePanelCount"),
  rulesBody: document.getElementById("rulesBody"),
  aliasPanel: document.getElementById("aliasPanel"),
  aliasName: document.getElementById("aliasName"),
  aliasMeta: document.getElementById("aliasMeta"),
  aliasDescription: document.getElementById("aliasDescription"),
  aliasSearchInput: document.getElementById("aliasSearchInput"),
  aliasItemsBody: document.getElementById("aliasItemsBody"),
  aliasCloseButton: document.getElementById("aliasCloseButton"),
  toast: document.getElementById("toast"),
};

const groupOptions = {
  any: { color: { background: "#ede9fe", border: "#8b5cf6" }, shape: "box" },
  alias: { color: { background: "#ccfbf1", border: "#0ea5a4" }, shape: "box" },
  interface: { color: { background: "#dbeafe", border: "#2563eb" }, shape: "box" },
  interface_ip: { color: { background: "#cffafe", border: "#0891b2" }, shape: "dot" },
  private: { color: { background: "#dcfce7", border: "#16a34a" }, shape: "dot" },
  public: { color: { background: "#fee2e2", border: "#dc2626" }, shape: "dot" },
  host: { color: { background: "#f3e8ff", border: "#7c3aed" }, shape: "box" },
};

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => els.toast.classList.remove("show"), 3600);
}

async function loadSample() {
  els.statusText.textContent = "Cargando demo sanitizado...";
  const response = await fetch("/api/sample");
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo cargar la muestra.");
  setData(data);
}

async function uploadXml(file) {
  const form = new FormData();
  form.append("xml", file);
  els.statusText.textContent = `Procesando ${file.name}...`;
  const response = await fetch("/api/upload", { method: "POST", body: form });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo procesar el XML.");
  setData(data);
}

function setData(data) {
  state.data = data;
  els.datasetName.textContent = data.name;
  hideAliasDetails();
  fillMetrics(data);
  fillSelects(data);
  applyFilters();
  showToast(`Diagrama listo: ${data.stats.total_rules} reglas`);
}

function fillMetrics(data) {
  const actions = data.stats.actions || {};
  els.metricRules.textContent = data.stats.total_rules || 0;
  els.metricPass.textContent = actions.pass || 0;
  els.metricBlocked.textContent = (actions.block || 0) + (actions.reject || 0);
  els.metricInterfaces.textContent = data.stats.interface_count || Object.keys(data.stats.interfaces || {}).length;
  els.metricAliases.textContent = data.stats.alias_count || 0;
}

function fillSelects(data) {
  const interfaceEntries = Object.entries(data.stats.interfaces || {}).sort((a, b) => a[0].localeCompare(b[0]));
  const protocolEntries = Object.entries(data.stats.protocols || {}).sort((a, b) => a[0].localeCompare(b[0]));
  els.interfaceSelect.innerHTML = `<option value="">Todas</option>${interfaceEntries
    .map(([name, count]) => `<option value="${escapeHtml(name)}">${escapeHtml(name)} (${count})</option>`)
    .join("")}`;
  els.protocolSelect.innerHTML = `<option value="">Todos</option>${protocolEntries
    .map(([name, count]) => `<option value="${escapeHtml(name)}">${escapeHtml(name.toUpperCase())} (${count})</option>`)
    .join("")}`;
}

function aliasSearchText(aliasName) {
  const alias = state.data?.aliases?.[aliasName];
  if (!alias) return "";
  const entries = alias.entries || [];
  return [
    alias.name,
    alias.type,
    alias.descr,
    ...entries.flatMap((entry) => [entry.value, entry.description, entry.kind]),
  ].join(" ");
}

function applyFilters() {
  if (!state.data) return;
  const query = els.searchInput.value.trim().toLowerCase();
  const selectedInterface = els.interfaceSelect.value;
  const selectedProtocol = els.protocolSelect.value;

  const rules = state.data.rules.filter((rule) => {
    if (!state.selectedActions.has(rule.action)) return false;
    if (selectedInterface && rule.interface !== selectedInterface) return false;
    if (selectedProtocol && rule.protocol !== selectedProtocol) return false;
    if (!query) return true;
    return [
      rule.number,
      rule.action,
      rule.interface,
      rule.interface_label,
      rule.protocol,
      rule.source,
      rule.source_label,
      aliasSearchText(rule.source),
      rule.destination,
      rule.destination_label,
      aliasSearchText(rule.destination),
      rule.destination_port,
      rule.description,
    ]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });

  state.visibleRules = rules;
  renderNetwork(rules);
  renderRules(rules);
  els.visibleCount.textContent = `${rules.length} reglas visibles`;
  els.rulePanelCount.textContent = rules.length;
  els.statusText.textContent = state.data.name;
}

function renderNetwork(rules) {
  const ruleIds = new Set(rules.map((rule) => rule.id));
  const edges = state.data.edges
    .filter((edge) => ruleIds.has(edge.ruleId))
    .map((edge) => ({ ...edge, label: state.labels ? `#${edge.ruleNumber} ${edge.label}` : "" }));
  const nodeIds = new Set();
  edges.forEach((edge) => {
    nodeIds.add(edge.from);
    nodeIds.add(edge.to);
  });
  const nodes = state.data.nodes.filter((node) => nodeIds.has(node.id));

  const networkData = {
    nodes: new vis.DataSet(positionNodes(nodes)),
    edges: new vis.DataSet(edges),
  };
  const options = {
    autoResize: true,
    groups: groupOptions,
    nodes: {
      borderWidth: 2,
      font: { color: "#172033", face: "Segoe UI", size: 14, multi: false },
      margin: 10,
      shadow: { enabled: true, color: "rgba(23,32,51,0.16)", size: 8, x: 0, y: 3 },
    },
    edges: {
      font: { color: "#334155", face: "Segoe UI", size: 11, strokeWidth: 3, strokeColor: "#ffffff" },
      selectionWidth: 3,
      hoverWidth: 3,
    },
    physics: {
      enabled: state.physics,
      solver: "forceAtlas2Based",
      forceAtlas2Based: {
        gravitationalConstant: -65,
        centralGravity: 0.012,
        springLength: 145,
        springConstant: 0.06,
        avoidOverlap: 0.55,
      },
      stabilization: { enabled: true, iterations: 160, fit: true },
    },
    interaction: {
      hover: true,
      tooltipDelay: 140,
      navigationButtons: true,
      keyboard: true,
    },
    layout: {
      improvedLayout: true,
      randomSeed: 42,
    },
  };

  const container = document.getElementById("network");
  state.network = new vis.Network(container, networkData, options);
  const fitNetwork = () => {
    if (!state.network) return;
    state.network.moveTo({ position: { x: 0, y: 0 }, scale: 0.56, animation: false });
    window.setTimeout(() => {
      state.network.fit({ animation: { duration: 450, easingFunction: "easeInOutQuad" } });
    }, 80);
  };
  window.setTimeout(fitNetwork, 250);
  window.setTimeout(fitNetwork, 1100);
  window.setTimeout(fitNetwork, 2600);
  state.network.once("stabilizationIterationsDone", () => {
    state.network.setOptions({ physics: { enabled: state.physics } });
    fitNetwork();
  });
  state.network.on("selectEdge", (params) => {
    const edgeId = params.edges[0];
    const edge = state.data.edges.find((item) => item.id === edgeId);
    if (edge) highlightRule(edge.ruleId);
  });
  state.network.on("select", (params) => {
    if (!params.nodes.length) {
      if (!params.edges.length) hideAliasDetails();
      return;
    }
    const nodeId = params.nodes[0];
    const node = state.data.nodes.find((item) => item.id === nodeId);
    if (node?.group === "alias") {
      showAliasDetails(nodeId);
    } else {
      hideAliasDetails();
    }
  });
}

function positionNodes(nodes) {
  const grouped = nodes.reduce((acc, node) => {
    const group = node.group || "host";
    acc[group] = acc[group] || [];
    acc[group].push(node);
    return acc;
  }, {});
  const radiusByGroup = {
    any: 0,
    interface: 155,
    interface_ip: 240,
    private: 320,
    alias: 410,
    host: 500,
    public: 585,
  };
  const order = ["any", "interface", "interface_ip", "private", "alias", "host", "public"];
  const positioned = [];

  order.forEach((group, ringIndex) => {
    const items = grouped[group] || [];
    const radius = radiusByGroup[group] ?? 500;
    items.forEach((node, index) => {
      if (group === "any") {
        positioned.push({ ...node, x: 0, y: 0 });
        return;
      }
      const angleOffset = ringIndex * 0.34;
      const angle = (Math.PI * 2 * index) / Math.max(items.length, 1) + angleOffset;
      positioned.push({
        ...node,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
      });
    });
  });

  Object.keys(grouped)
    .filter((group) => !order.includes(group))
    .forEach((group) => {
      grouped[group].forEach((node, index) => {
        const angle = (Math.PI * 2 * index) / Math.max(grouped[group].length, 1);
        positioned.push({ ...node, x: Math.cos(angle) * 520, y: Math.sin(angle) * 520 });
      });
    });

  return positioned;
}

function renderRules(rules) {
  els.rulesBody.innerHTML = rules
    .map((rule) => {
      const port = rule.destination_port === "any" ? rule.protocol.toUpperCase() : `${rule.protocol.toUpperCase()}:${rule.destination_port}`;
      const actionText = { pass: "Pass", block: "Block", reject: "Reject", unknown: "Otro" }[rule.action] || rule.action_label;
      return `<tr data-rule-id="${escapeHtml(rule.id)}">
        <td>${rule.number}</td>
        <td><span class="badge ${escapeHtml(rule.action)}">${escapeHtml(actionText)}</span></td>
        <td>${escapeHtml(rule.interface_label)}</td>
        <td>
          <div class="flow">
            <strong>${escapeHtml(rule.source_label)} -> ${escapeHtml(rule.destination_label)}</strong>
            <span>${escapeHtml(rule.description)}${rule.disabled ? " | Deshabilitada" : ""}</span>
          </div>
        </td>
        <td>${escapeHtml(port)}</td>
      </tr>`;
    })
    .join("");
}

function showAliasDetails(aliasName) {
  const alias = state.data?.aliases?.[aliasName];
  if (!alias) return;
  state.selectedAlias = alias;
  els.aliasPanel.hidden = false;
  els.aliasName.textContent = alias.name;

  const count = alias.count ?? (alias.entries || []).length;
  const meta = [`Tipo ${alias.type || "alias"}`, `${count} objetos`];
  if (alias.updatefreq) meta.push(`Actualiza ${alias.updatefreq}h`);
  els.aliasMeta.textContent = meta.join(" | ");

  els.aliasDescription.textContent = [alias.descr, alias.url].filter(Boolean).join(" | ");
  els.aliasSearchInput.value = "";
  renderAliasItems();
}

function hideAliasDetails() {
  state.selectedAlias = null;
  els.aliasPanel.hidden = true;
  els.aliasItemsBody.innerHTML = "";
  els.aliasSearchInput.value = "";
}

function aliasEntries(alias) {
  if (Array.isArray(alias.entries) && alias.entries.length) return alias.entries;
  return (alias.addresses || []).map((value, index) => ({
    value,
    kind: alias.type === "port" ? "Puerto" : "Objeto",
    description: (alias.details || [])[index] || "",
  }));
}

function renderAliasItems() {
  const alias = state.selectedAlias;
  if (!alias) return;

  const query = els.aliasSearchInput.value.trim().toLowerCase();
  const entries = aliasEntries(alias).filter((entry) =>
    [entry.value, entry.kind, entry.description].join(" ").toLowerCase().includes(query)
  );

  if (!aliasEntries(alias).length) {
    els.aliasItemsBody.innerHTML = `<tr><td class="alias-empty" colspan="3">Sin objetos guardados en el XML.</td></tr>`;
    return;
  }

  if (!entries.length) {
    els.aliasItemsBody.innerHTML = `<tr><td class="alias-empty" colspan="3">Sin coincidencias.</td></tr>`;
    return;
  }

  els.aliasItemsBody.innerHTML = entries
    .map(
      (entry) => `<tr>
        <td>${escapeHtml(entry.value)}</td>
        <td>${escapeHtml(entry.kind || "")}</td>
        <td>${escapeHtml(entry.description || "")}</td>
      </tr>`
    )
    .join("");
}

function highlightRule(ruleId) {
  const row = els.rulesBody.querySelector(`[data-rule-id="${CSS.escape(ruleId)}"]`);
  if (!row) return;
  row.scrollIntoView({ block: "center", behavior: "smooth" });
  row.animate(
    [
      { backgroundColor: "#dbeafe" },
      { backgroundColor: "transparent" },
    ],
    { duration: 1200 }
  );
}

function exportJson() {
  if (!state.data) return;
  const blob = new Blob([JSON.stringify(state.data, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${state.data.name.replace(/\.xml$/i, "")}-diagram.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function currentFilterSummary() {
  const actionLabels = { pass: "Pass", block: "Block", reject: "Reject", unknown: "Otro" };
  const allActions = ["pass", "block", "reject", "unknown"];
  const included = allActions.filter((action) => state.selectedActions.has(action)).map((action) => actionLabels[action]);
  const excluded = allActions.filter((action) => !state.selectedActions.has(action)).map((action) => actionLabels[action]);
  const visibleRules = state.visibleRules || [];
  const ruleNumbers = visibleRules.map((rule) => rule.number);

  return {
    dataset: state.data?.name || "",
    visible: visibleRules.length,
    total: state.data?.stats?.total_rules || 0,
    hidden: Math.max((state.data?.stats?.total_rules || 0) - visibleRules.length, 0),
    includedActions: included.length ? included.join(", ") : "Ninguna",
    excludedActions: excluded.length ? excluded.join(", ") : "Ninguna",
    interface: els.interfaceSelect.value || "Todas",
    protocol: els.protocolSelect.value || "Todos",
    query: els.searchInput.value.trim() || "Sin busqueda",
    firstRule: ruleNumbers.length ? Math.min(...ruleNumbers) : "-",
    lastRule: ruleNumbers.length ? Math.max(...ruleNumbers) : "-",
  };
}

function safeFileName(value) {
  return String(value || "pfschematic")
    .replace(/\.xml$/i, "")
    .replace(/[^\w.-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase();
}

function waitForFrame() {
  return new Promise((resolve) => window.requestAnimationFrame(() => window.requestAnimationFrame(resolve)));
}

function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = String(text || "").split(/\s+/);
  let line = "";
  let currentY = y;

  words.forEach((word) => {
    const testLine = line ? `${line} ${word}` : word;
    if (ctx.measureText(testLine).width > maxWidth && line) {
      ctx.fillText(line, x, currentY);
      line = word;
      currentY += lineHeight;
      return;
    }
    line = testLine;
  });

  if (line) ctx.fillText(line, x, currentY);
  return currentY + lineHeight;
}

function drawPill(ctx, x, y, color, label) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x + 8, y + 8, 8, Math.PI / 2, Math.PI * 1.5);
  ctx.arc(x + 112, y + 8, 8, Math.PI * 1.5, Math.PI / 2);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#ffffff";
  ctx.font = "700 18px Segoe UI, Arial";
  ctx.fillText(label, x + 18, y + 15);
}

function drawExportLegend(ctx, x, y, width, summary) {
  ctx.fillStyle = "#172033";
  ctx.font = "700 26px Segoe UI, Arial";
  ctx.fillText("Leyenda y filtros", x, y);

  ctx.font = "18px Segoe UI, Arial";
  ctx.fillStyle = "#334155";
  let textY = y + 36;
  textY = wrapCanvasText(
    ctx,
    `Reglas visibles: ${summary.visible} de ${summary.total}. Ocultas por filtros: ${summary.hidden}. Rango visible segun orden pfSense: #${summary.firstRule} a #${summary.lastRule}.`,
    x,
    textY,
    width,
    26
  );
  textY = wrapCanvasText(
    ctx,
    `Acciones incluidas: ${summary.includedActions}. Acciones filtradas fuera: ${summary.excludedActions}. Interfaz: ${summary.interface}. Protocolo: ${summary.protocol}. Busqueda: ${summary.query}.`,
    x,
    textY + 2,
    width,
    26
  );

  const pillY = textY + 12;
  drawPill(ctx, x, pillY, "#18a058", "Pass");
  drawPill(ctx, x + 134, pillY, "#d64545", "Block");
  drawPill(ctx, x + 268, pillY, "#f08c00", "Reject");
  drawPill(ctx, x + 402, pillY, "#64748b", "Deshab.");

  ctx.font = "18px Segoe UI, Arial";
  ctx.fillStyle = "#334155";
  wrapCanvasText(
    ctx,
    "Cada arista muestra #n antes del protocolo/puerto. Ese numero es el orden original de la regla dentro del XML de pfSense. Los nodos guardan en el tooltip la primera, ultima y lista resumida de reglas asociadas.",
    x,
    pillY + 54,
    width,
    26
  );
}

async function buildExportCanvas() {
  if (!state.data || !state.network) throw new Error("No hay diagrama para exportar.");
  state.network.redraw();
  await waitForFrame();

  const sourceCanvas = document.querySelector("#network canvas");
  if (!sourceCanvas || !sourceCanvas.width || !sourceCanvas.height) {
    throw new Error("No se pudo capturar el lienzo del diagrama.");
  }

  const summary = currentFilterSummary();
  const exportWidth = 1800;
  const margin = 56;
  const graphWidth = exportWidth - margin * 2;
  const graphHeight = Math.round(graphWidth * (sourceCanvas.height / sourceCanvas.width));
  const headerHeight = 174;
  const legendHeight = 250;
  const exportHeight = headerHeight + graphHeight + legendHeight + margin;
  const canvas = document.createElement("canvas");
  canvas.width = exportWidth;
  canvas.height = exportHeight;
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = "#f8fafc";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#172033";
  ctx.fillRect(0, 0, canvas.width, headerHeight);

  ctx.fillStyle = "#a7f3d0";
  ctx.fillRect(margin, 38, 72, 72);
  ctx.fillStyle = "#172033";
  ctx.font = "800 30px Segoe UI, Arial";
  ctx.fillText("PS", margin + 17, 84);

  ctx.fillStyle = "#ffffff";
  ctx.font = "800 42px Segoe UI, Arial";
  ctx.fillText("PfSchematic", margin + 92, 68);
  ctx.font = "18px Segoe UI, Arial";
  ctx.fillStyle = "#b8efe0";
  ctx.fillText("Propiedad de Alex Cabello Leiva, consultor de innovacion y ciberseguridad.", margin + 92, 100);
  ctx.fillStyle = "#d9f6ee";
  ctx.fillText(summary.dataset, margin + 92, 130);

  const graphY = headerHeight + 34;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(margin - 1, graphY - 1, graphWidth + 2, graphHeight + 2);
  ctx.strokeStyle = "#d9e2ec";
  ctx.lineWidth = 2;
  ctx.strokeRect(margin - 1, graphY - 1, graphWidth + 2, graphHeight + 2);
  ctx.drawImage(sourceCanvas, margin, graphY, graphWidth, graphHeight);

  drawExportLegend(ctx, margin, graphY + graphHeight + 56, graphWidth, summary);
  return canvas;
}

async function exportPng() {
  try {
    const canvas = await buildExportCanvas();
    const link = document.createElement("a");
    link.href = canvas.toDataURL("image/png");
    link.download = `${safeFileName(state.data?.name)}-pfschematic.png`;
    link.click();
    showToast("PNG exportado con leyenda");
  } catch (error) {
    showToast(error.message);
  }
}

async function exportPdf() {
  try {
    const canvas = await buildExportCanvas();
    const imageData = canvas.toDataURL("image/png");
    const printWindow = window.open("", "_blank");
    if (!printWindow) throw new Error("Permita ventanas emergentes para generar el PDF.");
    printWindow.document.write(`<!doctype html>
      <html lang="es">
        <head>
          <meta charset="utf-8">
          <title>PfSchematic PDF</title>
          <style>
            @page { size: landscape; margin: 10mm; }
            body { margin: 0; background: #ffffff; }
            img { width: 100%; display: block; }
          </style>
        </head>
        <body>
          <img src="${imageData}" alt="Exportacion PfSchematic">
          <script>
            window.addEventListener("load", () => {
              window.focus();
              window.print();
            });
          <\/script>
        </body>
      </html>`);
    printWindow.document.close();
    showToast("PDF listo para guardar desde el dialogo de impresion");
  } catch (error) {
    showToast(error.message);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.querySelectorAll("[data-action-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const action = button.dataset.actionFilter;
    if (state.selectedActions.has(action)) {
      state.selectedActions.delete(action);
      button.classList.remove("is-active");
    } else {
      state.selectedActions.add(action);
      button.classList.add("is-active");
    }
    applyFilters();
  });
});

els.sampleButton.addEventListener("click", () => {
  loadSample().catch((error) => showToast(error.message));
});
els.xmlInput.addEventListener("change", () => {
  const file = els.xmlInput.files[0];
  if (file) uploadXml(file).catch((error) => showToast(error.message));
});
els.searchInput.addEventListener("input", applyFilters);
els.interfaceSelect.addEventListener("change", applyFilters);
els.protocolSelect.addEventListener("change", applyFilters);
els.aliasSearchInput.addEventListener("input", renderAliasItems);
els.aliasCloseButton.addEventListener("click", hideAliasDetails);
els.fitButton.addEventListener("click", () => state.network?.fit({ animation: true }));
els.physicsButton.addEventListener("click", () => {
  state.physics = !state.physics;
  els.physicsButton.classList.toggle("is-active", state.physics);
  state.network?.setOptions({ physics: { enabled: state.physics } });
});
els.labelsButton.addEventListener("click", () => {
  state.labels = !state.labels;
  els.labelsButton.classList.toggle("is-active", state.labels);
  applyFilters();
});
els.exportButton.addEventListener("click", exportJson);
els.exportPngButton.addEventListener("click", exportPng);
els.exportPdfButton.addEventListener("click", exportPdf);

window.addEventListener("load", () => {
  if (window.lucide) window.lucide.createIcons();
  loadSample().catch((error) => showToast(error.message));
});
