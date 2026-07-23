// Inline line-icons uit v71 (currentColor, 24×24). Één bron voor de zijbalk.
// De SVG-strings zijn 1-op-1 overgenomen uit TapParfum_Portal_v71_cloud.html
// zodat de navigatie exact dezelfde iconentaal heeft als het origineel.
const sv = (p) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`

export const ICONS = {
  dashboard: sv('<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>'),
  tappunten: sv('<path d="M12 21s-6.5-5.6-6.5-10.5a6.5 6.5 0 0 1 13 0C18.5 15.4 12 21 12 21Z"/><circle cx="12" cy="10.5" r="2.4"/>'),
  agenda: sv('<rect x="3.5" y="4.5" width="17" height="16" rx="2.5"/><path d="M3.5 9h17M8 2.5v4M16 2.5v4"/><path d="M8.5 13.5l2 2 4-4"/>'),
  inbox: sv('<path d="M3.5 6.5A2 2 0 0 1 5.5 4.5h13a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2Z"/><path d="M3.8 7l8.2 6 8.2-6"/>'),
  calculator: sv('<rect x="5" y="2.5" width="14" height="19" rx="2.2"/><path d="M8 6.5h8"/><path d="M8.5 11h0M12 11h0M15.5 11h0M8.5 14.5h0M12 14.5h0M15.5 14.5h0M8.5 18h3.5"/>'),
  omzet: sv('<path d="M3.5 17.5 9 12l3.5 3.5L20.5 7"/><path d="M15.5 7h5v5"/>'),
  academy: sv('<path d="M12 4 2.5 8.5 12 13l9.5-4.5L12 4Z"/><path d="M6 10.5V15c0 1.4 2.7 2.8 6 2.8s6-1.4 6-2.8v-4.5"/><path d="M21.5 8.5v5"/>'),
  community: sv('<circle cx="9" cy="9" r="3"/><path d="M3.5 19c0-3 2.5-4.6 5.5-4.6S14.5 16 14.5 19"/><path d="M15.5 6.5a3 3 0 0 1 0 5.4M17 14.6c2.3.5 3.5 2 3.5 4.4"/>'),
  bestellen: sv('<path d="M4 6h2l1.5 10.5h9L18.5 8.5H6.2"/><circle cx="9" cy="20" r="1.3"/><circle cx="16" cy="20" r="1.3"/>'),
  geur: sv('<path d="M12 3v3M10 6h4l1 3.5H9L10 6Z"/><rect x="7" y="9.5" width="10" height="11" rx="2.5"/><path d="M9.5 13.5h5"/>'),
  merk: sv('<path d="M12 2.5 15 8.5l6.5 1-4.7 4.6 1.1 6.4L12 17.5 6.1 20.5l1.1-6.4L2.5 9.5 9 8.5 12 2.5Z"/>'),
  proces: sv('<path d="M4 6h16M4 12h16M4 18h10"/>'),
  kennis: sv('<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H18a1 1 0 0 1 1 1v15.5a1 1 0 0 1-1 1H6.5A1.5 1.5 0 0 1 5 19V4.5Z"/><path d="M5 17.5A1.5 1.5 0 0 1 6.5 16H19"/><path d="M9 7.5h6M9 10.5h4"/>'),
  check: sv('<path d="M4.5 12.5 9.5 17.5 19.5 6.5"/>'),
  ster: sv('<path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9 6.8 19.2l1-5.8L3.5 9.2l5.9-.9L12 3Z"/>'),
  bezoek: sv('<path d="M12 21s-6.5-5.6-6.5-10.5a6.5 6.5 0 0 1 13 0C18.5 15.4 12 21 12 21Z"/><path d="M9.5 10.5l1.8 1.8 3.4-3.4"/>'),
  euro: sv('<circle cx="12" cy="12" r="8.5"/><path d="M15 8.5a4 4 0 1 0 0 7M7.5 10.5h5M7.5 13.5h5"/>'),
  refresh: sv('<path d="M20 11a8 8 0 1 0-.6 4"/><path d="M20 4.5V11h-6"/>'),
  search: sv('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>'),
  users: sv('<circle cx="9" cy="9" r="3"/><path d="M3.5 19c0-3 2.5-4.6 5.5-4.6S14.5 16 14.5 19"/><path d="M15.5 6.5a3 3 0 0 1 0 5.4M17 14.6c2.3.5 3.5 2 3.5 4.4"/>'),
  spark: sv('<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>'),
  gift: sv('<rect x="4" y="9.5" width="16" height="4" rx="1.2"/><path d="M6 13.5h12V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19v-5.5Z"/><path d="M12 9.5v11"/><path d="M12 9.5c-2 0-4.5-.7-4.5-2.7C7.5 5.3 8.6 4.5 9.8 4.5c1.7 0 2.2 2 2.2 5Z"/><path d="M12 9.5c2 0 4.5-.7 4.5-2.7 0-1.5-1.1-2.3-2.3-2.3-1.7 0-2.2 2-2.2 5Z"/>'),
  procent: sv('<path d="M5.5 18.5 18.5 5.5"/><circle cx="7.5" cy="7.5" r="2.6"/><circle cx="16.5" cy="16.5" r="2.6"/>'),
  megafoon: sv('<path d="M4 13.5v-3l10-4.5v12L4 13.5Z"/><path d="M14 8.5c2 .6 3.2 1.6 3.2 3s-1.2 2.4-3.2 3"/><path d="M6.5 14v4a1.5 1.5 0 0 0 1.5 1.5h1a1.5 1.5 0 0 0 1.5-1.5v-2.8"/>'),
  vandaag: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4.2" stroke="currentColor" stroke-width="1.8"/><path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M18.5 5.5l-1.7 1.7M7.2 16.8l-1.7 1.7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  trofee: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7 4h10v4a5 5 0 0 1-10 0V4zM7 5H4.5a1 1 0 0 0-1 1c0 2.2 1.6 4 3.7 4.4M17 5h2.5a1 1 0 0 1 1 1c0 2.2-1.6 4-3.7 4.4M12 13v3.5M8.5 20.5h7M12 16.5c-1.4 0-2.5 1-2.8 2.3-.1.4-.2 1.7-.2 1.7h6s-.1-1.3-.2-1.7c-.3-1.3-1.4-2.3-2.8-2.3z" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  vial: sv('<path d="M9.5 3.5h5"/><path d="M10.5 3.5v4L7.5 14a4.8 4.8 0 1 0 9 0l-3-6.5v-4"/><path d="M8.5 15.5h7"/>')
}
