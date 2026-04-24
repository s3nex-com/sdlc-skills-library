# Accessibility testing guide

How to use the main a11y testing tools. Each section is self-contained.

---

## axe-core in Playwright

### Install

```bash
npm install --save-dev @axe-core/playwright
```

### Basic test

```javascript
// tests/a11y/dashboard.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('device dashboard accessibility', () => {
  test('no critical or serious violations', async ({ page }) => {
    await page.goto('/dashboard');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
      .analyze();

    // Filter to critical and serious only
    const blocking = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    );

    if (blocking.length > 0) {
      console.log('Violations:', JSON.stringify(blocking, null, 2));
    }

    expect(blocking).toHaveLength(0);
  });

  test('modal is accessible when open', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('button:has-text("Add device")');

    // Test the modal specifically
    const results = await new AxeBuilder({ page })
      .include('#add-device-modal')
      .analyze();

    expect(results.violations).toHaveLength(0);
  });
});
```

### Run in CI

```yaml
# .github/workflows/a11y.yml
- name: Run accessibility tests
  run: npx playwright test tests/a11y/
```

axe-core violation impact levels: critical → serious → moderate → minor. CI fails on critical and serious. Moderate and minor are logged but do not fail the build — triage within the sprint.

---

## axe-core in Cypress

### Install

```bash
npm install --save-dev cypress-axe axe-core
```

```javascript
// cypress/support/e2e.ts
import 'cypress-axe';
```

### Test

```javascript
// cypress/e2e/a11y/dashboard.cy.ts
describe('device dashboard accessibility', () => {
  beforeEach(() => {
    cy.visit('/dashboard');
    cy.injectAxe();
  });

  it('has no critical or serious violations', () => {
    cy.checkA11y(null, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag22aa'] },
      includedImpacts: ['critical', 'serious'],
    });
  });

  it('modal is accessible', () => {
    cy.get('button').contains('Add device').click();
    cy.checkA11y('#add-device-modal', {
      includedImpacts: ['critical', 'serious'],
    });
  });
});
```

---

## pa11y CLI

pa11y is useful for quick command-line audits of a URL — no test framework required.

### Install

```bash
npm install -g pa11y
```

### Basic usage

```bash
# Audit a single URL at WCAG 2.2 AA
pa11y --standard WCAG2AA https://app.example.com/dashboard

# Save report to file
pa11y --standard WCAG2AA --reporter json https://app.example.com/dashboard > pa11y-report.json

# Ignore specific rules (when a known third-party issue is tracked)
pa11y --standard WCAG2AA --ignore "WCAG2AA.Principle4.Guideline4_1.4_1_2.H91.InputText.Name" \
  https://app.example.com/dashboard
```

### Run against authenticated pages

```javascript
// .pa11yci.json — pa11y CI config
{
  "defaults": {
    "standard": "WCAG2AA",
    "timeout": 10000,
    "actions": [
      "navigate to https://app.example.com/login",
      "set field #email to test@example.com",
      "set field #password to testpassword",
      "click element #login-btn",
      "wait for url to be https://app.example.com/dashboard"
    ]
  },
  "urls": [
    "https://app.example.com/dashboard",
    "https://app.example.com/devices",
    "https://app.example.com/settings"
  ]
}
```

```bash
pa11y-ci --config .pa11yci.json
```

---

## Chrome DevTools — accessibility panel

For manual investigation without a screen reader.

1. Open DevTools (F12 or Cmd+Option+I)
2. Elements panel → select any element → check the Accessibility pane (bottom-right)
   - Shows the accessibility tree for the selected element
   - Shows computed accessible name, role, and properties
   - "View full accessibility tree" toggles the full tree view

**Contrast check:**
1. Select a text element in Elements panel
2. Click the color swatch next to `color:` in Styles pane
3. The contrast ratio appears in the color picker. Green check = pass, red cross = fail.

