import test from 'node:test';
import assert from 'node:assert/strict';

// Minimal copies of the modal helpers to avoid pulling in unrelated deps
function openModal(modal) {
  const el = typeof modal === 'string' ? document.getElementById(modal) : modal;
  if (!el) return;
  el.__prevFocus = document.activeElement;
  el.classList.remove('hidden');
  el.removeAttribute('hidden');
  el.setAttribute('aria-hidden', 'false');
  el.removeAttribute('inert');

  const focusable = el.querySelectorAll(
    'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  const trap = e => {
    if (e.key === 'Escape') {
      closeModal(el);
    } else if (e.key === 'Tab' && focusable.length) {
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  };

  const outside = e => {
    if (e.target === el) closeModal(el);
  };

  el.__trapFocus = trap;
  el.__outsideClick = outside;
  el.addEventListener('keydown', trap);
  el.addEventListener('click', outside);
  if (first) first.focus();
}

function closeModal(modal) {
  const el = typeof modal === 'string' ? document.getElementById(modal) : modal;
  if (!el) return;
  if (el.contains(document.activeElement)) {
    document.activeElement.blur();
  }
  el.removeEventListener('keydown', el.__trapFocus);
  el.removeEventListener('click', el.__outsideClick);
  delete el.__trapFocus;
  delete el.__outsideClick;
  el.classList.add('hidden');
  el.setAttribute('hidden', '');
  el.setAttribute('aria-hidden', 'true');
  el.setAttribute('inert', '');
  if (el.__prevFocus && typeof el.__prevFocus.focus === 'function') {
    el.__prevFocus.focus();
  }
  delete el.__prevFocus;
}

class FakeClassList {
  constructor() { this._set = new Set(); }
  add(...cls) { cls.forEach(c => this._set.add(c)); }
  remove(...cls) { cls.forEach(c => this._set.delete(c)); }
  toggle(cls, force) {
    if (force === true) return this._set.add(cls);
    if (force === false) return this._set.delete(cls);
    if (this._set.has(cls)) this._set.delete(cls); else this._set.add(cls);
  }
  contains(cls) { return this._set.has(cls); }
}

class FakeElement {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.classList = new FakeClassList();
    this.attributes = {};
    this.children = [];
    this.dataset = {};
  }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name]; }
  removeAttribute(name) { delete this.attributes[name]; }
  appendChild(child) { this.children.push(child); }
  focus() { document.activeElement = this; }
  blur() { if (document.activeElement === this) document.activeElement = null; }
  querySelectorAll() { return this.children; }
  addEventListener() {}
  removeEventListener() {}
  contains(node) { return this.children.includes(node); }
}

class FakeDocument {
  constructor() {
    this.elements = {};
    this.activeElement = null;
    this.body = new FakeElement('body');
  }
  createElement(tag) { return new FakeElement(tag); }
  getElementById(id) { return this.elements[id] || null; }
}

test('openModal and closeModal toggle attributes and focus', () => {
  const doc = new FakeDocument();
  global.document = doc;

  const trigger = doc.createElement('button');
  doc.activeElement = trigger;

  const modal = doc.createElement('div');
  modal.classList.add('hidden');
  modal.setAttribute('hidden', '');
  modal.setAttribute('aria-hidden', 'true');
  modal.setAttribute('inert', '');

  const yes = doc.createElement('button');
  const no = doc.createElement('button');
  modal.appendChild(yes);
  modal.appendChild(no);

  doc.elements['confirm-modal'] = modal;

  openModal('confirm-modal');

  assert(!modal.classList.contains('hidden'));
  assert.equal(modal.getAttribute('aria-hidden'), 'false');
  assert.strictEqual(modal.getAttribute('inert'), undefined);
  assert.equal(modal.__prevFocus, trigger);
  assert.equal(doc.activeElement, yes);

  closeModal('confirm-modal');

  assert(modal.classList.contains('hidden'));
  assert.equal(modal.getAttribute('aria-hidden'), 'true');
  assert.equal(modal.getAttribute('inert'), '');
  assert.equal(doc.activeElement, trigger);
});
