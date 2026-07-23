/**
 * admin.js — ZTB Super App Admin Dashboard
 * Main JavaScript for all admin UI interactions:
 *   - Core utilities (section switching, toasts, fetch wrapper, confirm dialog)
 *   - Generic inline-editable TableManager engine
 *   - Questions Library management
 *   - Assessment Config management
 *   - DOMContentLoaded initialisation wiring
 *
 * External dependency: SheetJS (xlsx) must be loaded before this script
 *   <script src="https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js"></script>
 */

/* =========================================================
   1. CORE UTILITIES
   ========================================================= */

function showSection(name) {
  document.querySelectorAll('.section-panel').forEach(panel => {
    panel.classList.remove('active');
    panel.style.display = 'none';
  });
  document.querySelectorAll('.sidebar-nav-item').forEach(item => {
    item.classList.remove('active');
  });
  const target = document.querySelector(`.section-panel[data-section="${name}"]`);
  if (target) {
    target.classList.add('active');
    target.style.display = 'block';
  }
  const navItem = document.querySelector(`.sidebar-nav-item[data-section="${name}"]`);
  if (navItem) navItem.classList.add('active');
}

function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = [
      'position:fixed', 'top:1.25rem', 'right:1.25rem',
      'z-index:9999', 'display:flex', 'flex-direction:column', 'gap:0.5rem'
    ].join(';');
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  toast.style.cssText = [
    'padding:0.75rem 1.25rem',
    'border-radius:6px',
    'color:#fff',
    'font-size:0.875rem',
    'box-shadow:0 4px 12px rgba(0,0,0,0.15)',
    'opacity:0',
    'transition:opacity 0.25s ease',
    type === 'error' ? 'background:#e53e3e' : 'background:#38a169'
  ].join(';');
  container.appendChild(toast);
  requestAnimationFrame(() => {
    requestAnimationFrame(() => { toast.style.opacity = '1'; });
  });
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, 3000);
}

async function fetchAPI(url, method = 'GET', body = null) {
  const options = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' }
  };
  if (body !== null) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  if (response.status === 401) { window.location.href = '/admin/login'; return; }
  let data = null;
  const contentType = response.headers.get('Content-Type') || '';
  if (contentType.includes('application/json')) data = await response.json();
  if (!response.ok) {
    const errMsg = (data && data.message) ? data.message : response.statusText;
    throw new Error(errMsg);
  }
  return data;
}

function confirmDialog(message) {
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.style.cssText = [
      'position:fixed', 'inset:0', 'background:rgba(0,0,0,0.45)',
      'z-index:10000', 'display:flex', 'align-items:center', 'justify-content:center'
    ].join(';');
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog';
    dialog.style.cssText = [
      'background:#fff', 'border-radius:8px',
      'padding:1.5rem 2rem', 'max-width:420px', 'width:90%',
      'box-shadow:0 8px 32px rgba(0,0,0,0.2)'
    ].join(';');
    dialog.innerHTML = `
      <p style="margin:0 0 1.25rem;font-size:1rem;color:#2d3748;">${message}</p>
      <div style="display:flex;gap:0.75rem;justify-content:flex-end;">
        <button class="btn-cancel" style="padding:0.5rem 1rem;border:1px solid #cbd5e0;
          border-radius:5px;background:#fff;cursor:pointer;font-size:0.875rem;">Cancel</button>
        <button class="btn-confirm" style="padding:0.5rem 1rem;border:none;
          border-radius:5px;background:#e53e3e;color:#fff;cursor:pointer;font-size:0.875rem;">Confirm</button>
      </div>`;
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    function close(result) { overlay.remove(); resolve(result); }
    dialog.querySelector('.btn-confirm').addEventListener('click', () => close(true));
    dialog.querySelector('.btn-cancel').addEventListener('click', () => close(false));
    overlay.addEventListener('click', e => { if (e.target === overlay) close(false); });
    function onKey(e) {
      if (e.key === 'Escape') { document.removeEventListener('keydown', onKey); close(false); }
      if (e.key === 'Enter')  { document.removeEventListener('keydown', onKey); close(true);  }
    }
    document.addEventListener('keydown', onKey);
  });
}

