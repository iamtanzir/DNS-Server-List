// ==UserScript==
// @name         ShortsGuard — block Reels & Shorts, keep the apps
// @namespace    https://github.com/iamtanzir/DNS-Server-List
// @version      1.0.0
// @description  Hides YouTube Shorts, Facebook Reels and Instagram Reels while keeping feeds, DMs and Messenger working. No tracking, no network calls.
// @author       iamtanzir
// @license      MIT
// @homepageURL  https://github.com/iamtanzir/DNS-Server-List
// @supportURL   https://github.com/iamtanzir/DNS-Server-List/issues
// @match        https://www.youtube.com/*
// @match        https://m.youtube.com/*
// @match        https://www.facebook.com/*
// @match        https://web.facebook.com/*
// @match        https://m.facebook.com/*
// @match        https://www.instagram.com/*
// @run-at       document-start
// @grant        GM_registerMenuCommand
// ==/UserScript==

/*
 * ShortsGuard — the client-side half of the DNS-Server-List "no Reels, no Shorts" setup.
 *
 * Why a userscript? DNS can only block whole domains. /shorts/<id>, /reel/<id> and
 * /reels/<id> are paths on the same domains as the normal feed, so no resolver can
 * block them without blocking Facebook / Instagram / YouTube entirely. This script
 * hides those surfaces inside the page and rewrites their URLs, while leaving
 * /messages, messenger.com, /direct/, the feed and every media CDN untouched.
 */

