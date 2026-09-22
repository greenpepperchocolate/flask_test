const form = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const dropZone = document.getElementById("drop-zone");
const dropZoneText = document.getElementById("drop-zone-text");
const submitBtn = document.getElementById("submit-btn");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const uploadSection = document.getElementById("upload-section");
const result = document.getElementById("result");
const resetBtn = document.getElementById("reset-btn");
const appTitle = document.getElementById("app-title");

const DROP_ZONE_DEFAULT_HTML =
  "ここにCSVファイルをドラッグ&ドロップ<br>またはクリックしてファイルを選択";

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  if (e.dataTransfer.files.length > 0) {
    fileInput.files = e.dataTransfer.files;
    updateDropZoneText();
  }
});

fileInput.addEventListener("change", updateDropZoneText);

function updateDropZoneText() {
  if (fileInput.files.length > 0) {
    dropZoneText.textContent = fileInput.files[0].name;
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const file = fileInput.files[0];
  if (!file) return;

  errorBox.classList.add("hidden");
  errorBox.textContent = "";
  result.classList.add("hidden");
  loading.classList.remove("hidden");
  submitBtn.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "処理に失敗しました");
    }

    renderResult(data);
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
    submitBtn.disabled = false;
  }
});

function renderResult(data) {
  document.getElementById("res-filename").textContent = data.filename;
  document.getElementById("res-shape").textContent =
    `${data.original_rows} 行 / ${data.original_cols} 列`;
  document.getElementById("res-duplicate").textContent = `${data.duplicate_removed} 件`;
  document.getElementById("res-rows-after").textContent = `${data.rows_after_cleaning} 行`;

  const columnsBody = document.getElementById("columns-body");
  columnsBody.innerHTML = "";
  data.columns_info.forEach((col) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${escapeHtml(col.column)}</td><td>${escapeHtml(col.dtype)}</td><td>${col.missing}</td>`;
    columnsBody.appendChild(tr);
  });

  document.getElementById("describe-container").innerHTML = data.describe_html;
  document.getElementById("preview-container").innerHTML = data.preview_html;

  uploadSection.classList.add("hidden");
  result.classList.remove("hidden");
}

function resetToUpload() {
  form.reset();
  dropZoneText.innerHTML = DROP_ZONE_DEFAULT_HTML;
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
  result.classList.add("hidden");
  uploadSection.classList.remove("hidden");
}

resetBtn.addEventListener("click", resetToUpload);
appTitle.addEventListener("click", resetToUpload);

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