/* =========================================================
   2. GENERIC INLINE-EDITABLE TABLE ENGINE
   ========================================================= */

class TableManager {
  constructor(config) {
    this.section        = config.section;
    this.tableId        = config.tableId;
    this.apiBase        = config.apiBase;
    this.defaultColumns = config.defaultColumns || [];
    this.fieldMap       = config.fieldMap || {};   // display name -> API key

    this.rows = [];
    this.columns = [...this.defaultColumns];
    this._dragSourceIndex = null;
  }

  async loadData() {
    try {
      const data = await fetchAPI(`${this.apiBase}/`);
      if (Array.isArray(data)) {
        this.rows = data;
      } else {
        this.rows    = data.rows    || [];
        this.columns = data.columns || this.defaultColumns;
      }
      this.renderTable(this.rows, this.columns);
    } catch (err) {
      showToast(`Failed to load data for ${this.section}: ${err.message}`, 'error');
    }
  }

  renderTable(rows, columns) {
    this.rows    = rows;
    this.columns = columns;

    const table = document.getElementById(this.tableId);
    if (!table) return;

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    columns.forEach((col, colIndex) => {
      const th = document.createElement('th');
      th.contentEditable = 'true';
      th.dataset.colIndex = colIndex;
      th.dataset.colName  = col;
      th.textContent      = col;
      th.draggable        = true;
      th.title            = 'Edit column name or drag to reorder';
      headerRow.appendChild(th);
    });

    const actionTh = document.createElement('th');
    actionTh.textContent = 'Actions';
    actionTh.style.width = '70px';
    headerRow.appendChild(actionTh);
    thead.appendChild(headerRow);

    const tbody = document.createElement('tbody');

    rows.forEach(row => {
      const tr = document.createElement('tr');
      tr.dataset.rowId = row.id ?? row.ID ?? '';

      columns.forEach(col => {
        const td = document.createElement('td');
        const apiKey = this.fieldMap[col] || col;
        td.contentEditable  = 'true';
        td.dataset.field    = apiKey;
        td.dataset.rowId    = row.id ?? row.ID ?? '';
        td.textContent      = row[apiKey] ?? '';
        tr.appendChild(td);
      });

      const actionTd = document.createElement('td');
      const delBtn   = document.createElement('button');
      delBtn.className   = 'btn-icon btn-delete';
      delBtn.textContent = '🗑';
      delBtn.title       = 'Delete row';
      delBtn.dataset.rowId = row.id ?? row.ID ?? '';
      actionTd.appendChild(delBtn);
      tr.appendChild(actionTd);

      tbody.appendChild(tr);
    });

    table.innerHTML = '';
    table.appendChild(thead);
    table.appendChild(tbody);

    this.attachHeaderListeners();
    this.attachCellListeners();
    this.setupDragAndDrop();
  }

  attachHeaderListeners() {
    const table = document.getElementById(this.tableId);
    if (!table) return;
    table.querySelectorAll('thead th[contenteditable="true"]').forEach(th => {
      th.dataset.originalName = th.textContent.trim();
      th.addEventListener('blur', async () => {
        const oldName = th.dataset.originalName;
        const newName = th.textContent.trim();
        if (!newName || newName === oldName) return;
        try {
          await fetchAPI(`${this.apiBase}/column`, 'PATCH', { oldName, newName });
          th.dataset.originalName = newName;
          th.dataset.colName      = newName;
          const idx = this.columns.indexOf(oldName);
          if (idx !== -1) this.columns[idx] = newName;
          showToast(`Column renamed to "${newName}"`, 'success');
        } catch (err) {
          showToast(`Rename failed: ${err.message}`, 'error');
          th.textContent = oldName;
        }
      });
    });
  }

