// Navegador de Smartsheet manejado por HTTP local (Playwright). Ver README.md y
// backend/docs/PLAYWRIGHT_SMARTSHEET.md. Sólo con autorización del usuario.
//
// - El usuario inicia sesión a mano la primera vez; la sesión queda en el perfil (fuera del repo).
// - Escucha sólo en 127.0.0.1: nadie de la red puede manejarlo.
// - No guarda contraseñas, tokens ni respuestas: sólo capturas en la carpeta de capturas.
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { chromium } = require("playwright");

const SCRIPTS = process.env.PW_SCRIPTS || path.join(__dirname, "scripts");
const PROFILE =
  process.env.PW_PROFILE || path.join(os.homedir(), ".config", "galp_smartsheet_ui", "profile");
const SHOTS = process.env.PW_SHOTS || path.join(os.tmpdir(), "smartsheet_ui_shots");
const PORT = Number(process.env.PW_PORT || 9334);
const START = process.env.PW_START || "https://app.smartsheet.com/";

fs.mkdirSync(SHOTS, { recursive: true });

const readScript = (name) => fs.readFileSync(path.resolve(SCRIPTS, name), "utf8");
const readArg = (q) => {
  if (q("argjson")) return JSON.parse(q("argjson"));
  return q("arg") ? JSON.parse(fs.readFileSync(path.resolve(SCRIPTS, q("arg")), "utf8")) : null;
};

async function handle(u, page, pages) {
  const q = (k, d) => u.searchParams.get(k) ?? d;
  const wait = (ms) => page.waitForTimeout(Number(q("wait", ms)));
  switch (u.pathname) {
    case "/state":
      return pages.map((p, i) => `${i} ${p.url()}`).join("\n");
    case "/goto":
      await page.goto(q("url"), { waitUntil: "domcontentloaded", timeout: 60000 });
      await wait(7000);
      return page.url();
    case "/shot": {
      const file = path.join(SHOTS, `${q("name", "shot")}.png`);
      await page.screenshot({ path: file, fullPage: q("full") === "1" });
      return file;
    }
    case "/text":
      return (await page.evaluate(() => document.body.innerText)).slice(0, Number(q("n", 5000)));
    case "/aria":
      return (await page.locator(q("sel", "body")).first().ariaSnapshot()).slice(0, Number(q("n", 8000)));
    case "/click":
      await page.getByText(q("t"), { exact: q("exact") === "1" }).nth(Number(q("i", 0))).click();
      await wait(3000);
      return "ok";
    case "/clickrole":
      await page
        .getByRole(q("role"), { name: q("name"), exact: q("exact") === "1" })
        .nth(Number(q("i", 0)))
        .click();
      await wait(3000);
      return "ok";
    case "/clickxy":
      await page.mouse.click(Number(q("x")), Number(q("y")));
      await wait(3000);
      return "ok";
    case "/type":
      await page.keyboard.type(q("t"), { delay: 40 });
      await wait(800);
      return "ok";
    case "/key":
      await page.keyboard.press(q("k", "Escape"));
      await wait(1500);
      return "ok";
    case "/scroll":
      await page.mouse.move(Number(q("x", 700)), Number(q("y", 500)));
      await page.mouse.wheel(Number(q("dx", 0)), Number(q("dy", 600)));
      await wait(1500);
      return "ok";
    case "/drag": {
      const [x1, y1, x2, y2] = ["x1", "y1", "x2", "y2"].map((k) => Number(q(k)));
      await page.mouse.move(x1, y1);
      await page.mouse.down();
      await page.mouse.move(x1 + 5, y1 + 5, { steps: 5 });
      await page.mouse.move(x2, y2, { steps: Number(q("steps", 25)) });
      await page.mouse.up();
      await wait(1500);
      return "ok";
    }
    case "/box": {
      const box = await page.getByText(q("t"), { exact: q("exact") === "1" }).nth(Number(q("i", 0))).boundingBox();
      return JSON.stringify(box);
    }
    case "/eval": {
      const result = await page.evaluate(readScript(q("f")));
      return typeof result === "string" ? result : JSON.stringify(result, null, 1);
    }
    case "/run": {
      const AsyncFn = Object.getPrototypeOf(async function () {}).constructor;
      return String(await new AsyncFn("page", "arg", readScript(q("f")))(page, readArg(q)));
    }
    default:
      return null;
  }
}

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: false,
    viewport: { width: 1500, height: 900 },
  });
  const first = ctx.pages()[0] || (await ctx.newPage());
  await first.goto(START, { waitUntil: "domcontentloaded", timeout: 60000 });
  console.log("listo:", first.url());
  http
    .createServer(async (req, res) => {
      const u = new URL(req.url, "http://local");
      const pages = ctx.pages();
      const page = pages[Number(u.searchParams.get("tab") ?? pages.length - 1)];
      try {
        const out = await handle(u, page, pages);
        res.statusCode = out === null ? 404 : 200;
        res.end(out ?? "ruta desconocida");
      } catch (error) {
        res.statusCode = 500;
        res.end(String(error).slice(0, 600));
      }
    })
    .listen(PORT, "127.0.0.1", () => console.log(`escuchando en http://127.0.0.1:${PORT}`));
})().catch((error) => {
  console.error(String(error));
  process.exit(1);
});
