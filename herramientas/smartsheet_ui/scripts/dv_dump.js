// /run: configuración de una o varias Dynamic Views con títulos de columna (sólo lectura).
// arg = { ids: ["<id de vista>", ...] }. Los accesos salen sin correos (sólo nivel y si es grupo).
if (!page.url().startsWith("https://app.smartsheet.com/")) {
  await page.goto("https://app.smartsheet.com/dynamicview/", { waitUntil: "load" });
  await page.waitForTimeout(5000);
}
return JSON.stringify(
  await page.evaluate(async (ids) => {
    const get = async (u) => {
      const r = await fetch(u, { credentials: "include" });
      return r.ok ? r.json() : { error: r.status };
    };
    const out = {};
    for (const id of ids) {
      const view = await get(`/dynamicview/api/views/${id}?include=config,shares,form,filters`);
      const meta = await get(`/dynamicview/api/views/${id}/sourcemetadata`);
      if (view.error || meta.error) {
        out[id] = { error: view.error || meta.error };
        continue;
      }
      const title = Object.fromEntries((meta.columns || []).map((c) => [String(c.id), c.title]));
      const name = (cid) => title[String(cid)] || cid;
      const cfg = view.config || {};
      const form = view.form || {};
      out[id] = {
        name: view.name.trim(),
        source: `${view.viewSourceType} ${meta.sourceName} (${view.viewSourceId})`,
        user_column: cfg.userColumnId ? name(cfg.userColumnId) : null,
        sheet_filter: cfg.sheetFilterId || null,
        new_rows_to: cfg.intakeSheetId || null,
        comments: { show: cfg.displayComments, add: cfg.canAddComments },
        attachments: { show: cfg.displayAttachments, add: cfg.canAddAttachments },
        download: cfg.canDownload,
        table: (cfg.displayedFields || []).sort((a, b) => a.ordinal - b.ordinal).map((f) => name(f.columnId)),
        panel: (form.fields || [])
          .sort((a, b) => a.ordinal - b.ordinal)
          .map((f) => name(f.columnId) + (f.readOnly ? " [RO]" : "") + (f.required ? " [REQ]" : "")),
        rules: (form.rules || []).map((r) => ({
          name: r.name,
          when: `${name(r.criteria.columnId)} ${r.criteria.comparator} ${JSON.stringify(r.criteria.options)}`,
          actions: r.actions.map((a) => `${a.actionType}: ${a.fields.map(name).join(", ")}`),
        })),
        shares: (view.shares || []).map((s) => ({
          level: s.accessLevel,
          group: Boolean(s.grantedToGroupId),
          domain: Boolean(s.grantedToDomain),
          person: Boolean(s.email),
        })),
      };
    }
    return out;
  }, arg.ids),
  null,
  1,
);
