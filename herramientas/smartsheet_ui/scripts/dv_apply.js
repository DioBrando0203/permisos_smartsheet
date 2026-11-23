// Ajusta panel (Details Panel) y/o tabla (Visible fields) de una Dynamic View con el mismo PUT que usa la pantalla.
// arg = { id, expect, panel?: [[title, "ro"|"req"|""], ...], table?: [title, ...],
//         rules?: { "<rule name>": [["EDITABLE"|"READ_ONLY"|"HIDE"|"REQUIRE", [titles]], ...] }, dry?: bool }
// Las reglas que no se nombran se conservan tal cual. Devuelve el resultado releído.
let xsrf = null;
const grab = (r) => { const v = r.headers()["x-smar-xsrf"]; if (v) xsrf = v; };
page.on("request", grab);
await page.goto(`https://app.smartsheet.com/dynamicview/views/${arg.id}/admin/basic`, { waitUntil: "load" });
await page.waitForTimeout(6000);
page.off("request", grab);
if (!xsrf) return JSON.stringify({ error: "no encontré el token de la página" });
return JSON.stringify(
  await page.evaluate(async ({ arg, xsrf }) => {
    const get = async (u) => (await fetch(u, { credentials: "include" })).json();
    const base = `/dynamicview/api/views/${arg.id}`;
    const view = await get(`${base}?include=config,shares,form,filters`);
    if ((view.name || "").trim() !== arg.expect) return { error: `nombre inesperado: ${view.name}` };
    const meta = await get(`${base}/sourcemetadata`);
    const byTitle = Object.fromEntries(meta.columns.map((c) => [c.title, c]));
    const byId = Object.fromEntries(meta.columns.map((c) => [String(c.id), c.title]));
    const idOf = (t) => {
      if (!byTitle[t]) throw new Error(`no existe la columna "${t}"`);
      return byTitle[t].id;
    };
    const body = {};
    try {
      if (arg.panel) {
        const fields = arg.panel.map(([t, flag], i) => ({
          columnId: idOf(t), ordinal: i, required: flag === "req", readOnly: flag === "ro", hidden: false,
        }));
        const inPanel = new Set(fields.map((f) => String(f.columnId)));
        const rules = ((view.form && view.form.rules) || []).map((r) => {
          if (!arg.rules || !arg.rules[r.name]) return r;
          const actions = arg.rules[r.name].map(([type, titles]) => {
            const old = r.actions.find((a) => a.actionType === type);
            return { actionType: type, fields: titles.map(idOf), id: old ? old.id : crypto.randomUUID() };
          });
          return { ...r, actions };
        });
        for (const r of rules) for (const a of r.actions) for (const f of a.fields)
          if (!inPanel.has(String(f))) throw new Error(`la regla ${r.name} usa ${byId[String(f)]}, que no está en el panel`);
        body.form = { fields, rules };
      }
      if (arg.table) {
        body.config = {
          displayedFields: arg.table.map((t, i) => ({ type: byTitle[t] ? byTitle[t].type : idOf(t), ordinal: i, columnId: idOf(t) })),
        };
      }
      if (arg.name) body.name = arg.name;
      if (arg.config || arg.userColumn !== undefined) {
        body.config = { ...(body.config || {}), ...(arg.config || {}) };
        if (arg.userColumn !== undefined) body.config.userColumnId = arg.userColumn ? idOf(arg.userColumn) : null;
      }
    } catch (e) {
      return { error: e.message };
    }
    if (arg.dry) return { dry: body };
    const res = await fetch(base, {
      method: "PUT", credentials: "include", headers: { "Content-Type": "application/json", "x-smar-xsrf": xsrf }, body: JSON.stringify(body),
    });
    if (!res.ok) return { error: `PUT ${res.status}: ${(await res.text()).slice(0, 300)}` };
    const after = await get(`${base}?include=config,shares,form,filters`);
    const name = (id) => byId[String(id)] || id;
    return {
      name: after.name,
      user: after.config.userColumnId ? name(after.config.userColumnId) : null,
      table: (after.config.displayedFields || []).sort((a, b) => a.ordinal - b.ordinal).map((f) => name(f.columnId)),
      panel: ((after.form && after.form.fields) || []).sort((a, b) => a.ordinal - b.ordinal)
        .map((f) => name(f.columnId) + (f.readOnly ? "[RO]" : "") + (f.required ? "[REQ]" : "")),
      rules: ((after.form && after.form.rules) || []).map((r) => `${r.name}: ` + r.actions.map((a) => `${a.actionType} ${a.fields.map(name).join("/")}`).join("; ")),
      config: Object.fromEntries(Object.entries(after.config).filter(([k]) => k !== "displayedFields")),
    };
  }, { arg, xsrf }),
);
