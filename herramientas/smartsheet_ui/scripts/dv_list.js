// /run: lista las Dynamic Views a las que entra la cuenta (sólo lectura).
// Devuelve id, nombre, tipo e id del origen y cuántos accesos tiene, sin correos.
if (!page.url().startsWith("https://app.smartsheet.com/")) {
  await page.goto("https://app.smartsheet.com/dynamicview/", { waitUntil: "load" });
  await page.waitForTimeout(5000);
}
const views = await page.evaluate(async () => {
  const r = await fetch("/dynamicview/api/views?include=ownerDetails", { credentials: "include" });
  return r.ok ? r.json() : { error: r.status };
});
if (!Array.isArray(views)) return JSON.stringify(views);
return views
  .map((v) => `${v.id} | ${v.name.trim()} | ${v.viewSourceType} ${v.viewSourceId} | grupos ${(v.sharedWithGroups || []).length}`)
  .sort((a, b) => a.split(" | ")[1].localeCompare(b.split(" | ")[1]))
  .join("\n");