  attachCellListeners() {
    const table = document.getElementById(this.tableId);
    if (!table) return;
    table.querySelectorAll('tbody td[contenteditable="true"]').forEach(td => {
      td.dataset.originalValue = td.textContent;
      td.addEventListener('blur', async () => {
        const original = td.dataset.originalValue;
        const value    = td.textContent;
        if (value === original) return;
        const id    = td.dataset.rowId;
        const field = td.dataset.field;
        try {
          await fetchAPI(`${this.apiBase}/cell`, 'PATCH', { id, field, value });
          td.dataset.originalValue = value;
        } catch (err) {
          showToast(`Save failed: ${err.message}`, 'error');
          td.textContent = original;
        }
      });
    });
    table.querySelectorAll('.btn-delete').forEach(btn => {
      btn.addEventListener('click', () => this.deleteRow(btn.dataset.rowId));
    });
  }

  async addRow() {
    const emptyRow = {};
    this.columns.forEach(col => {
      const apiKey = this.fieldMap[col] || col;
      emptyRow[apiKey] = '';
    });
    try {
      await fetchAPI(`${this.apiBase}/`, 'POST', emptyRow);
      await this.loadData();
      showToast('Row added', 'success');
    } catch (err) {
      showToast(`Add row failed: ${err.message}`, 'error');
    }
  }

  async deleteRow(id) {
    const ok = await confirmDialog(`Delete row #${id}? This cannot be undone.`);
    if (!ok) return;
    try {
      await fetchAPI(`${this.apiBase}/${id}`, 'DELETE');
      await this.loadData();
      showToast('Row deleted', 'success');
    } catch (err) {
      showToast(`Delete failed: ${err.message}`, 'error');
    }
  }

  async addColumn(name) {
    if (!name || !name.trim()) { showToast('Column name cannot be empty', 'error'); return; }
    try {
      await fetchAPI(`${this.apiBase}/columns`, 'POST', { name: name.trim() });
      await this.loadData();
      showToast(`Column "${name}" added`, 'success');
    } catch (err) {
      showToast(`Add column failed: ${err.message}`, 'error');
    }
  }

  async deleteColumn(name) {
    const ok = await confirmDialog(`Delete column "${name}"? All data in this column will be lost.`);
    if (!ok) return;
    try {
      await fetchAPI(`${this.apiBase}/columns/${encodeURIComponent(name)}`, 'DELETE');
      await this.loadData();
      showToast(`Column "${name}" deleted`, 'success');
    } catch (err) {
      showToast(`Delete column failed: ${err.message}`, 'error');
    }
  }

  async reorderColumns(newOrder) {
    try {
      await fetchAPI(`${this.apiBase}/columns/reorder`, 'PATCH', { order: newOrder });
      this.columns = newOrder;
      this.renderTable(this.rows, this.columns);
    } catch (err) {
      showToast(`Reorder failed: ${err.message}`, 'error');
    }
  }