(() => {
  "use strict";

  const KEY = "shortsguard.settings.v1";
  const DEFAULTS = Object.freeze({
    enabled: true,
    youtube: true,
    facebook: true,
    instagram: true,
    redirect: true,
    toast: true,
  });

  const host = location.hostname;
  const site = /(^|\.)youtube\.com$/.test(host)
    ? "youtube"
    : /(^|\.)facebook\.com$/.test(host)
      ? "facebook"
      : /(^|\.)instagram\.com$/.test(host)
        ? "instagram"
        : null;

  if (!site) return;

  // messenger.com is deliberately not matched. Paths that must never be touched:
  const SAFE_PATHS = /\/(messages|messenger|direct|login|checkpoint|recover|privacy|help|policies)(\/|$)/i;

  const SELECTORS = {
    youtube: [
      "ytd-reel-shelf-renderer",
      "ytm-reel-shelf-renderer",
      "ytd-rich-shelf-renderer[is-shorts]",
      "ytd-rich-section-renderer:has(ytd-rich-shelf-renderer[is-shorts])",
      "ytd-reel-video-renderer",
      "ytd-shorts",
      "ytm-shorts-lockup-view-model",
      'ytd-guide-entry-renderer:has(a[title="Shorts"])',
      'ytd-mini-guide-entry-renderer[aria-label="Shorts"]',
      'yt-tab-shape[tab-title="Shorts"]',
      'yt-chip-cloud-chip-renderer:has(yt-formatted-string[title="Shorts"])',
      'ytd-video-renderer:has(a#thumbnail[href^="/shorts/"])',
      'ytd-grid-video-renderer:has(a#thumbnail[href^="/shorts/"])',
      'yt-lockup-view-model:has(a[href^="/shorts/"])',
      'grid-shelf-view-model:has(a[href^="/shorts/"])',
      'ytd-comment-thread-renderer:has(a[href^="/shorts/"])',
    ],
    facebook: [
      'a[href*="/reel/"]',
      'a[href*="/reels/"]',
      'a[href*="sk=reels_tab"]',
      'div[aria-label="Reels"]',
      'div[aria-label="Reels and short videos"]',
      'div[data-pagelet^="Reels"]',
      'div[data-pagelet*="Reel"]',
      'div[role="navigation"] a[href*="/reel/"]',
      'div[role="feed"] div:has(> div a[href*="/reel/"])',
    ],
    instagram: [
      'a[href="/reels/"]',
      'a[href^="/reels/"]',
      'a[href*="/reel/"]',
      'a:has(svg[aria-label="Reels"])',
      'div[aria-label="Reels"]',
      'div[role="tablist"] a[href="/reels/"]',
      'article:has(a[href*="/reel/"])',
    ],
  };

  const stats = { redirected: 0, appliedAt: null };
  let settings = { ...DEFAULTS };
  let styleEl = null;
  let redirecting = false;
  let toastShown = false;

  /* ------------------------------------------------------------------ */
  /* storage: chrome.storage in the extension, localStorage in a userscript */
  /* ------------------------------------------------------------------ */
  const extStorage = (() => {
    try {
      return typeof chrome !== "undefined" && chrome.storage && chrome.storage.local ? chrome.storage.local : null;
    } catch {
      return null;
    }
  })();

  async function loadSettings() {
    try {
      if (extStorage) {
        const got = await extStorage.get(KEY);
        settings = { ...DEFAULTS, ...(got && got[KEY] ? got[KEY] : {}) };
      } else {
        settings = { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
      }
    } catch {
      settings = { ...DEFAULTS };
    }
  }

  function saveSettings() {
    try {
      if (extStorage) extStorage.set({ [KEY]: settings });
      else localStorage.setItem(KEY, JSON.stringify(settings));
    } catch {
      /* private mode / blocked storage — keep the in-memory settings */
    }
  }

  /* ------------------------------------------------------------------ */
  /* CSS hiding                                                          */
  /* ------------------------------------------------------------------ */
  function applyCss() {
    const active = settings.enabled && settings[site];
    if (!active) {
      if (styleEl) {
        styleEl.remove();
        styleEl = null;
      }
      return;
    }
    if (styleEl && styleEl.isConnected) return;

    styleEl = document.createElement("style");
    styleEl.id = "shortsguard-style";
    styleEl.textContent =
      SELECTORS[site].join(",\n") +
      "{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important}";
    (document.head || document.documentElement).appendChild(styleEl);
  }

  /* ------------------------------------------------------------------ */
  /* URL redirects                                                       */
  /* ------------------------------------------------------------------ */
  function redirectTarget() {
    const path = location.pathname;

    if (site === "youtube") {
      const m = path.match(/^\/shorts\/([A-Za-z0-9_-]{6,})/);
      if (m) return `/watch?v=${m[1]}`;
      return null;
    }

    if (site === "facebook" && /^\/(reel|reels)(\/|$)/i.test(path)) return "/";
    if (site === "instagram" && /^\/(reel|reels)(\/|$)/i.test(path)) return "/";
    return null;
  }

  function enforceRedirect() {
    if (!settings.enabled || !settings[site] || !settings.redirect) return;
    if (redirecting) return;
    if (SAFE_PATHS.test(location.pathname)) return;

    const target = redirectTarget();
    if (!target) return;

    redirecting = true;
    stats.redirected += 1;
    try {
      location.replace(target);
    } catch {
      redirecting = false;
    }
  }

  /* ------------------------------------------------------------------ */
  /* toast                                                               */
  /* ------------------------------------------------------------------ */
  function showToast() {
    if (!settings.toast || toastShown) return;
    toastShown = true;

    const box = document.createElement("div");
    box.id = "shortsguard-toast";
    box.textContent = "🛡️ ShortsGuard: Reels & Shorts hidden — chats and feeds still work.";
    box.style.cssText = [
      "position:fixed",
      "left:16px",
      "bottom:16px",
      "z-index:2147483647",
      "max-width:320px",
      "padding:10px 14px",
      "border-radius:10px",
      "background:#161b22",
      "color:#e6edf3",
      "border:1px solid #3fb950",
      "font:600 13px/1.4 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif",
      "box-shadow:0 8px 24px rgba(0,0,0,.4)",
      "cursor:pointer",
      "opacity:1",
      "transition:opacity .3s",
    ].join(";");
    box.title = "Click to dismiss";
    box.addEventListener("click", () => box.remove());
    (document.body || document.documentElement).appendChild(box);
    setTimeout(() => {
      box.style.opacity = "0";
      setTimeout(() => box.remove(), 350);
    }, 4500);
  }

  /* ------------------------------------------------------------------ */
  /* SPA navigation hooks                                                */
  /* ------------------------------------------------------------------ */
  function tick() {
    applyCss();
    enforceRedirect();
    if (settings.enabled && settings[site]) showToast();
  }

  function watchNavigation() {
    // YouTube fires this on every in-app navigation.
    window.addEventListener("yt-navigate-finish", tick);
    window.addEventListener("yt-page-data-updated", tick);
    // Facebook / Instagram use the History API.
    for (const method of ["pushState", "replaceState"]) {
      const original = history[method];
      history[method] = function patched(...args) {
        const result = original.apply(this, args);
        queueMicrotask(tick);
        return result;
      };
    }
    window.addEventListener("popstate", tick);
  }

  function startObserver() {
    const observer = new MutationObserver(() => {
      // Cheap: only re-checks the two idempotent operations above.
      applyCss();
      enforceRedirect();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  /* ------------------------------------------------------------------ */
  /* public handle + menu commands                                       */
  /* ------------------------------------------------------------------ */
  function expose() {
    const api = {
      get settings() {
        return { ...settings };
      },
      get stats() {
        return { ...stats, hidden: styleEl ? styleEl.isConnected : false };
      },
      set(patch) {
        settings = { ...settings, ...patch };
        saveSettings();
        if (!settings.enabled || !settings[site]) {
          if (styleEl) styleEl.remove();
          styleEl = null;
        }
        applyCss();
        enforceRedirect();
        return { ...settings };
      },
    };
    try {
      window.ShortsGuard = api;
    } catch {
      /* sandboxed page */
    }

    if (typeof GM_registerMenuCommand === "function") {
      GM_registerMenuCommand("ShortsGuard: on/off", () => api.set({ enabled: !settings.enabled }));
      GM_registerMenuCommand("ShortsGuard: redirect /shorts & /reels", () =>
        api.set({ redirect: !settings.redirect }),
      );
      GM_registerMenuCommand("ShortsGuard: status", () =>
        alert(
          `ShortsGuard ${settings.enabled ? "ON" : "OFF"}\n` +
            `YouTube: ${settings.youtube} · Facebook: ${settings.facebook} · Instagram: ${settings.instagram}\n` +
            `Redirects: ${settings.redirect}\n` +
            `Redirected this session: ${stats.redirected}`,
        ),
      );
    }

    if (extStorage && chrome.storage.onChanged) {
      chrome.storage.onChanged.addListener((changes, area) => {
        if (area !== "local" || !changes[KEY]) return;
        settings = { ...DEFAULTS, ...(changes[KEY].newValue || {}) };
        if (!settings.enabled || !settings[site]) {
          if (styleEl) styleEl.remove();
          styleEl = null;
        }
        applyCss();
        enforceRedirect();
      });
    }
  }

  /* ------------------------------------------------------------------ */
  /* boot                                                                */
  /* ------------------------------------------------------------------ */
  async function boot() {
    await loadSettings();
    stats.appliedAt = new Date().toISOString();
    applyCss();
    enforceRedirect();
    watchNavigation();
    startObserver();
    expose();
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", tick, { once: true });
    } else {
      tick();
    }
  }

  boot();
})();
