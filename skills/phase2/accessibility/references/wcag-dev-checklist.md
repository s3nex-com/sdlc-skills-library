# WCAG 2.2 AA — developer checklist

Organized by component type. Print this and check each item before a PR that touches UI. Criterion references use WCAG 2.2 numbering.

---

## Forms

| # | What to check | How to check | Mode |
|---|--------------|--------------|------|
| F1 | Every `<input>`, `<select>`, `<textarea>` has a `<label>` linked via `for`/`id` — not just placeholder | Inspect element; placeholder text ≠ label | Manual |
| F2 | Error messages are linked to their input via `aria-describedby` | Inspect ARIA attributes when error state is active | Manual |
| F3 | Required fields use `required` attribute or `aria-required="true"` | Inspect; asterisk alone fails 1.3.1 | Manual |
| F4 | On submit with errors: focus moves to error summary or first errored field | Tab through form; submit with errors; watch focus | Manual |
| F5 | Input type matches data: `type="email"`, `type="tel"`, `type="date"` | Inspect; correct type enables mobile keyboard and autocomplete | Manual |
| F6 | No reliance on placeholder as the only label | Remove field value; check label still present | Manual |

WCAG criteria: 1.3.1 (Info and Relationships), 3.3.1 (Error Identification), 3.3.2 (Labels or Instructions)

---

## Buttons and interactive elements

| # | What to check | How to check | Mode |
|---|--------------|--------------|------|
| B1 | Every `<button>` has a text label or `aria-label` | Inspect; icon-only buttons must have aria-label | Manual / axe |
| B2 | Every `<a>` link has descriptive text — not "click here" or "read more" | Read link text out of context; is the destination clear? | Manual |
| B3 | Custom interactive elements have correct ARIA role | Inspect; e.g. custom dropdown → `role="combobox"` | Manual |
| B4 | All interactive elements reachable by Tab | Tab through feature; every control must receive focus | Manual |
| B5 | Buttons activated by Enter or Space; links by Enter | Tab to element; press Enter; press Space | Manual |
| B6 | No keyboard trap | Tab into any component; Escape or continued Tab must exit | Manual |
| B7 | Focus indicator is visible | Tab through feature; blue outline or equivalent must be visible | Manual |

WCAG criteria: 2.1.1 (Keyboard), 2.1.2 (No Keyboard Trap), 2.4.7 (Focus Visible), 4.1.2 (Name, Role, Value)

---

## Modals and overlays

| # | What to check | How to check | Mode |
|---|--------------|--------------|------|
| M1 | Focus moves into modal when it opens | Open modal; check active element is inside it | Manual |
| M2 | Tab cycles only within modal while it is open | Tab repeatedly; focus must not escape to background content | Manual |
| M3 | Escape closes modal | Press Escape; modal must close | Manual |
| M4 | Focus returns to trigger element on close | Close modal; check focus lands on the element that opened it | Manual |
| M5 | Modal has `role="dialog"` and `aria-modal="true"` | Inspect | Manual |
| M6 | Modal has `aria-labelledby` pointing to modal title | Inspect; title `id` must match aria-labelledby value | Manual |
| M7 | Background content is inert while modal is open | Tab should not reach background; use `inert` attribute or aria-hidden | Manual |

WCAG criteria: 2.1.1 (Keyboard), 2.1.2 (No Keyboard Trap), 4.1.2 (Name, Role, Value)

---

## Navigation and page structure

| # | What to check | How to check | Mode |
|---|--------------|--------------|------|
| N1 | Page has exactly one `<h1>` that is the page title | Inspect; `<h1>` must identify the page, not the brand | Manual |
| N2 | Heading hierarchy is logical: h1 → h2 → h3 (no skipped levels) | Run axe-core; or inspect heading structure | Automated |
| N3 | Page has landmark regions: `<main>`, `<nav>`, `<header>`, `<footer>` | Inspect | Manual |
| N4 | Skip link is first focusable element; links to `<main>` | Press Tab on fresh page load; check first focus | Manual |
| N5 | Page `<title>` changes on route change (SPAs) | Navigate in the app; watch browser tab title | Manual |
| N6 | Nav links indicate current page: `aria-current="page"` | Inspect active nav item | Manual |

WCAG criteria: 2.4.1 (Bypass Blocks), 2.4.2 (Page Titled), 1.3.1 (Info and Relationships)

---

## Tables

| # | What to check | How to check | Mode |
|---|--------------|--------------|------|
| T1 | Data tables use `<th>` for headers with `scope="col"` or `scope="row"` | Inspect | Manual |
| T2 | Table has a `<caption>` or `aria-label` describing its purpose | Inspect | Manual |
| T3 | Sortable column headers are buttons with `aria-sort` attribute set | Inspect sort state; axe catches missing aria-sort | Automated |
| T4 | No layout tables (use CSS grid/flex instead) | Inspect for `<table>` used for layout | Manual |

WCAG criteria: 1.3.1 (Info and Relationships)

---

## Visual — contrast and color

| # | What to check | How to check | Mode |
|---|--------------|--------------|------|
| V1 | Normal text (< 18px or < 14px bold): ≥ 4.5:1 contrast | Chrome DevTools color picker; or axe-core | Automated |
| V2 | Large text (≥ 18px or ≥ 14px bold): ≥ 3:1 contrast | Chrome DevTools color picker | Automated |
| V3 | Interactive element boundaries: ≥ 3:1 against background | Inspect; check button borders, input borders | Automated |
| V4 | Information not conveyed by color alone | DevTools → Rendering → Achromatopsia; can you still read the UI? | Manual |
| V5 | Content usable at 200% zoom without horizontal scrolling | Browser zoom to 200%; scroll only vertically | Manual |

WCAG criteria: 1.4.1 (Use of Color), 1.4.3 (Contrast — Minimum), 1.4.4 (Resize Text), 1.4.11 (Non-text Contrast)

---

## Images and media

| # | What to check | How to check | Mode |
|---|--------------|--------------|------|
| I1 | Informative images have descriptive `alt` text | Inspect; alt must convey the meaning, not just filename | Manual |
| I2 | Decorative images have `alt=""` (empty) | Inspect; decorative = no information lost if invisible | Manual |
| I3 | Icon images used as buttons have `aria-label` on the button, not just alt on the icon | Inspect | Manual |
| I4 | Videos have captions (auto-generated captions do not satisfy 1.2.2) | Play video; verify closed captions available and accurate | Manual |
| I5 | Audio-only content has a text transcript | Check for transcript link or inline text | Manual |

WCAG criteria: 1.1.1 (Non-text Content), 1.2.1 (Audio-only and Video-only), 1.2.2 (Captions — Prerecorded)

---

## Automated testing coverage

axe-core in CI catches automatically: missing labels, missing alt text, color contrast, invalid ARIA roles, landmark issues, heading order, duplicate IDs.

axe-core does NOT catch: keyboard traps, focus management in modals, correct focus return on close, skip link functionality, SPA title updates, color-only information.

Manual checklist is required alongside automation.
