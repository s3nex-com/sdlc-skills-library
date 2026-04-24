---
name: accessibility
description: >
  accessibility, a11y, WCAG, screen reader, keyboard navigation, color contrast,
  inclusive design, EU Accessibility Act, ADA compliance, focus management,
  aria labels, accessible components, ARIA, tab order, focus trap, skip link,
  axe-core, pa11y, contrast ratio, accessible forms, landmark regions
---

## Purpose

WCAG 2.2 compliance is legally required in growing markets: the EU Accessibility Act came into force June 2025 for private-sector products, and ADA Title III covers US public-facing web services. Accessibility failures are not edge cases — they are defects that block a real user segment and create legal exposure. This skill makes accessibility a first-class engineering concern, not a final-sprint audit. It maps WCAG 2.2 AA requirements directly to the dev tasks that produce them, provides a 15-minute PR checklist, and defines the CI automation that catches regressions before they ship.

---

## When to use

- Any user-facing web feature (new page, new component, new form, modal, navigation change)
- Any user-facing mobile feature (apply platform guidelines: iOS HIG, Android accessibility)
- Pre-PR: dev checklist (15 minutes, every PR that touches UI)
- Sprint planning: when a third-party component is being adopted (verify it is accessible before committing)
- Audit: a dedicated accessibility pass on an existing feature surface

---

## When NOT to use

- **Internal-only tools with no external users** — skip unless a team member has accessibility needs. If they do, apply the same checklist.
- **Mobile-native accessibility (iOS/Android)** — platform-specific tooling (XCTest accessibility API, TalkBack testing, SwiftUI AccessibilityElement) is beyond this skill's scope. Use platform guidelines directly.
- **APIs and backend services** — no UI, not applicable.
- **Visual design review** — color palette decisions and design system choices belong in design review, not here. This skill handles implementation correctness, not design intent.

---

## Process

### When accessibility applies

| Surface | External users? | Apply this skill? |
|---------|----------------|-------------------|
| Web app | Yes | Always |
| Mobile app | Yes | Yes — use platform guidelines |
| Internal tool | Team only | Only if team member has accessibility needs |
| API / backend | None | Not applicable |

### WCAG 2.2 AA mapped to dev tasks

Focus on the criteria that devs actually produce. Ignore the full 78-criterion spec here — those are for formal audits.

**Forms**
- Every input has a `<label>` that references it by `for`/`id`. Placeholder text does not substitute for a label.
- Error messages are linked to the input via `aria-describedby`. The error must be programmatically associated, not just visually adjacent.
- Required fields are marked programmatically: `required` attribute or `aria-required="true"`. An asterisk alone is not sufficient.
- On form submission error: move focus to the error summary or the first errored field.

**Interactive elements**
- Every button and link has a visible text label, or `aria-label` for icon-only controls.
- Custom interactive components (dropdowns, tabs, accordions, date pickers) implement the correct ARIA role from the ARIA Authoring Practices Guide.
- Every interactive element is reachable and operable by keyboard: Tab to reach, Enter or Space to activate, Arrow keys for within-component navigation (menus, tabs).
- No keyboard traps: pressing Tab or Escape must always allow the user to leave any component.

**Modals and overlays**
- When a modal opens: focus moves into the modal (first focusable element or the dialog itself).
- Focus is trapped inside the modal while it is open — Tab cycles through modal controls only.
- When modal closes: focus returns to the element that triggered it.
- Modal markup: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to the modal title.

**Visual**
- Normal text (under 18px or 14px bold): minimum 4.5:1 contrast ratio against background.
- Large text (18px+ or 14px+ bold): minimum 3:1 contrast ratio.
- Interactive element boundaries: 3:1 contrast against adjacent background.
- Do not rely on color alone to convey information. Add text, icon, or pattern as a second channel.
- Content does not break or disappear when zoomed to 200%.

**Navigation and page structure**
- Page has landmark regions: `<main>`, `<nav>`, `<header>`, `<footer>`. One `<h1>` per page.
- Skip link: first focusable element on every page is "Skip to main content", linking to `<main>`. Hidden until focused is fine.
- In SPAs: page `<title>` must update on route change. A screen reader user's primary orientation mechanism is the page title.

### Dev checklist — 15 minutes, before every PR that touches UI

