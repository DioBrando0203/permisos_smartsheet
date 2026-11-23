// Crea UNA regla de formato condicional en el cuadro "Conditional Formatting" ya abierto (no guarda).
// arg = { column, values[], target: "row" | "<columna>", bold, strike, bg: "rgb(...)" | null, fg: "rgb(...)" | null }
const log = [];
const wait = (ms) => page.waitForTimeout(ms);

// Centro del elemento con texto exacto `text` dentro del contenedor más cercano al ancla `anchor`.
async function locate(anchor, text) {
  return page.evaluate(
    ([anchor, text]) => {
      const norm = (s) => (s || "").replace(/\s+/g, " ").trim();
      const exact = (t) =>
        Array.from(document.querySelectorAll("body *")).filter((e) => {
          if (norm(e.textContent) !== t) return false;
          for (const c of e.children) if (norm(c.textContent) === t) return false;
          const r = e.getBoundingClientRect();
          return r.width > 0 && r.height > 0;
        });
      const anchors = exact(anchor);
      if (!anchors.length) return null;
      const a = anchors[anchors.length - 1];
      if (text === null) {
        const r = a.getBoundingClientRect();
        return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
      }
      for (let box = a; box && box !== document.body; box = box.parentElement) {
        const hits = exact(text).filter((e) => box.contains(e) && e !== a);
        if (hits.length) {
          hits[0].scrollIntoView({ block: "nearest" });
          const r = hits[0].getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        }
      }
      return null;
    },
    [anchor, text],
  );
}

async function click(anchor, text, ms = 900) {
  const p = await locate(anchor, text);
  if (!p) throw new Error(`no encontré "${text}" junto a "${anchor}"`);
  await page.mouse.click(p.x, p.y);
  await wait(ms);
  return p;
}

// Muestra de color visible con ese fondo, en el recuadro de la paleta abierta (debajo de "No Background").
async function swatch(color) {
  const nb = (await locate("No Background", null)) || (await locate("Automatic", null));
  if (!nb) return null;
  return page.evaluate(
    ([color, nb]) => {
      for (const e of document.querySelectorAll("body *")) {
        const r = e.getBoundingClientRect();
        if (r.width < 8 || r.width > 22 || r.height < 8 || r.height > 22) continue;
        if (getComputedStyle(e).backgroundColor !== color) continue;
        const cx = r.x + r.width / 2;
        const cy = r.y + r.height / 2;
        if (Math.abs(cx - nb.x) > 80 || cy < nb.y || cy > nb.y + 110) continue;
        return { x: cx, y: cy };
      }
      return null;
    },
    [color, nb],
  );
}

async function pickColor(fs, dx, color) {
  await page.mouse.click(fs.x + dx, fs.y + 101);
  await wait(700);
  const s = await swatch(color);
  if (!s) throw new Error(`no encontré el color ${color}`);
  await page.mouse.click(s.x, s.y);
  await wait(700);
}

// arg.from = "target" retoma una regla a medias (formato ya puesto y cerrado).
if (!arg.from) {
// 1. Regla nueva.
await click("Note: higher rules take priority over lower rules.", "Add New Rule", 1500);

// 2. Formato (la regla nueva es la que dice <set condition>).
await click("<set condition>", "this format", 1200);
const fs = await locate("Font Size", null);
if (!fs) throw new Error("no se abrió el formato");
if (arg.bold) await page.mouse.click(fs.x - 19, fs.y + 52), await wait(500);
if (arg.strike) await page.mouse.click(fs.x + 20, fs.y + 77), await wait(500);
if (arg.bg) await pickColor(fs, -7, arg.bg);
if (arg.fg) await pickColor(fs, 34, arg.fg);
await page.mouse.click(fs.x + 39, fs.y - 59);
await wait(800);
log.push("formato");
}

// 3. A qué se aplica.
if (arg.target !== "row" && arg.from !== "condition") {
  await click("<set condition>", "entire row", 1200);
  await listPick("Select what to format:", arg.target, { x0: -70, x1: 175, y0: 20, y1: 210, wx: 0, wy: 120 });
  log.push(`destino ${arg.target}`);
  await click("Select what to format:", "OK", 1000);
}

// 4. Condición.
await click("<set condition>", null, 1500);
// Las listas sólo dibujan lo visible: se sube al inicio y se baja hasta encontrar el texto,
// buscando sólo en el recuadro de la lista (relativo al ancla).
async function listPick(anchorText, v, box) {
  const a = typeof anchorText === "string" ? await locate(anchorText, null) : anchorText;
  if (!a) throw new Error(`no encontré "${anchorText}"`);
  await page.mouse.move(a.x + box.wx, a.y + box.wy);
  await page.mouse.wheel(0, -5000);
  await wait(400);
  for (let i = 0; i < 40; i++) {
    const p = await page.evaluate(
      ([v, a, b]) => {
        const norm = (s) => (s || "").replace(/\s+/g, " ").trim();
        for (const e of document.querySelectorAll("body *")) {
          if (norm(e.textContent) !== norm(v)) continue;
          if (Array.from(e.children).some((c) => norm(c.textContent) === norm(v))) continue;
          const r = e.getBoundingClientRect();
          const cx = r.x + r.width / 2;
          const cy = r.y + r.height / 2;
          if (r.width === 0 || cx < a.x + b.x0 || cx > a.x + b.x1 || cy < a.y + b.y0 || cy > a.y + b.y1) continue;
          const top = document.elementFromPoint(cx, cy);
          if (top !== e && !e.contains(top)) continue;
          return { x: cx, y: cy };
        }
        return null;
      },
      [v, a, box],
    );
    if (p) {
      await page.mouse.click(p.x, p.y);
      await wait(600);
      return;
    }
    await page.mouse.wheel(0, 115);
    await wait(350);
  }
  throw new Error(`no encontré "${v}" en la lista`);
}

const COLS = { x0: -100, x1: 170, y0: 12, y1: 245, wx: 0, wy: 120 };
const VALS = { x0: -80, x1: 420, y0: 10, y1: 215, wx: 0, wy: 120 };
await listPick("1. Select column for condition", arg.column, COLS);
await wait(800);
if (arg.explore) return (await page.getByRole("dialog", { name: "Set Condition" }).ariaSnapshot()).slice(0, 6000);
const selectAll = await locate("Select All", null);
if (!selectAll) throw new Error('no encontré "Select All"');
for (const v of arg.values) await listPick(selectAll, v, VALS);
await click("Apply format when condition is NOT met", "OK", 1500);
log.push(`condición ${arg.column}: ${arg.values.length} valores`);
return log.join("; ");
