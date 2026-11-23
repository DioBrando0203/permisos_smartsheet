(() => {
  // Muestras de color visibles (cuadros chicos con fondo) del menú de colores abierto: centro y color.
  const out = [];
  for (const e of document.querySelectorAll("*")) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 22 || r.height < 8 || r.height > 22) continue;
    const bg = getComputedStyle(e).backgroundColor;
    if (bg === "rgba(0, 0, 0, 0)") continue;
    const vis = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    if (vis !== e && !e.contains(vis)) continue;
    out.push(`${Math.round(r.x + r.width / 2)},${Math.round(r.y + r.height / 2)} ${bg} ${e.getAttribute("title") || ""}`);
  }
  return out.join("\n");
})()
