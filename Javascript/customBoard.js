import { escapeHTML } from './core_utils.js';

/**
 * Fetch and display the alliance custom board image and text.
 *
 * @param {object} options
 * @param {string} [options.endpoint] API endpoint returning image_url and custom_text
 * @param {string} [options.imageSelector] CSS selector for the image container
 * @param {string} [options.textSelector] CSS selector for the text container
 * @param {string} [options.altText] Alt text for the inserted image
 * @param {function} [options.fetchFn] Custom fetch function for authenticated requests
 */
export async function loadCustomBoard({
  endpoint = '/api/alliance-vault/custom-board',
  imageSelector = '#custom-image-slot',
  textSelector = '#custom-text-slot',
  altText = 'Custom Banner',
  fetchFn = fetch
} = {}) {
  const imgSlot = document.querySelector(imageSelector);
  const textSlot = document.querySelector(textSelector);
  if (!imgSlot || !textSlot) return;

  try {
    const res = await fetchFn(endpoint);
    const data = await res.json();

    imgSlot.innerHTML = data.image_url
      ? `<img src="${escapeHTML(data.image_url)}" alt="${escapeHTML(altText)}">`
      : '<p>No custom image set.</p>';

    textSlot.innerHTML = data.custom_text
      ? `<p>${escapeHTML(data.custom_text)}</p>`
      : '<p>No custom text set.</p>';
  } catch (err) {
    console.error('❌ Error loading custom board:', err);
    imgSlot.innerHTML = '<p>Error loading image.</p>';
    textSlot.innerHTML = '<p>Error loading text.</p>';
  }
}
