// Renombra una Dynamic View desde General > View name y guarda; devuelve el pedido que manda la pantalla.
const sent = [];
const onReq = (r) => {
  if (r.url().includes("/dynamicview/api/") && r.method() !== "GET") {
    sent.push({ method: r.method(), url: r.url(), body: (r.postData() || "").slice(0, 6000) });
  }
};
await page.goto(`https://app.smartsheet.com/dynamicview/views/${arg.id}/admin/basic`, { waitUntil: "load" });
await page.waitForTimeout(6000);
const box = page.getByRole("textbox").first();
const before = await box.inputValue();
if (before.trim() !== arg.expect) return `nombre inesperado: "${before}"`;
await box.fill(arg.name);
await page.waitForTimeout(800);
page.on("request", onReq);
await page.getByRole("button", { name: "Save", exact: true }).click();
await page.waitForTimeout(5000);
page.off("request", onReq);
return JSON.stringify({ before, after: await box.inputValue(), sent });