  setupDragAndDrop() {
    const table = document.getElementById(this.tableId);
    if (!table) return;
    const ths = Array.from(table.querySelectorAll('thead th[draggable="true"]'));
    ths.forEach((th, index) => {
      th.addEventListener('dragstart', e => {
        this._dragSourceIndex = index;
        th.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
      });
      th.addEventListener('dragend', () => {
        th.classList.remove('dragging');
        ths.forEach(t => t.classList.remove('drag-over'));
      });
      th.addEventListener('dragover', e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        ths.forEach(t => t.classList.remove('drag-over'));
        th.classList.add('drag-over');
      });
      th.addEventListener('drop', e => {
        e.preventDefault();
        const targetIndex = index;
        const sourceIndex = this._dragSourceIndex;
        if (sourceIndex === null || sourceIndex === targetIndex) return;
        const newOrder = [...this.columns];
        const [moved]  = newOrder.splice(sourceIndex, 1);
        newOrder.splice(targetIndex, 0, moved);
        ths.forEach(t => t.classList.remove('drag-over'));
        this._dragSourceIndex = null;
        this.reorderColumns(newOrder);
      });
    });
  }

  async importExcel(file) {
    if (!window.XLSX) { showToast('SheetJS (XLSX) library not loaded', 'error'); return; }
    try {
      const buffer   = await file.arrayBuffer();
      const workbook = XLSX.read(buffer, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const sheet     = workbook.Sheets[sheetName];
      const jsonRows  = XLSX.utils.sheet_to_json(sheet, { defval: '' });
      if (jsonRows.length === 0) { showToast('The spreadsheet contains no data rows', 'error'); return; }
      const fileHeaders    = Object.keys(jsonRows[0]);
      const missingColumns = this.columns.filter(col => !fileHeaders.includes(col));
      if (missingColumns.length > 0) {
        showToast(`Missing columns in file: ${missingColumns.join(', ')}`, 'error');
        return;
      }
      await fetchAPI(`${this.apiBase}/import`, 'POST', { rows: jsonRows });
      await this.loadData();
      showToast(`Imported ${jsonRows.length} rows successfully`, 'success');
    } catch (err) {
      showToast(`Import failed: ${err.message}`, 'error');
    }
  }

  async exportExcel() {
    try {
      const response = await fetch(`${this.apiBase}/export`, { method: 'GET', credentials: 'include' });
      if (response.status === 401) { window.location.href = '/admin/login'; return; }
      if (response.ok) {
        const blob = await response.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `${this.section}-export.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        return;
      }
    } catch (_) {}
    if (!window.XLSX) { showToast('Export not available (SheetJS not loaded)', 'error'); return; }
    try {
      const wsData = [this.columns, ...this.rows.map(row => this.columns.map(col => {
        const apiKey = this.fieldMap[col] || col;
        return row[apiKey] ?? '';
      }))];
      const ws = XLSX.utils.aoa_to_sheet(wsData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, this.section);
      XLSX.writeFile(wb, `${this.section}-export.xlsx`);
      showToast('Export downloaded', 'success');
    } catch (err) {
      showToast(`Export failed: ${err.message}`, 'error');
    }
  }

  triggerImport() {
    const input = document.getElementById(`import-file-${this.section}`);
    if (input) input.click();
  }

  handleImport(input) {
    const file = input.files[0];
    if (file) this.importExcel(file);
    input.value = "";
  }
}

/* =========================================================
   3. TABLE MANAGER INSTANCES
   ========================================================= */

const valuePropsTable = new TableManager({
  section:        'valueprops',
  tableId:        'table-valueprops',
  apiBase:        '/admin/valueprops',
  defaultColumns: ['ID', 'Value Proposition Name', 'Description', 'Business Value', 'Mandatory?'],
  fieldMap: {
    'ID':                     'id',
    'Value Proposition Name': 'title',
    'Description':            'description',
    'Business Value':         'business_value',
    'Mandatory?':             'mandatory'
  }
});

const assetsTable = new TableManager({
  section:        'assets',
  tableId:        'table-assets',
  apiBase:        '/admin/assets',
  defaultColumns: ['ID', 'Asset Name', 'Asset Type', 'Link/URL', 'Description', 'Tags'],
  fieldMap: {
    'ID':          'id',
    'Asset Name':  'name',
    'Asset Type':  'asset_type',
    'Link/URL':    'url',
    'Description': 'description',
    'Tags':        'tags'
  }
});

const testCasesTable = new TableManager({
  section:        'testcases',
  tableId:        'table-testcases',
  apiBase:        '/admin/testcases',
  defaultColumns: ['ID', 'Test Case Name', 'Description', 'Steps', 'Expected Result', 'Tags'],
  fieldMap: {
    'ID':              'id',
    'Test Case Name':  'name',
    'Description':     'description',
    'Steps':           'steps',
    'Expected Result': 'expected_result',
    'Tags':            'tags'
  }
});

const povTable = new TableManager({
  section:        'povplanner',
  tableId:        'table-povplanner',
  apiBase:        '/admin/povplanner',
  defaultColumns: ['ID', 'POV Step Name', 'Description', 'Duration', 'Owner', 'Status'],
  fieldMap: {
    'ID':            'id',
    'POV Step Name': 'name',
    'Description':   'description',
    'Duration':      'duration',
    'Owner':         'owner',
    'Status':        'status'
  }
});

const roadblocksTable = new TableManager({
  section:        'roadblocks',
  tableId:        'table-roadblocks',
  apiBase:        '/admin/roadblocks',
  defaultColumns: ['ID', 'Roadblock Name', 'Description', 'Category', 'Severity', 'Mitigation'],
  fieldMap: {
    'ID':             'id',
    'Roadblock Name': 'name',
    'Description':    'description',
    'Category':       'category',
    'Severity':       'severity',
    'Mitigation':     'mitigation'
  }
});

const TABLE_MANAGERS = {
  valueprops:  valuePropsTable,
  assets:      assetsTable,
  testcases:   testCasesTable,
  povplanner:  povTable,
  roadblocks:  roadblocksTable
};
const libraryTables = TABLE_MANAGERS;
   5. ASSESSMENT CONFIG
   ========================================================= */

let _assessmentConfig = [];

async function loadAssessmentConfig() {
  try {
    const config = await fetchAPI('/admin/assessment/config');
    _assessmentConfig = Array.isArray(config) ? config : (config.items || []);
    renderConfigList(_assessmentConfig);
  } catch (err) {
    showToast(`Failed to load assessment config: ${err.message}`, 'error');
  }
}

function renderConfigList(config) {
  const container = document.getElementById('assessment-config-list');
  if (!container) return;
  container.innerHTML = '';
  if (!config || config.length === 0) {
    container.innerHTML = '<p class="empty-state">No assessment config items found.</p>';
    return;
  }
  config.forEach((item, index) => {
    const li = document.createElement('li');
    li.className      = 'config-item';
    li.dataset.itemId = item.id;
    li.dataset.index  = index;
    li.draggable      = true;
    li.innerHTML = `
      <span class="drag-handle config-drag-handle" title="Drag to reorder">⠿</span>
      <input type="checkbox" class="config-checkbox" id="config-item-${item.id}"
             data-item-id="${item.id}" ${item.enabled ? 'checked' : ''}>
      <label for="config-item-${item.id}" class="config-label">${item.name || item.id}</label>`;
    container.appendChild(li);
  });
  setupConfigDragDrop();
}

function setupConfigDragDrop() {
  const container = document.getElementById('assessment-config-list');
  if (!container) return;
  let dragSrcEl = null;
  const items = Array.from(container.querySelectorAll('.config-item'));
  items.forEach(item => {
    item.addEventListener('dragstart', e => {
      dragSrcEl = item;
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', item.dataset.index);
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      container.querySelectorAll('.config-item').forEach(el => el.classList.remove('drag-over'));
    });
    item.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      if (item !== dragSrcEl) {
        container.querySelectorAll('.config-item').forEach(el => el.classList.remove('drag-over'));
        item.classList.add('drag-over');
      }
    });
    item.addEventListener('drop', e => {
      e.preventDefault();
      if (!dragSrcEl || dragSrcEl === item) return;
      container.insertBefore(dragSrcEl, item);
      Array.from(container.querySelectorAll('.config-item')).forEach((el, i) => { el.dataset.index = i; });
      item.classList.remove('drag-over');
      dragSrcEl = null;
    });
  });
}

async function saveAssessmentConfig() {
  const container = document.getElementById('assessment-config-list');
  if (!container) return;
  const items = Array.from(container.querySelectorAll('.config-item')).map((li, index) => ({
    id:      li.dataset.itemId,
    enabled: li.querySelector('.config-checkbox')?.checked ?? true,
    order:   index
  }));
  try {
    await fetchAPI('/admin/assessment/config', 'POST', { items });
    showToast('Assessment config saved', 'success');
  } catch (err) {
    showToast(`Save config failed: ${err.message}`, 'error');
  }
}

/* =========================================================
   6. INITIALISATION
   ========================================================= */

document.addEventListener('DOMContentLoaded', async () => {

  showSection('valueprops');

  await Promise.all([
    valuePropsTable.loadData(),
    assetsTable.loadData(),
    testCasesTable.loadData(),
    povTable.loadData(),
    roadblocksTable.loadData()
  ]);

  if (typeof loadQuestions === 'function') await loadQuestions();
  if (typeof loadAssessmentConfig === 'function') await loadAssessmentConfig();


  document.querySelectorAll('.sidebar-nav-item[data-section]').forEach(navItem => {
    navItem.addEventListener('click', () => showSection(navItem.dataset.section));
  });

  document.querySelectorAll('[data-action][data-section]').forEach(btn => {
    const action  = btn.dataset.action;
    const section = btn.dataset.section;
    const mgr     = TABLE_MANAGERS[section];
    if (!mgr) return;
    switch (action) {
      case 'add-row':
        btn.addEventListener('click', () => mgr.addRow());
        break;
      case 'add-column':
        btn.addEventListener('click', async () => {
          const name = await _promptDialog('Enter new column name:');
          if (name) mgr.addColumn(name);
        });
        break;
      case 'import':
        btn.addEventListener('click', () => {
          const fileInput = document.getElementById(`${section}-import-input`);
          if (fileInput) { fileInput.value = ''; fileInput.click(); }
        });
        break;
      case 'export':
        btn.addEventListener('click', () => mgr.exportExcel());
        break;
    }
  });

  Object.keys(TABLE_MANAGERS).forEach(section => {
    const fileInput = document.getElementById(`${section}-import-input`);
    if (!fileInput) return;
    fileInput.addEventListener('change', () => {
      const file = fileInput.files[0];
      if (file) TABLE_MANAGERS[section].importExcel(file);
    });
  });

  const addQuestionBtn = document.getElementById('btn-add-question');
  if (addQuestionBtn) addQuestionBtn.addEventListener('click', addQuestion);

  const saveConfigBtn = document.getElementById('btn-save-assessment-config');
  if (saveConfigBtn) saveConfigBtn.addEventListener('click', saveAssessmentConfig);

  Object.entries(TABLE_MANAGERS).forEach(([section, mgr]) => {
    const panel = document.querySelector(`.section-panel[data-section="${section}"]`);
    if (!panel) return;
    panel.addEventListener('click', async e => {
      const btn = e.target.closest('[data-action="delete-column"]');
      if (btn) { const col = btn.dataset.column; if (col) await mgr.deleteColumn(col); }
    });
  });

  if (typeof window !== 'undefined') {
    window._ztbAdmin = { TABLE_MANAGERS, loadAssessmentConfig, showSection, showToast };
  }
});

/* =========================================================
   HELPER — _promptDialog
   ========================================================= */

function _promptDialog(message) {
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.style.cssText = [
      'position:fixed', 'inset:0', 'background:rgba(0,0,0,0.45)',
      'z-index:10000', 'display:flex', 'align-items:center', 'justify-content:center'
    ].join(';');
    const dialog = document.createElement('div');
    dialog.style.cssText = [
      'background:#fff', 'border-radius:8px', 'padding:1.5rem 2rem',
      'max-width:420px', 'width:90%', 'box-shadow:0 8px 32px rgba(0,0,0,0.2)'
    ].join(';');
    dialog.innerHTML = `
      <p style="margin:0 0 0.75rem;font-size:1rem;color:#2d3748;">${message}</p>
      <input type="text" class="prompt-input" style="
        width:100%;padding:0.5rem 0.75rem;border:1px solid #cbd5e0;
        border-radius:5px;font-size:0.875rem;box-sizing:border-box;
        margin-bottom:1rem;" autofocus>
      <div style="display:flex;gap:0.75rem;justify-content:flex-end;">
        <button class="btn-cancel" style="padding:0.5rem 1rem;border:1px solid #cbd5e0;
          border-radius:5px;background:#fff;cursor:pointer;font-size:0.875rem;">Cancel</button>
        <button class="btn-ok" style="padding:0.5rem 1rem;border:none;
          border-radius:5px;background:#3182ce;color:#fff;cursor:pointer;font-size:0.875rem;">OK</button>
      </div>`;
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    const input = dialog.querySelector('.prompt-input');
    function close(value) { overlay.remove(); resolve(value); }
    dialog.querySelector('.btn-ok').addEventListener('click', () => close(input.value.trim() || null));
    dialog.querySelector('.btn-cancel').addEventListener('click', () => close(null));
    overlay.addEventListener('click', e => { if (e.target === overlay) close(null); });
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter')  close(input.value.trim() || null);
      if (e.key === 'Escape') close(null);
    });
    requestAnimationFrame(() => input.focus());
  });
}
