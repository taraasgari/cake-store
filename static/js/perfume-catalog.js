(() => {
  'use strict';

  const config = document.getElementById('pa-catalog-config');
  if (!config) return;

  const dialog = document.getElementById('pa-catalog-dialog');
  const form = document.getElementById('pa-catalog-form');
  const error = document.getElementById('pa-catalog-error');
  if (!dialog || !form || !error) return;

  let active = null;
  const widgets = [];
  const labels = {
    category: 'دسته‌بندی',
    brand: 'برند',
    product_type: 'نوع محصول',
    tags: 'تگ',
  };

  function actionButton(kind, label, icon, handler) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `pa-catalog-icon pa-catalog-${kind}`;
    button.setAttribute('aria-label', label);
    button.title = label;
    button.innerHTML = `<i class="fa-solid ${icon}" aria-hidden="true"></i><span class="sr-only">${label}</span>`;
    button.addEventListener('click', handler);
    return button;
  }

  function refresh(widget) {
    const {select, picker, list, edit, remove} = widget;

    if (picker) {
      const previous = picker.value;
      picker.replaceChildren(new Option('انتخاب تگ برای مدیریت', ''));
      list.replaceChildren();

      [...select.options].filter(option => option.value).forEach(option => {
        picker.add(new Option(option.textContent.trim(), option.value));

        const label = document.createElement('label');
        label.className = 'pa-tag-choice';
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = option.selected;
        input.addEventListener('change', () => {
          option.selected = input.checked;
          select.dispatchEvent(new Event('change'));
        });
        label.append(input, document.createTextNode(option.textContent.trim()));
        list.append(label);
      });

      picker.value = previous;
    }

    const selected = (picker || select).value;
    if (edit) edit.disabled = !selected;
    if (remove) remove.disabled = !selected;
  }

  function open(widget, action) {
    const id = (widget.picker || widget.select).value;
    const option = [...widget.select.options].find(item => item.value === id);
    if (action !== 'add' && !option) return;

    active = {widget, action, id};
    form.reset();
    error.textContent = '';

    document.getElementById('pa-catalog-title').textContent =
      ({add: 'افزودن ', edit: 'ویرایش ', delete: 'حذف '})[action] + labels[widget.select.name];

    const deleting = action === 'delete';
    document.getElementById('pa-catalog-fields').hidden = deleting;
    document.getElementById('pa-catalog-delete-message').hidden = !deleting;
    form.elements.name.required = !deleting;
    form.elements.name.value = action === 'add' ? '' : option.textContent.trim();
    form.elements.slug.value = action === 'add' ? '' : option.dataset.slug || '';
    form.elements.slug.maxLength = widget.select.name === 'tags' ? 50 : 100;
    form.elements.name.maxLength = widget.select.name === 'tags' ? 50 : 100;

    const parent = form.elements.parent_id;
    document.getElementById('pa-catalog-parent').hidden = widget.select.name !== 'category';
    parent.replaceChildren(new Option('بدون والد', ''));

    if (widget.select.name === 'category') {
      [...widget.select.options]
        .filter(item => item.value && (action === 'add' || item.value !== id))
        .forEach(item => parent.add(new Option(item.textContent.trim(), item.value)));
      parent.value = action === 'add' ? '' : option.dataset.parent || '';
    }

    dialog.showModal();
  }

  Object.keys(labels).forEach(name => {
    const select = document.querySelector(`select[name="${name}"]`);
    if (!select) return;

    const widget = {select};
    widgets.push(widget);

    const shell = document.createElement('div');
    shell.className = select.multiple ? 'pa-catalog-shell pa-catalog-shell-tags' : 'pa-catalog-shell';
    select.parentNode.insertBefore(shell, select);
    shell.append(select);

    const actions = document.createElement('div');
    actions.className = 'pa-catalog-actions';

    if (select.multiple) {
      select.hidden = true;

      const list = document.createElement('div');
      list.className = 'pa-tag-list';
      shell.append(list);
      widget.list = list;

      const picker = document.createElement('select');
      picker.className = 'pa-catalog-picker';
      picker.setAttribute('aria-label', 'تگ برای مدیریت');
      widget.picker = picker;

      if (config.dataset.canManage === 'true') shell.append(picker);
      picker.addEventListener('change', () => refresh(widget));
    }

    if (config.dataset.canManage === 'true') {
      const add = actionButton('add', `افزودن ${labels[name]}`, 'fa-plus', () => open(widget, 'add'));
      widget.edit = actionButton('edit', `ویرایش ${labels[name]} انتخاب‌شده`, 'fa-pen', () => open(widget, 'edit'));
      widget.remove = actionButton('delete', `حذف ${labels[name]} انتخاب‌شده`, 'fa-trash-can', () => open(widget, 'delete'));
      actions.append(add, widget.edit, widget.remove);
      shell.append(actions);
    }

    select.addEventListener('change', () => refresh(widget));
    refresh(widget);
  });

  document.getElementById('pa-catalog-cancel')?.addEventListener('click', () => dialog.close());

  dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!active) return;

    const {widget, action, id} = active;
    const rawUrl = config.getAttribute(`data-${widget.select.name}-${action}`);
    if (!rawUrl) return;
    const url = rawUrl.replace('/0/', `/${id}/`);
    const submit = form.querySelector('[type=submit]');
    submit.disabled = true;
    error.textContent = '';

    try {
      const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
      const response = await fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf,
        },
        body: JSON.stringify({
          name: form.elements.name.value,
          slug: form.elements.slug.value,
          parent_id: form.elements.parent_id.value || null,
        }),
      });

      if (!response.headers.get('content-type')?.includes('application/json')) {
        throw new Error('دسترسی مجاز نیست یا نشست شما منقضی شده است.');
      }

      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || 'عملیات انجام نشد.');

      if (action === 'delete') {
        [...widget.select.options].find(option => option.value === id)?.remove();
        if (!widget.select.multiple) widget.select.value = '';
      } else {
        let option = [...widget.select.options].find(item => item.value === String(data.id));
        if (!option) {
          option = new Option(data.name, String(data.id));
          widget.select.add(option);
        }
        option.textContent = data.name;
        option.dataset.slug = data.slug || '';
        option.dataset.parent = data.parent_id || '';
        if (action === 'add') option.selected = true;
        if (widget.picker) widget.picker.value = String(data.id);
      }

      refresh(widget);
      widget.select.dispatchEvent(new Event('change'));
      dialog.close();
    } catch (exc) {
      error.textContent = exc.message || 'عملیات انجام نشد.';
    } finally {
      submit.disabled = false;
    }
  });
})();
