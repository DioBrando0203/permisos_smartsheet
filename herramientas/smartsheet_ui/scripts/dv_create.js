// /run: crea una Dynamic View en blanco sobre una hoja o reporte de Pruebas (escribe: pedir OK).
// arg = { source: "<nombre exacto de la hoja o reporte>" }. Devuelve el id de la vista nueva.
// Después se configura con dv_apply.js (nombre, tabla, panel, restricción por usuario).
await page.goto("https://app.smartsheet.com/dynamicview/", { waitUntil: "load" });
await page.waitForTimeout(6000);
await page.getByRole("button", { name: "Create new view", exact: true }).first().click();
await page.waitForTimeout(2500);
const dialog = page.getByRole("dialog");
await dialog.getByRole("searchbox", { name: "Search sheets and reports." }).fill(arg.source);
await page.waitForTimeout(4000);
const texts = (await dialog.getByRole("listitem").allInnerTexts()).map((t) => t.trim());
// Barrera: el resultado debe estar en el workspace Pruebas (AGENTS.md).
if (!texts.includes("Pruebas")) return JSON.stringify({ error: "el resultado no está en Pruebas", texts });
const escaped = arg.source.replace(/[.*+?^$()|[\]\\{}]/g, "\\$&");
const exact = new RegExp("^" + escaped + "$");
await dialog.getByRole("listitem").filter({ hasText: exact }).click();
await page.waitForTimeout(1200);
await dialog.getByRole("button", { name: "Create", exact: true }).click();
await page.waitForTimeout(8000);
const id = (page.url().match(/views\/([0-9a-f-]{36})/) || [])[1] || null;
return JSON.stringify({ id, url: page.url() });
