const form = document.querySelector("#search-form");
const queryInput = document.querySelector("#query");
const limitInput = document.querySelector("#limit");
const aiInput = document.querySelector("#use-ai");
const submitButton = document.querySelector("#submit");
const feedback = document.querySelector("#feedback");
const resultsSection = document.querySelector("#results-section");
const results = document.querySelector("#results");
const parsed = document.querySelector("#parsed");
const resultCount = document.querySelector("#result-count");

const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[character]));
const labelMap = { manufacturer: "برند", material: "جنس", size_inch: "سایز", connection: "اتصال", standard: "استاندارد", pressure_class: "کلاس فشار" };

function renderParsed(values) {
  const keys = ["item_type", "item_subtype", "manufacturer", "material", "material_family", "size_inch", "pressure_class", "connection", "standard"];
  parsed.innerHTML = keys.filter(key => values[key] !== null && values[key] !== undefined && values[key] !== "").map(key => `<span class="chip">${escapeHtml(labelMap[key] || key)}=${escapeHtml(values[key])}</span>`).join("");
}

function renderCard(item) {
  const meta = [item.manufacturer && `برند: ${item.manufacturer}`, item.material && `جنس: ${item.material}`, item.size_inch && `سایز: ${item.size_inch} in`, item.connection && `اتصال: ${item.connection}`, item.standard && `استاندارد: ${item.standard}`].filter(Boolean).map(value => `<span>${escapeHtml(value)}</span>`).join("");
  const differences = item.differences?.length ? `<div class="difference"><strong>تفاوت:</strong>${escapeHtml(item.differences.join("، "))}</div>` : "";
  return `<article class="result-card"><div class="result-head"><div class="mesc-code">${escapeHtml(item.mesc_code)}</div><span class="score">${Math.round(item.score * 100)}%</span></div><p class="description">${escapeHtml(item.description_fa)}</p><p class="description-en">${escapeHtml(item.description_en)}</p><div class="meta">${meta}</div>${differences}</article>`;
}

async function runSearch() {
  const query = queryInput.value.trim();
  if (!query) return;
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "در حال جست‌وجو...";
  feedback.className = "feedback";
  feedback.textContent = "در حال تحلیل درخواست و جست‌وجو در کاتالوگ...";
  try {
    const response = await fetch("/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, limit: Number(limitInput.value), use_ai: aiInput.checked }) });
    const raw = await response.text();
    let data;
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      throw new Error(`پاسخ نامعتبر از سرور (${response.status}): ${raw.slice(0, 180)}`);
    }
    if (!response.ok) throw new Error(data.detail || data.error || "خطا در دریافت پاسخ");
    renderParsed(data.parsed || {});
    results.innerHTML = data.results?.length ? data.results.map(renderCard).join("") : "<p>نتیجه‌ای پیدا نشد. مشخصات را بازتر یا دقیق‌تر بنویس.</p>";
    resultCount.textContent = `${data.results?.length || 0} نتیجه`;
    resultsSection.classList.remove("hidden");
    feedback.textContent = data.ai_error ? `نتیجه با parser داخلی پیدا شد؛ AI در دسترس نبود: ${data.ai_error}` : (data.ai_used ? "درخواست با AI تحلیل شد و سپس با کاتالوگ تطبیق داده شد." : "نتیجه با parser داخلی و کاتالوگ پیدا شد.");
    if (data.ai_error) feedback.classList.add("error");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    feedback.className = "feedback error";
    feedback.textContent = `خطا: ${error.message}`;
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span").textContent = "جست‌وجو";
  }
}

form.addEventListener("submit", event => { event.preventDefault(); runSearch(); });
queryInput.addEventListener("keydown", event => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") runSearch(); });
document.querySelectorAll(".example").forEach(button => button.addEventListener("click", () => { queryInput.value = button.dataset.query; queryInput.focus(); }));
