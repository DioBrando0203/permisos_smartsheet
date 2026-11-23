(() => {
  // Lee las reglas del cuadro Conditional Formatting abierto: texto y estilo de la muestra "abcde".
  const all = Array.from(document.querySelectorAll("*"));
  const samples = all.filter((e) => e.children.length === 0 && e.textContent.trim() === "abcde");
  const out = [];
  for (const s of samples) {
    let row = s.parentElement;
    while (row && !/If\s/.test(row.innerText || "")) row = row.parentElement;
    if (!row) continue;
    const text = row.innerText.replace(/\s+/g, " ").replace(/abcde/, "").trim();
    const pick = (el) => {
      const cs = getComputedStyle(el);
      return {
        bg: cs.backgroundColor,
        fg: cs.color,
        deco: cs.textDecorationLine,
        weight: cs.fontWeight,
        italic: cs.fontStyle,
      };
    };
    let bgEl = s;
    while (bgEl && getComputedStyle(bgEl).backgroundColor === "rgba(0, 0, 0, 0)") bgEl = bgEl.parentElement;
    const st = pick(s);
    st.bg = bgEl ? getComputedStyle(bgEl).backgroundColor : "none";
    const disabled = /disabled/i.test(row.className) || getComputedStyle(row).opacity < 1;
    out.push(`${text} || bg=${st.bg} fg=${st.fg} deco=${st.deco} w=${st.weight} ${st.italic}${disabled ? " [DISABLED?]" : ""}`);
  }
  return out.join("\n");
})()
