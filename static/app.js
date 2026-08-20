document.addEventListener('DOMContentLoaded', () => {
  // --- Navigation Tab Switching ---
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabPanes = document.querySelectorAll('.tab-pane');

  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      navTabs.forEach(t => t.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      document.getElementById(targetId).classList.add('active');
    });
  });

  // --- Theme Toggle ---
  const themeToggle = document.getElementById('themeToggle');
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
    const icon = themeToggle.querySelector('i');
    if (document.body.classList.contains('light-theme')) {
      icon.className = 'fa-solid fa-sun';
    } else {
      icon.className = 'fa-solid fa-moon';
    }
  });

  // --- Sample Routine for Code Studio ---
  const SAMPLE_ROUTINE = `*-----------------------------------------------------------------------------
* <Rating>0</Rating>
*-----------------------------------------------------------------------------
    SUBROUTINE V.VAL.CHECK.LIMIT.EXPIRY
*-----------------------------------------------------------------------------
* Description: Validates Limit Expiry Date against TODAY + 30 days.
*-----------------------------------------------------------------------------
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_F.LIMIT
    $INSERT I_F.CUSTOMER

    IF NOT(V$FUNCTION MATCHES 'I':@VM:'C') THEN
        RETURN
    END

    GOSUB INITIALISE
    GOSUB PROCESS.VALIDATION
    RETURN

INITIALISE:
    FN.CUSTOMER = 'F.CUSTOMER'
    F.CUSTOMER  = ''
    CALL OPF(FN.CUSTOMER, F.CUSTOMER)

    Y.EXPIRY.DATE = R.NEW(LI.EXPIRY.DATE)
    Y.CUST.ID     = R.NEW(LI.CUSTOMER.NUMBER)
    Y.MIN.DAYS    = '+30C'
    RETURN

PROCESS.VALIDATION:
    IF Y.EXPIRY.DATE EQ '' THEN
        AF = LI.EXPIRY.DATE
        ETEXT = 'EB-MANDATORY.FIELD'
        CALL STORE.END.ERROR
        RETURN
    END

    Y.CALC.DATE = TODAY
    CALL CDT('', Y.CALC.DATE, Y.MIN.DAYS)

    IF Y.EXPIRY.DATE < Y.CALC.DATE THEN
        AF = LI.EXPIRY.DATE
        ETEXT = 'EB-EXPIRY.DATE.TOO.EARLY' : @FM : Y.CALC.DATE
        CALL STORE.END.ERROR
        RETURN
    END

    R.CUST.REC = ''
    Y.CUST.ERR = ''
    CALL F.READ(FN.CUSTOMER, Y.CUST.ID, R.CUST.REC, F.CUSTOMER, Y.CUST.ERR)
    IF Y.CUST.ERR NE '' THEN
        AF = LI.CUSTOMER.NUMBER
        ETEXT = 'EB-CUSTOMER.NOT.FOUND'
        CALL STORE.END.ERROR
        RETURN
    END

    RETURN
    END`;

  const codeEditor = document.getElementById('codeEditor');
  codeEditor.value = SAMPLE_ROUTINE;

  document.getElementById('loadSampleBtn').addEventListener('click', () => {
    codeEditor.value = SAMPLE_ROUTINE;
  });

  // Quick Send from Studio to Learning tab
  document.getElementById('sendToLearnBtn').addEventListener('click', () => {
    const currentCode = codeEditor.value;
    document.getElementById('learnCode').value = currentCode;
    document.getElementById('learnTitle').value = 'Imported from Studio';
    document.querySelector('.nav-tab[data-tab="learning"]').click();
  });

  // --- Export .b File ---
  document.getElementById('downloadCodeBtn').addEventListener('click', () => {
    const code = codeEditor.value;
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = document.getElementById('currentFileName').textContent || 'ROUTINE.b';
    a.click();
    URL.revokeObjectURL(url);
  });

  // --- Run Linter ---
  const runLintBtn = document.getElementById('runLintBtn');
  const lintResultsContainer = document.getElementById('lintResultsContainer');
  const scoreBadge = document.getElementById('scoreBadge');

  runLintBtn.addEventListener('click', async () => {
    const code = codeEditor.value;
    if (!code.trim()) {
      alert('Please enter source code to analyze.');
      return;
    }

    runLintBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
    try {
      const resp = await fetch('/api/lint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });
      const data = await resp.json();

      scoreBadge.textContent = `Score: ${data.score}/100 [${data.status}]`;
      scoreBadge.style.color = data.status === 'PASS' ? 'var(--success)' : 'var(--danger)';

      if (data.issues.length === 0) {
        lintResultsContainer.innerHTML = `
          <div class="empty-state">
            <i class="fa-solid fa-circle-check" style="color: var(--success);"></i>
            <p><strong>Zero Defects Detected!</strong><br>Code conforms strictly to Temenos T24, TAFJ, concurrency, and performance guidelines.</p>
          </div>
        `;
      } else {
        lintResultsContainer.innerHTML = data.issues.map(issue => `
          <div class="issue-card ${issue.severity}">
            <div class="issue-header">
              <div class="issue-title">
                <span class="badge badge-${issue.severity.toLowerCase()}">${issue.severity}</span>
                <span>${issue.title}</span>
              </div>
              <span class="issue-line">Line ${issue.line}</span>
            </div>
            <div class="issue-msg">${issue.message}</div>
            ${issue.code_snippet ? `<div class="issue-snippet">${escapeHtml(issue.code_snippet)}</div>` : ''}
            ${issue.suggestion ? `<div class="issue-fix"><strong>Recommended Fix:</strong>\n${escapeHtml(issue.suggestion)}</div>` : ''}
          </div>
        `).join('');
      }
    } catch (err) {
      lintResultsContainer.innerHTML = `<div class="issue-card CRITICAL"><p>Error communicating with linter: ${err.message}</p></div>`;
    } finally {
      runLintBtn.innerHTML = '<i class="fa-solid fa-shield-halved"></i> Run T24 Linter';
    }
  });

  // --- Routine Scaffolder Engine ---
  let availableTemplates = [];
  let currentSelectedTemplate = null;

  async function loadTemplates() {
    try {
      const resp = await fetch('/api/templates');
      const data = await resp.json();
      availableTemplates = data.templates;

      const templateListEl = document.getElementById('templateList');
      templateListEl.innerHTML = availableTemplates.map((t, idx) => `
        <div class="template-item ${idx === 0 ? 'active' : ''}" data-id="${t.id}">
          <h4>${t.name}</h4>
          <p>${t.category}</p>
        </div>
      `).join('');

      if (availableTemplates.length > 0) {
        selectTemplate(availableTemplates[0].id);
      }

      document.querySelectorAll('.template-item').forEach(item => {
        item.addEventListener('click', () => {
          document.querySelectorAll('.template-item').forEach(i => i.classList.remove('active'));
          item.classList.add('active');
          selectTemplate(item.getAttribute('data-id'));
        });
      });
    } catch (err) {
      console.error('Failed to load templates', err);
    }
  }

  function selectTemplate(templateId) {
    currentSelectedTemplate = availableTemplates.find(t => t.id === templateId);
    if (!currentSelectedTemplate) return;

    document.getElementById('templateTitle').textContent = currentSelectedTemplate.name;
    document.getElementById('templateDescription').textContent = currentSelectedTemplate.description;

    const fieldsContainer = document.getElementById('dynamicFormFields');
    fieldsContainer.innerHTML = currentSelectedTemplate.fields.map(f => `
      <div class="form-group">
        <label>${f.label}</label>
        <input type="text" id="field_${f.name}" name="${f.name}" value="${f.default}" class="input-control">
      </div>
    `).join('');
  }

  document.getElementById('generateRoutineBtn').addEventListener('click', async () => {
    if (!currentSelectedTemplate) return;

    const params = {};
    currentSelectedTemplate.fields.forEach(f => {
      const input = document.getElementById(`field_${f.name}`);
      if (input) params[f.name] = input.value;
    });

    try {
      const resp = await fetch('/api/templates/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: currentSelectedTemplate.id,
          params
        })
      });
      const data = await resp.json();
      document.getElementById('generatedCodeBlock').textContent = data.code;
    } catch (err) {
      alert('Error generating template: ' + err.message);
    }
  });

  document.getElementById('copyGeneratedBtn').addEventListener('click', () => {
    const text = document.getElementById('generatedCodeBlock').textContent;
    navigator.clipboard.writeText(text);
    alert('Generated code copied to clipboard!');
  });

  document.getElementById('loadToEditorBtn').addEventListener('click', () => {
    const text = document.getElementById('generatedCodeBlock').textContent;
    codeEditor.value = text;
    document.querySelector('.nav-tab[data-tab="studio"]').click();
  });

  loadTemplates();

  // --- Pattern Learning & Memory Store Engine ---
  const submitLearnBtn = document.getElementById('submitLearnBtn');
  const learnedSamplesList = document.getElementById('learnedSamplesList');
  const learnedCountBadge = document.getElementById('learnedCountBadge');

  async function loadLearnedSamples() {
    try {
      const resp = await fetch('/api/learned-samples');
      const data = await resp.json();
      const samples = data.samples || [];
      learnedCountBadge.textContent = samples.length;

      if (samples.length === 0) {
        learnedSamplesList.innerHTML = `
          <div class="empty-state">
            <i class="fa-solid fa-graduation-cap"></i>
            <p><strong>Memory Store Empty</strong><br>Submit your bank's production routines on the left to train the AI with your local patterns.</p>
          </div>
        `;
        return;
      }

      learnedSamplesList.innerHTML = samples.map(s => `
        <div class="sample-card">
          <div class="sample-card-header">
            <div>
              <h4>${escapeHtml(s.title)}</h4>
              <div class="sample-badge-row">
                <span class="badge badge-stmt">${escapeHtml(s.category)}</span>
                ${s.extracted_routine_name ? `<span class="tag-badge"><i class="fa-solid fa-code"></i> ${escapeHtml(s.extracted_routine_name)}</span>` : ''}
              </div>
            </div>
            <button class="btn btn-danger btn-sm delete-sample-btn" data-id="${s.id}" title="Delete Sample"><i class="fa-solid fa-trash"></i></button>
          </div>
          
          ${s.notes ? `<p style="font-size: 0.8rem; color: var(--text-secondary);"><strong>Note:</strong> ${escapeHtml(s.notes)}</p>` : ''}
          
          <div class="sample-badge-row">
            ${s.extracted_inserts.length > 0 ? `<span class="tag-badge">Inserts: ${escapeHtml(s.extracted_inserts.join(', '))}</span>` : ''}
            ${s.extracted_tables.length > 0 ? `<span class="tag-badge">Tables: ${escapeHtml(s.extracted_tables.join(', '))}</span>` : ''}
          </div>

          <div class="sample-actions">
            <button class="btn btn-secondary btn-sm load-sample-to-editor" data-id="${s.id}"><i class="fa-solid fa-arrow-right-to-bracket"></i> Load in Editor</button>
          </div>
        </div>
      `).join('');

      // Attach Delete Handlers
      document.querySelectorAll('.delete-sample-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          const id = btn.getAttribute('data-id');
          if (confirm('Are you sure you want to delete this learned pattern from AI memory?')) {
            await fetch(`/api/learned-samples/${id}`, { method: 'DELETE' });
            loadLearnedSamples();
          }
        });
      });

      // Attach Load in Editor Handlers
      document.querySelectorAll('.load-sample-to-editor').forEach(btn => {
        btn.addEventListener('click', () => {
          const id = parseInt(btn.getAttribute('data-id'));
          const sample = samples.find(s => s.id === id);
          if (sample) {
            codeEditor.value = sample.code;
            document.getElementById('currentFileName').textContent = `${sample.extracted_routine_name || 'LEARNED_ROUTINE'}.b`;
            document.querySelector('.nav-tab[data-tab="studio"]').click();
          }
        });
      });

    } catch (err) {
      console.error('Error loading learned patterns', err);
    }
  }

  submitLearnBtn.addEventListener('click', async () => {
    const title = document.getElementById('learnTitle').value.trim();
    const category = document.getElementById('learnCategory').value;
    const tags = document.getElementById('learnTags').value.trim();
    const notes = document.getElementById('learnNotes').value.trim();
    const code = document.getElementById('learnCode').value.trim();

    if (!title || !code) {
      alert('Please provide both a Title and Source Code.');
      return;
    }

    submitLearnBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting...';
    try {
      const resp = await fetch('/api/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, category, tags, notes, code })
      });
      const data = await resp.json();

      if (data.status === 'success') {
        alert(data.message);
        document.getElementById('learnTitle').value = '';
        document.getElementById('learnTags').value = '';
        document.getElementById('learnNotes').value = '';
        document.getElementById('learnCode').value = '';
        loadLearnedSamples();
      }
    } catch (err) {
      alert('Failed to learn sample: ' + err.message);
    } finally {
      submitLearnBtn.innerHTML = '<i class="fa-solid fa-brain"></i> Ingest & Train AI Memory';
    }
  });

  document.getElementById('refreshSamplesBtn').addEventListener('click', () => {
    loadLearnedSamples();
  });

  loadLearnedSamples();

  // --- OFS Message Builder ---
  document.getElementById('buildOfsBtn').addEventListener('click', () => {
    const appVer = document.getElementById('ofsAppVersion').value.trim();
    const func = document.getElementById('ofsFunction').value;
    const op = document.getElementById('ofsOperation').value;
    const comp = document.getElementById('ofsCompany').value.trim();
    const fieldsRaw = document.getElementById('ofsFieldList').value.trim().split('\n');

    const formattedFields = fieldsRaw
      .filter(line => line.includes('='))
      .map(line => line.trim())
      .join(',');

    const ofsPayload = `${appVer}/${func}/${op},//${comp},,${formattedFields}`;
    document.getElementById('ofsResultPayload').textContent = ofsPayload;
  });

  // --- Accounting Entry Visualizer ---
  document.getElementById('visualizeAccountingBtn').addEventListener('click', () => {
    const acct = document.getElementById('accDebitAcct').value.trim();
    const amt = parseFloat(document.getElementById('accAmount').value) || 0;
    const pl = document.getElementById('accPlCategory').value.trim();

    const tbody = document.getElementById('ledgerTableBody');
    tbody.innerHTML = `
      <tr>
        <td><span class="badge badge-stmt">STMT.ENTRY</span></td>
        <td>${acct} (Customer Account)</td>
        <td><span class="text-danger">DEBIT (-)</span></td>
        <td>-${amt.toFixed(2)}</td>
        <td>150</td>
      </tr>
      <tr>
        <td><span class="badge badge-categ">CATEG.ENTRY</span></td>
        <td>PL${pl} (Internal P&L)</td>
        <td><span class="text-success">CREDIT (+)</span></td>
        <td>+${amt.toFixed(2)}</td>
        <td>150</td>
      </tr>
    `;

    const net = -amt + amt;
    document.getElementById('netBalanceValue').textContent = `${net.toFixed(2)} LCY (BALANCED)`;
  });

  // --- AI Chat Studio ---
  const chatInput = document.getElementById('chatInput');
  const sendChatBtn = document.getElementById('sendChatBtn');
  const chatMessages = document.getElementById('chatMessages');

  async function handleSendMessage(promptText) {
    const prompt = promptText || chatInput.value.trim();
    if (!prompt) return;

    appendMessage('user', prompt);
    chatInput.value = '';

    const loadingId = appendMessage('assistant', '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing banking architecture and learned patterns...');

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await resp.json();
      updateMessage(loadingId, formatMarkdown(data.response));
    } catch (err) {
      updateMessage(loadingId, `<p class="text-danger">Error: ${err.message}</p>`);
    }
  }

  sendChatBtn.addEventListener('click', () => handleSendMessage());
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      handleSendMessage(prompt);
    });
  });

  function appendMessage(role, htmlContent) {
    const id = 'msg_' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role === 'user' ? 'user-msg' : 'system-msg'}`;
    msgDiv.id = id;
    msgDiv.innerHTML = `
      <div class="msg-avatar"><i class="fa-solid ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i></div>
      <div class="msg-content">${htmlContent}</div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
  }

  function updateMessage(id, htmlContent) {
    const msgDiv = document.getElementById(id);
    if (msgDiv) {
      msgDiv.querySelector('.msg-content').innerHTML = htmlContent;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  function formatMarkdown(text) {
    return text
      .replace(/```basic([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});
