// script.js (replace existing)
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("searchInput");
  const btn = document.getElementById("searchBtn");
  const out = document.getElementById("result");
  const msg = document.getElementById("message") || document.getElementById("result");

  const BACKEND = "http://127.0.0.1:5000/search";

  function escapeHtml(s){ return String(s||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'", "&#39;"); }

  // parse numeric price from many possible fields
  function extractNumericPrice(item){
    const candFields = ["price","offer_price","product_price","selling_price","mrp","amount"];
    for(const k of candFields){
      if(item[k]){
        const num = String(item[k]).replace(/[^\d\.,\-]/g,"").trim();
        if(num) return num;
      }
    }

    // fallback: look inside name/title for first number
    const text = (item.name || "") + " " + (item.title || "");
    const m = text.replace(/₹/g,"").match(/([0-9]{1,3}(?:[,\.\s][0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)/);
    if(m) return m[0].replace(/\s+/g,"").replace(/,/g,"");
    return "";
  }

  function fmtRupee(nStr){
    if(!nStr) return "";
    // ensure decimal / remove stray characters
    const cleaned = String(nStr).replace(/[^\d\.]/g, "");
    if(cleaned === "") return "";
    const num = Number(cleaned);
    if(Number.isNaN(num)) return nStr;
    // format with thousands separators
    return num.toLocaleString("en-IN");
  }

  function makeCard(item){
    const row = document.createElement("div");
    row.className = "card-row";
    row.style.display = "flex";
    row.style.gap = "12px";
    row.style.alignItems = "center";
    row.style.padding = "10px 8px";
    row.style.borderRadius = "8px";
    row.style.background = "rgba(255,255,255,0.03)";

    const thumb = document.createElement("div");
    thumb.style.width = "84px";
    thumb.style.height = "84px";
    thumb.style.borderRadius = "8px";
    thumb.style.overflow = "hidden";
    thumb.style.background = "#333";
    const img = document.createElement("img");
    img.src = item.image || item.image_url || "";
    img.alt = item.title || item.name || "product";
    img.style.width = "100%";
    img.style.height = "100%";
    img.style.objectFit = "cover";
    img.onerror = () => {
      img.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='84' height='84'%3E%3Crect width='100%25' height='100%25' fill='%23ddd'/%3E%3C/svg%3E";
    };
    thumb.appendChild(img);

    const meta = document.createElement("div");
    meta.style.flex = "1";

    const title = document.createElement("div");
    title.style.fontWeight = "600";
    title.style.fontSize = "15px";
    title.style.color = "#fff";

    const link = document.createElement("a");
    link.href = item.link || item.url || "#";
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.innerHTML = escapeHtml(item.title || item.name || "Untitled product");
    link.style.color = "inherit";
    link.style.textDecoration = "none";
    title.appendChild(link);

    const priceRow = document.createElement("div");
    priceRow.style.marginTop = "6px";
    priceRow.style.display = "flex";
    priceRow.style.alignItems = "center";
    priceRow.style.gap = "10px";

    const raw = extractNumericPrice(item);
    const formatted = fmtRupee(raw);

    const price = document.createElement("div");
    price.style.fontWeight = "700";
    price.style.color = "#d1ffd1";
    price.style.fontSize = "16px";
    price.textContent = formatted ? "₹ " + formatted : "Price unavailable";

    const source = document.createElement("div");
    source.style.fontSize = "13px";
    source.style.color = "#ccc";
    source.textContent = item.source ? "(" + item.source + ")" : "";

    priceRow.appendChild(price);
    priceRow.appendChild(source);

    meta.appendChild(title);
    meta.appendChild(priceRow);

    row.appendChild(thumb);
    row.appendChild(meta);

    return row;
  }

  function renderArray(arr){
    out.innerHTML = "";
    if(!Array.isArray(arr) || arr.length === 0){
      msg.textContent = "No products found.";
      return;
    }
    msg.textContent = `Showing ${arr.length} result(s) — sorted by lowest price first`;

    // render each card
    const container = document.createElement("div");
    container.style.display = "grid";
    container.style.gap = "12px";

    arr.forEach(it => {
      const card = makeCard(it);
      container.appendChild(card);
    });

    out.appendChild(container);
  }

  function renderLegacy(data){
    // legacy structure: { db_recent:[], amazon_live:[] }
    out.innerHTML = "";
    const wrapper = document.createElement("div");

    const db = Array.isArray(data.db_recent) ? data.db_recent : [];
    const am = Array.isArray(data.amazon_live) ? data.amazon_live : [];

    const dbHeader = document.createElement("div");
    dbHeader.style.color = "#fff";
    dbHeader.style.fontWeight = "600";
    dbHeader.textContent = `Recent DB entries (${db.length})`;
    wrapper.appendChild(dbHeader);
    if(db.length === 0){
      const p = document.createElement("div"); p.style.color="#ccc"; p.textContent = "No DB entries.";
      wrapper.appendChild(p);
    } else {
      db.forEach(r => {
        const el = document.createElement("div");
        el.innerHTML = `<a href="${escapeHtml(r.url||'#')}" target="_blank">${escapeHtml(r.name||r.id||'item')}</a> — ${escapeHtml(String(r.price||'N/A'))}`;
        wrapper.appendChild(el);
      });
    }

    const amHeader = document.createElement("div");
    amHeader.style.color="#fff"; amHeader.style.fontWeight="600"; amHeader.textContent = `Amazon live (${am.length})`;
    wrapper.appendChild(amHeader);
    if(am.length === 0){
      const p = document.createElement("div"); p.style.color="#ccc"; p.textContent = "No live amazon results.";
      wrapper.appendChild(p);
    } else {
      am.slice(0,20).forEach(i => {
        const el = document.createElement("div");
        el.innerHTML = `<a href="${escapeHtml(i.link||'#')}" target="_blank">${escapeHtml(i.name||'—')}</a> — ${escapeHtml(String(i.price||'N/A'))}`;
        wrapper.appendChild(el);
      });
    }

    out.appendChild(wrapper);
    msg.textContent = `DB: ${db.length} | Amazon: ${am.length}`;
  }

  btn.addEventListener("click", async () => {
    const q = (input.value || "").trim();
    if(!q){ out.innerText = "Enter a search term."; return; }

    btn.disabled = true;
    out.innerHTML = "";
    msg.textContent = "Searching...";

    try{
      const resp = await fetch(BACKEND, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q })
      });

      if(!resp.ok){
        const text = await resp.text().catch(()=>null);
        msg.textContent = `Server error ${resp.status}: ${text||resp.statusText}`;
        return;
      }

      const data = await resp.json();

      if(Array.isArray(data)){
        renderArray(data);
      } else if(typeof data === "object" && (data.db_recent || data.amazon_live)){
        renderLegacy(data);
      } else {
        // fallback: try to normalize object keys (maybe backend returned { results: [...] })
        if(data && Array.isArray(data.results)) renderArray(data.results);
        else { msg.textContent = "Unexpected server response."; console.warn("Unexpected server response:", data); }
      }

    }catch(err){
      console.error(err);
      msg.textContent = "Network or server error. Check terminal for Flask errors.";
    }finally{
      btn.disabled = false;
    }
  });

  input.addEventListener("keypress", (e) => { if(e.key === "Enter") btn.click(); });
});
