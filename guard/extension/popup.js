"use strict";

const KEY = "shortsguard.settings.v1";
const DEFAULTS = {
  enabled: true,
  youtube: true,
  facebook: true,
  instagram: true,
  redirect: true,
  toast: true,
};

async function load() {
  const got = await chrome.storage.local.get(KEY);
  return { ...DEFAULTS, ...(got[KEY] || {}) };
}

async function save(patch) {
  const next = { ...(await load()), ...patch };
  await chrome.storage.local.set({ [KEY]: next });
  return next;
}

function paint(settings) {
  for (const input of document.querySelectorAll("[data-setting]")) {
    input.checked = Boolean(settings[input.dataset.setting]);
  }
  const status = document.getElementById("status");
  const sites = [
    settings.youtube && "YouTube",
    settings.facebook && "Facebook",
    settings.instagram && "Instagram",
  ].filter(Boolean);

  status.innerHTML = !settings.enabled
    ? '<span style="color:#f0a35e">Paused</span> — nothing is hidden.'
    : sites.length
      ? `<span class="state">Active</span> on ${sites.join(", ")}${settings.redirect ? " · URL redirects on" : ""}.`
      : '<span style="color:#f0a35e">On</span>, but every site is unchecked.';
}

for (const input of document.querySelectorAll("[data-setting]")) {
  input.addEventListener("change", async () => {
    paint(await save({ [input.dataset.setting]: input.checked }));
  });
}

load().then(paint).catch(() => {
  document.getElementById("status").textContent = "Storage unavailable — reload the extension.";
});
