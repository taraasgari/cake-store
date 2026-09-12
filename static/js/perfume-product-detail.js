(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const mainImage = $('[data-pd-main-image]');
  const price = $('[data-pd-price]');
  const variantInput = $('[data-pd-variant-input]');
  const selectedVariant = $('[data-pd-selected-variant]');
  const qty = $('[data-pd-qty-input]');
  const form = $('[data-pd-buy-form]');
  const cartButton = $('[data-pd-cart-button]');

  function setImage(src) {
    if (!mainImage || !src) return;
    mainImage.classList.add('changing');
    window.setTimeout(() => {
      mainImage.src = src;
      mainImage.classList.remove('changing');
    }, 100);
  }

  $$('[data-pd-thumb]').forEach((button) => {
    button.addEventListener('click', () => {
      $$('[data-pd-thumb]').forEach((item) => item.classList.remove('active'));
      button.classList.add('active');
      setImage(button.dataset.image);
    });
  });

  const variants = $$('[data-pd-variant]');
  variants.forEach((button) => {
    button.addEventListener('click', () => {
      variants.forEach((item) => item.classList.remove('active'));
      button.classList.add('active');
      if (variantInput) variantInput.value = button.dataset.id || '';
      if (selectedVariant) selectedVariant.textContent = button.querySelector('strong')?.textContent?.trim() || 'انتخاب شد';
      if (price && button.dataset.price) price.textContent = Number(button.dataset.price).toLocaleString('fa-IR');
      if (qty) {
        const stock = Math.max(1, Number(button.dataset.stock || 1));
        qty.max = String(stock);
        qty.value = String(Math.min(Math.max(1, Number(qty.value || 1)), stock));
      }
      setImage(button.dataset.image);
    });
  });

  $('[data-pd-minus]')?.addEventListener('click', () => {
    if (!qty) return;
    qty.value = String(Math.max(1, Number(qty.value || 1) - 1));
  });
  $('[data-pd-plus]')?.addEventListener('click', () => {
    if (!qty) return;
    const max = Number(qty.max || 999);
    qty.value = String(Math.min(max, Number(qty.value || 1) + 1));
  });

  form?.addEventListener('submit', (event) => {
    if (variants.length && !variantInput?.value) {
      event.preventDefault();
      selectedVariant?.classList.add('error');
      if (selectedVariant) selectedVariant.textContent = 'لطفاً یک تنوع را انتخاب کنید';
      variants[0]?.focus();
    }
  });

  if (variants.length === 1) variants[0].click();
  if (cartButton?.disabled && qty) qty.disabled = true;

  $('[data-pd-share]')?.addEventListener('click', async () => {
    try {
      if (navigator.share) await navigator.share({title: document.title, url: location.href});
      else {
        await navigator.clipboard.writeText(location.href);
        const btn = $('[data-pd-share]');
        if (btn) {
          const old = btn.innerHTML;
          btn.innerHTML = '<i class="fa-solid fa-check"></i> لینک کپی شد';
          window.setTimeout(() => { btn.innerHTML = old; }, 1600);
        }
      }
    } catch (_) {}
  });
})();
