/**
 * script.js
 * ---------
 * Client-side JavaScript for SmartDataOS
 *
 * Features:
 *   - Live regex validation (mirrors server-side patterns)
 *   - Password strength meter
 *   - Drag-and-drop file upload
 *   - Form submission loading state
 *   - Debounced API validation
 */

// ── Regex patterns (mirror server-side patterns in validation.py) ────────────
const PATTERNS = {
  name:     /^[A-Za-z\s\-']{2,60}$/,
  email:    /^[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}$/,
  phone:    /^\+?[\d\s\-\(\)]{7,15}$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]).{8,}$/,
};

const MESSAGES = {
  name:     "Name must be 2–60 alphabetic characters.",
  email:    "Invalid email address.",
  phone:    "Phone must be 7–15 digits.",
  password: "≥8 chars · uppercase · lowercase · digit · special character.",
};

// ── Live field validation ─────────────────────────────────────────────────────
function validateField(fieldId) {
  const input = document.getElementById(fieldId);
  if (!input) return;
  const hint  = document.getElementById(`${fieldId}-hint`);
  const value = input.value.trim();

  if (!value) {
    input.className = "";
    if (hint) { hint.textContent = ""; hint.className = "field-hint"; }
    return;
  }

  const valid = PATTERNS[fieldId]?.test(value) ?? true;
  input.classList.toggle("input-ok",    valid);
  input.classList.toggle("input-error", !valid);

  if (hint) {
    hint.textContent = valid ? "✓ Looks good" : MESSAGES[fieldId];
    hint.className   = `field-hint ${valid ? "hint-ok" : "hint-error"}`;
  }
}

// Attach listeners once DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  ["name", "email", "phone", "password"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input",  () => validateField(id));
      el.addEventListener("blur",   () => validateField(id));
    }
  });

  // Password strength meter
  const pwInput = document.getElementById("password");
  if (pwInput) {
    pwInput.addEventListener("input", updatePasswordStrength);
  }

  // Drag-and-drop
  setupDropzone();

  // Form submit → loading state
  const form = document.getElementById("mainForm");
  if (form) {
    form.addEventListener("submit", () => {
      const btn    = document.getElementById("submitBtn");
      const text   = btn?.querySelector(".btn-text");
      const loader = document.getElementById("loader");
      if (text)   text.style.display   = "none";
      if (loader) loader.style.display = "inline";
    });
  }
});

// ── Password strength ─────────────────────────────────────────────────────────
function updatePasswordStrength() {
  const val = document.getElementById("password")?.value || "";
  const bar = document.getElementById("pw-bar");
  if (!bar) return;

  let score = 0;
  if (val.length >= 8)              score++;
  if (/[A-Z]/.test(val))            score++;
  if (/[a-z]/.test(val))            score++;
  if (/\d/.test(val))               score++;
  if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(val)) score++;

  const colours = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"];
  bar.style.width      = `${score * 20}%`;
  bar.style.background = colours[score - 1] || "transparent";
}

// ── Toggle password visibility ────────────────────────────────────────────────
function togglePw() {
  const input = document.getElementById("password");
  if (!input) return;
  input.type = input.type === "password" ? "text" : "password";
}

// ── Drag-and-drop dropzone ────────────────────────────────────────────────────
function setupDropzone() {
  const zone = document.getElementById("dropzone");
  if (!zone) return;

  ["dragenter", "dragover"].forEach(ev =>
    zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.add("drag-over"); })
  );
  ["dragleave", "drop"].forEach(ev =>
    zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.remove("drag-over"); })
  );
  zone.addEventListener("drop", e => {
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      const input = document.getElementById("dataset");
      if (input) {
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        handleFileSelect(input);
      }
    }
  });
}

// ── File select feedback ──────────────────────────────────────────────────────
function handleFileSelect(input) {
  const file    = input?.files?.[0];
  const content = document.getElementById("drop-content");
  if (!content) return;

  if (file) {
    const size = (file.size / 1024).toFixed(1);
    content.innerHTML = `
      <div class="drop-icon">✅</div>
      <div class="drop-text">
        <strong>${escapeHtml(file.name)}</strong>
        <br/><span class="drop-sub">${size} KB · ready to upload</span>
      </div>`;
  }
}

// ── Utility ───────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return str.replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}