**Vision deficiency simulation:**
1. DevTools → More tools → Rendering
2. "Emulate vision deficiencies" → Achromatopsia (full grayscale)
3. Check that status, alerts, and data visualization still work without color

**Keyboard focus debugging:**
1. DevTools → Sources panel
2. Check "Pause on DOM modifications" to catch focus changes
3. Or: in Console, `document.addEventListener('focusin', (e) => console.log(e.target))`

---

## VoiceOver quick start — macOS

VoiceOver is built into macOS. Use it to verify modal focus management and ARIA live regions.

### Enable / disable
- Toggle on/off: Cmd + F5 (or Control + Option + F5 on some keyboards)
- Or: System Settings → Accessibility → VoiceOver → Enable VoiceOver

### Basic navigation
| Key | Action |
|-----|--------|
| VO + Right Arrow | Move to next item (VO = Control + Option) |
| VO + Left Arrow | Move to previous item |
| VO + Space | Activate (click) the focused item |
| Tab | Move to next interactive element |
| Shift + Tab | Move to previous interactive element |
| VO + U | Open the Rotor (navigate by headings, links, landmarks) |
| VO + H | Navigate to next heading |
| Escape | Close VoiceOver Rotor or stop interaction |

### What to test with VoiceOver
1. Tab through the feature — does VoiceOver announce each element's name and role?
2. Open a modal — does VoiceOver announce the dialog title? Does Tab stay inside?
3. Submit a form with errors — does VoiceOver announce the error summary?
4. Trigger a live region update (notification, toast) — does VoiceOver announce it automatically?

### Quick settings for testing
- VoiceOver Utility (VO + F8) → Speech → reduce speech rate for easier listening
- Turn off verbosity options that add noise during testing: VO + F8 → Verbosity

---

## NVDA quick start — Windows

NVDA (NonVisual Desktop Access) is free and is the most widely used screen reader with Chrome on Windows.

### Download
https://www.nvaccess.org/download/

### Enable / disable
- NVDA + Q: quit NVDA (NVDA key = Insert by default)
- Start menu → NVDA to launch

### Basic navigation
| Key | Action |
|-----|--------|
| Tab | Move to next interactive element |
| Shift + Tab | Move to previous interactive element |
| NVDA + Down Arrow | Read current line |
| NVDA + Space | Activate form mode (to type in fields) |
| H | Move to next heading (browse mode) |
| D | Move to next landmark |
| B | Move to next button |
| F | Move to next form field |
| Escape | Exit form mode / return to browse mode |

### What to test with NVDA (Chrome)
1. Tab to every interactive element — does NVDA announce the name, role, and state?
2. Navigate by headings (H key) — is the page structure logical?
3. Navigate by landmarks (D key) — are main, nav, header, footer announced?
4. Tab into a modal — does NVDA switch to form mode? Does Tab stay inside the modal?
5. Trigger an `aria-live` region — does NVDA announce the update without losing focus?

### Pairing: NVDA + Chrome
NVDA works best with Chrome on Windows for web testing. Firefox also works well. Avoid IE and Edge Legacy.

---

## What automated testing covers vs. what it does not

| Issue type | axe-core / pa11y | Manual required |
|-----------|-----------------|-----------------|
| Missing alt text | Yes | — |
| Missing form labels | Yes | — |
| Color contrast | Yes | — |
| Invalid ARIA roles | Yes | — |
| Duplicate IDs | Yes | — |
| Heading order | Yes | — |
| Keyboard trap | No | Yes |
| Focus moves into modal on open | No | Yes |
| Focus trapped inside modal | No | Yes |
| Focus returns to trigger on close | No | Yes |
| Skip link works | No | Yes |
| SPA title updates on route change | No | Yes |
| Color-only information | No | Yes (grayscale check) |
| Logical reading order | Partial | Yes |
| Custom widget keyboard behavior | No | Yes |

Automated testing reliably catches ~40% of WCAG issues. The other ~60% require the manual checklist and occasional screen reader testing.
