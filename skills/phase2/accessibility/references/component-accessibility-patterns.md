# Accessible component patterns

Copy-ready HTML and ARIA patterns for the most common accessible components. Each pattern covers the markup only — styling is separate.

---

## 1. Form with error handling

```html
<form novalidate>
  <!-- Text input with label and error -->
  <div class="field">
    <label for="device-name">Device name</label>
    <input
      id="device-name"
      name="device-name"
      type="text"
      required
      aria-required="true"
      aria-describedby="device-name-error"
      aria-invalid="true"
    />
    <span id="device-name-error" role="alert">
      Device name is required.
    </span>
  </div>

  <!-- Select with label -->
  <div class="field">
    <label for="device-type">Device type</label>
    <select id="device-type" name="device-type" required aria-required="true">
      <option value="">Select a type</option>
      <option value="sensor">Sensor</option>
      <option value="gateway">Gateway</option>
    </select>
  </div>

  <!-- Error summary (shown on submit with errors) -->
  <div
    id="error-summary"
    role="alert"
    aria-labelledby="error-summary-title"
    tabindex="-1"
  >
    <h2 id="error-summary-title">There are 2 errors</h2>
    <ul>
      <li><a href="#device-name">Device name is required</a></li>
      <li><a href="#device-type">Device type must be selected</a></li>
    </ul>
  </div>

  <button type="submit">Save device</button>
</form>
```

On submit error: `document.getElementById('error-summary').focus()` — moves focus to the summary so screen reader announces the errors. Each error links back to its field.

`aria-invalid="true"` is set on the field when it has an error. Remove (or set to `"false"`) on successful input.

`role="alert"` on the error message causes it to be announced immediately by screen readers when it appears.

---

## 2. Modal with focus trap

```html
<!-- Trigger -->
<button id="open-modal" type="button">Add device</button>

<!-- Modal (hidden by default with hidden attribute or display:none) -->
<div
  id="add-device-modal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  tabindex="-1"
>
  <h2 id="modal-title">Add device</h2>

  <form>
    <label for="modal-device-name">Device name</label>
    <input id="modal-device-name" type="text" />

    <div class="modal-actions">
      <button type="submit">Add</button>
      <button type="button" id="close-modal">Cancel</button>
    </div>
  </form>
</div>

<!-- Background content: apply inert attribute when modal is open -->
<main id="page-content"><!-- page content here --></main>
```

```javascript
const modal = document.getElementById('add-device-modal');
const openBtn = document.getElementById('open-modal');
const closeBtn = document.getElementById('close-modal');
const pageContent = document.getElementById('page-content');

// Focusable elements inside the modal
const focusableSelectors = 'button, input, select, textarea, [href], [tabindex]:not([tabindex="-1"])';

function openModal() {
  modal.removeAttribute('hidden');
  pageContent.setAttribute('inert', ''); // prevents Tab from reaching background
  modal.focus(); // focus the dialog container
}

function closeModal() {
  modal.setAttribute('hidden', '');
  pageContent.removeAttribute('inert');
  openBtn.focus(); // return focus to the trigger
}

// Focus trap
modal.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
    return;
  }
  if (e.key !== 'Tab') return;

  const focusable = [...modal.querySelectorAll(focusableSelectors)];
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
});

openBtn.addEventListener('click', openModal);
closeBtn.addEventListener('click', closeModal);
```

The `inert` attribute (supported in all modern browsers) prevents keyboard interaction with background content without needing `aria-hidden` on every background element.

---

## 3. Custom dropdown (combobox)

Use the native `<select>` element wherever possible. Build a custom dropdown only when the design requires it.

```html
<div class="combobox-container">
  <label id="env-label" for="env-input">Environment</label>

  <div role="combobox" aria-expanded="false" aria-haspopup="listbox" aria-owns="env-list">
    <input
      id="env-input"
      type="text"
      autocomplete="off"
      aria-autocomplete="list"
      aria-controls="env-list"
      aria-labelledby="env-label"
    />
  </div>

  <ul
    id="env-list"
    role="listbox"
    aria-label="Environments"
    hidden
  >
    <li role="option" id="opt-prod" aria-selected="false">Production</li>
    <li role="option" id="opt-staging" aria-selected="false">Staging</li>
    <li role="option" id="opt-dev" aria-selected="false">Development</li>
  </ul>
</div>
```

Keyboard behavior required by ARIA Authoring Practices:
- Down Arrow: opens list, moves to next option
- Up Arrow: moves to previous option
- Enter: selects focused option, closes list
- Escape: closes list, returns focus to input
- Home / End: move to first / last option

Set `aria-expanded="true"` on the combobox div when the list opens. Set `aria-selected="true"` on the selected option.

For full implementation, reference the ARIA APG combobox pattern: https://www.w3.org/WAI/ARIA/apg/patterns/combobox/

---

## 4. Data table with sortable columns

```html
<table>
  <caption>Device fleet — 142 devices</caption>
  <thead>
    <tr>
      <th scope="col">
        <button
          type="button"
          aria-sort="none"
          data-col="name"
        >
          Device name
          <span aria-hidden="true">↕</span>
        </button>
      </th>
      <th scope="col">
        <button
          type="button"
          aria-sort="ascending"
          data-col="status"
        >
          Status
          <span aria-hidden="true">↑</span>
        </button>
      </th>
      <th scope="col">Last seen</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>edge-gw-001</td>
      <td>
        <!-- Status uses icon + text, not color alone -->
        <span aria-hidden="true">●</span>
        <span>Online</span>
      </td>
      <td>2026-04-20 14:32</td>
    </tr>
  </tbody>
</table>
```

`aria-sort` values: `"none"` (sortable, not sorted), `"ascending"`, `"descending"`. Only one column may have ascending or descending at a time. Others reset to `"none"`.

The sort icon `<span aria-hidden="true">` hides it from screen readers — the `aria-sort` attribute communicates sort state programmatically.

Status uses both an icon and text label — not color alone. The dot icon is `aria-hidden` since the text "Online" conveys the same information.

---

## 5. Icon button

```html
<!-- Bad: no accessible name -->
<button type="button">
  <svg><!-- filter icon --></svg>
</button>

<!-- Good: aria-label provides the accessible name -->
<button type="button" aria-label="Filter devices">
  <svg aria-hidden="true" focusable="false"><!-- filter icon --></svg>
</button>

<!-- Good: visually hidden text (preferred when tooltip exists) -->
<button type="button">
  <svg aria-hidden="true" focusable="false"><!-- filter icon --></svg>
  <span class="sr-only">Filter devices</span>
</button>
```

`focusable="false"` on the SVG prevents IE/Edge from adding SVG elements to the tab order.

`class="sr-only"` (screen-reader only) is a utility class: `position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap;`. Do not use `display: none` or `visibility: hidden` — those hide content from screen readers too.

Prefer visually hidden text over `aria-label` when a tooltip is provided — the tooltip text and the accessible name stay in sync automatically.

---

## 6. Skip link

First focusable element on every page. Visible only on focus (acceptable), or always visible.

```html
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- ...navigation and header... -->

<main id="main-content" tabindex="-1">
  <!-- page content -->
</main>
```

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: 0;
  z-index: 9999;
  padding: 8px 16px;
  background: #000;
  color: #fff;
}
.skip-link:focus {
  top: 0;
}
```

`tabindex="-1"` on `<main>` allows programmatic focus (from the skip link) without adding it to the natural tab order. Without this, some browsers do not scroll to `<main>` when the skip link is activated.
