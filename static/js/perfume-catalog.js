(() => {
  'use strict';
  const config = document.getElementById('pa-catalog-config');
  if (!config) return;
  const dialog = document.getElementById('pa-catalog-dialog');
  const form = document.getElementById('pa-catalog-form');
  const error = document.getElementById('pa-catalog-error');
  let active = null;
  const widgets = [];
  const labels = {category:'دسته‌بندی', brand:'برند', product_type:'غلظت / نوع رایحه', tags:'تگ رایحه'};
  function button(text, action) {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = text;
    b.addEventListener('click', action); return b;
  }
  function refresh(widget) {
    const {select, picker, list, edit, remove} = widget;
    if (picker) {
      const previous = picker.value;
      picker.replaceChildren(new Option('انتخاب تگ برای ویرایش یا حذف', ''));
      list.replaceChildren();
      [...select.options].filter(o => o.value).forEach(option => {
        picker.add(new Option(option.textContent.trim(), option.value));
        const label = document.createElement('label'); label.className = 'pa-tag-choice';
        const input = document.createElement('input'); input.type = 'checkbox'; input.checked = option.selected;
        input.addEventListener('change', () => {option.selected = input.checked; select.dispatchEvent(new Event('change'));});
        label.append(input, document.createTextNode(option.textContent.trim())); list.append(label);
      });
      picker.value = previous;
    }
    const selected = (picker || select).value;
    if (edit) edit.disabled = remove.disabled = !selected;
  }
  function open(widget, action) {
    const id = (widget.picker || widget.select).value;
    const option = [...widget.select.options].find(o => o.value === id);
    if (action !== 'add' && !option) return;
    active = {widget, action, id}; form.reset(); error.textContent = '';
    document.getElementById('pa-catalog-title').textContent = ({add:'افزودن ', edit:'ویرایش ', delete:'حذف '})[action] + labels[widget.select.name];
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
      [...widget.select.options].filter(o => o.value && (action === 'add' || o.value !== id)).forEach(o => parent.add(new Option(o.textContent.trim(), o.value)));
      parent.value = action === 'add' ? '' : option.dataset.parent || '';
    }
    dialog.showModal();
  }
  Object.keys(labels).forEach(name => {
    const select = document.querySelector(`select[name="${name}"]`);
    if (!select) return;
    const row = document.createElement('div'); row.className = 'pa-catalog-actions';
    const widget = {select}; widgets.push(widget);
    if (select.multiple) {
      select.hidden = true;
      const list = document.createElement('div'); list.className = 'pa-tag-list';
      select.after(list); widget.list = list;
      const picker = document.createElement('select'); picker.setAttribute('aria-label', 'تگ برای مدیریت'); widget.picker = picker;
      if (config.dataset.canManage === 'true') row.append(picker);
      picker.addEventListener('change', () => {widget.edit.disabled = widget.remove.disabled = !picker.value;});
    }
    if (config.dataset.canManage === 'true') {
      const add = button('+ افزودن', () => open(widget, 'add'));
      widget.edit = button('ویرایش', () => open(widget, 'edit'));
      widget.remove = button('حذف', () => open(widget, 'delete'));
      row.append(add, widget.edit, widget.remove);
    }
    select.after(row);
    select.addEventListener('change', () => refresh(widget)); refresh(widget);
  });
  document.getElementById('pa-catalog-cancel').addEventListener('click', () => dialog.close());
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const {widget, action, id} = active;
    const url = config.getAttribute(`data-${widget.select.name}-${action}`).replace('/0/', `/${id}/`);
    const submit = form.querySelector('[type=submit]'); submit.disabled = true; error.textContent = '';
    try {
      const response = await fetch(url, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json', 'X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value}, body:JSON.stringify({name:form.elements.name.value, slug:form.elements.slug.value, parent_id:form.elements.parent_id.value || null})});
      if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('دسترسی مجاز نیست یا نشست شما منقضی شده است.');
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || 'عملیات انجام نشد.');
      if (action === 'delete') {
        const option = [...widget.select.options].find(o => o.value === id); option?.remove();
        if (!widget.select.multiple) widget.select.value = '';
      } else {
        let option = [...widget.select.options].find(o => o.value === String(data.id));
        if (!option) {option = new Option(data.name, String(data.id)); widget.select.add(option);}
        option.textContent = data.name; option.dataset.slug = data.slug; option.dataset.parent = data.parent_id || '';
        if (action === 'add') option.selected = true;
        if (widget.picker) widget.picker.value = String(data.id);
      }
      refresh(widget); widget.select.dispatchEvent(new Event('change')); dialog.close();
    } catch (exc) {error.textContent = exc.message;}
    finally {submit.disabled = false;}
  });
})();