1. Tab through the entire feature without a mouse. Can you reach every interactive element? Can you activate every button and link? Can you complete every form?
2. Check every form field has a visible label — not just placeholder text.
3. Check every button and icon control has a text label or `aria-label`.
4. Open any modals. Does focus move into the modal? Does Tab stay inside it? Does Escape close it and return focus to the trigger?
5. Run the axe-core browser extension on the feature. Fix every Critical and Serious violation before the PR merges.
6. Grayscale check: Chrome DevTools → Rendering → Emulate vision deficiency: Achromatopsia. Does the feature still work — no information lost, no controls ambiguous?

If any step fails, fix before merging. Do not defer accessibility fixes to a "hardening sprint".

### Automated testing in CI

Add `axe-core` via Playwright or Cypress to the CI pipeline. Fail on Critical violations. Serious violations must be triaged within one sprint.

```javascript
// Playwright + axe-core example
import { checkA11y } from 'axe-playwright';

test('device dashboard has no critical a11y violations', async ({ page }) => {
  await page.goto('/dashboard');
  await checkA11y(page, null, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag22aa'] },
    violationCategories: ['critical', 'serious'],
  });
});
```

Automated testing catches approximately 40% of WCAG issues. The manual checklist above catches the rest. Do not claim WCAG compliance based on automated testing alone.

### Legal exposure — know your market

| Market | Law | Applies to |
|--------|-----|-----------|
| EU | EU Accessibility Act (Jun 2025) | Private-sector products and services |
| US | ADA Title III | Web services open to the public |
| EU public sector | EN 301 549 | Government and public-sector sites |
| UK | Equality Act 2010 | Services open to the public |

Target level: WCAG 2.2 AA. AAA is aspirational and often impractical for commercial products. Targeting AA satisfies all four legal frameworks above.

---

## Output format

Produce an accessibility review note for every feature that goes through a dedicated a11y pass. For routine PRs, the checklist result is sufficient.

```
Accessibility review — Device Dashboard feature
Date: 2026-04-20

Automated (axe-core via Playwright, CI run): 0 Critical, 1 Serious
  → Fixed: missing aria-label on filter icon button (WCAG 4.1.2)

Keyboard: PASS
  All controls reachable via Tab. Modal (Add Device) traps focus correctly.
  Escape closes modal and returns focus to trigger button.

Contrast: PASS
  All body text ≥ 4.5:1 (verified with Chrome DevTools color picker).
  Interactive element borders ≥ 3:1.

Forms: PASS
  All inputs have <label> elements. Error messages linked via aria-describedby.
  Required fields marked with aria-required="true".

Color-only: PASS (grayscale check passed — status badges use icon + color)

Known limitation:
  Third-party date picker component (react-datepicker v4.8) has ARIA issues
  on the calendar grid navigation — arrow keys do not work correctly.
  → Workaround: user can type date directly in the input (keyboard accessible)
  → Filed upstream: github.com/Hacker0x01/react-datepicker/issues/XXXX
  → Documented in ADR-018: date picker selection

Overall: AA conformance for this feature except noted date picker limitation.
```

---

## Skill execution log

Append one line to `docs/skill-log.md` each time this skill fires:

```
[YYYY-MM-DD] accessibility | outcome: OK|BLOCKED|PARTIAL | next: <next action> | note: <one-line summary>
```

Examples:
```
[2026-04-20] accessibility | outcome: OK | next: merge PR | note: device dashboard — all checklist items pass, axe clean
[2026-04-20] accessibility | outcome: PARTIAL | next: fix date picker in sprint 15 | note: 1 serious violation deferred — third-party component; workaround documented
[2026-04-20] accessibility | outcome: BLOCKED | next: add axe-core to CI pipeline | note: no automated a11y testing in CI; cannot verify regression safety
```

---

## Reference files

`skills/phase2/accessibility/references/wcag-dev-checklist.md` — printable checklist organized by component type (forms, modals, navigation, tables, media). Each item: WCAG criterion reference, what to check, how to check it, automated or manual.

`skills/phase2/accessibility/references/component-accessibility-patterns.md` — code patterns for the most common accessible components: form with error handling, modal with focus trap, custom dropdown, data table with sortable columns, icon button. Actual HTML and ARIA markup.

`skills/phase2/accessibility/references/a11y-testing-guide.md` — how to set up axe-core in Playwright and Cypress, pa11y CLI usage, Chrome DevTools accessibility panel, VoiceOver quick start (macOS), NVDA quick start (Windows).
