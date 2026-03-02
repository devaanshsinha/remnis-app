const CAPTURE_ENABLED_KEY = "captureEnabled";

const toggle = document.getElementById("captureToggle");
const statusText = document.getElementById("statusText");

function render(enabled) {
  toggle.checked = enabled;
  statusText.textContent = enabled ? "Status: capturing" : "Status: paused";
}

function setCaptureEnabled(enabled) {
  chrome.storage.local.set({ [CAPTURE_ENABLED_KEY]: enabled }, () => {
    render(enabled);
  });
}

chrome.storage.local.get(CAPTURE_ENABLED_KEY, (result) => {
  const enabled = result[CAPTURE_ENABLED_KEY] ?? true;
  render(enabled);
});

toggle.addEventListener("change", () => {
  setCaptureEnabled(toggle.checked);
});
