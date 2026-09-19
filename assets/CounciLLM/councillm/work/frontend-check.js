
        // --- 1. Dynamic Greeting Setup ---
        const hour = new Date().getHours();
        const greetingEl = document.getElementById('greeting-text');
        if(hour < 12) greetingEl.textContent = "Coffee and Time with Me?";
        else if(hour < 18) greetingEl.textContent = "Good afternoon";
        else greetingEl.textContent = "Good evening";

        const API_BASE = window.location.origin;
        const conversation = [];
        let selectedModel = 'auto';

        // --- 2. Interactive Dropdown State Management ---
        function closeAllDropdowns() {
            document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('show'));
        }
        
        function setupDropdown(btnId, dropdownId) {
            document.getElementById(btnId).addEventListener('click', (e) => {
                e.stopPropagation();
                const dd = document.getElementById(dropdownId);
                const isShowing = dd.classList.contains('show');
                closeAllDropdowns();
                if(!isShowing) dd.classList.add('show');
            });
        }

        setupDropdown('profile-btn', 'profile-dropdown');
        setupDropdown('attach-btn', 'attach-dropdown');
        setupDropdown('model-btn', 'model-dropdown');

        document.addEventListener('click', closeAllDropdowns);
        document.addEventListener('keydown', (e) => {
            if(e.key === 'Escape') {
                closeAllDropdowns();
                document.querySelectorAll('dialog').forEach(d => d.close());
            }
        });

        // --- 3. Sidebar Collapsible Sections ---
        function toggleSection(id) {
            const el = document.getElementById(id);
            if(el.style.display === 'none') {
                el.style.display = 'block';
            } else {
                el.style.display = 'none';
            }
        }

        function setModel(modelName, label) {
            selectedModel = modelName;
            document.getElementById('active-model-name').textContent = label || modelName;
            closeAllDropdowns();
        }

        // --- 4. Chat View Transition ---
        function resetToHome() {
            document.getElementById('chat-stream').innerHTML = '';
            conversation.length = 0;
            document.getElementById('home-view').classList.remove('hidden');
            document.getElementById('chat-view').style.display = 'none';
            document.getElementById('chat-input-container').classList.add('hidden');
            document.getElementById('main-input-wrapper').style.margin = "0";
            
            // Re-inject input to home
            const inputWrapper = document.getElementById('main-input-wrapper');
            document.querySelector('.home-container').insertBefore(inputWrapper, document.querySelector('.quick-chips'));
            
            resetProgress();
        }

        function resetProgress() {
            document.getElementById('workflow-status').textContent = "Waiting for task...";
            const steps = document.getElementById('workflow-steps');
            steps.innerHTML = [
                'Analyze request context', 'Select model', 'Generate response'
            ].map((label, index) => `<div class="progress-step"><div class="step-icon pending">${index + 1}</div><div class="step-text text-sm text-muted">${label}</div></div>`).join('');
        }

        function escapeHtml(text) {
            return String(text)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        function renderTrace(tree, toolContainer, route, model, trace) {
            tree.classList.remove('hidden');
            toolContainer.innerHTML = '';
            toolContainer.insertAdjacentHTML(
                'beforeend',
                `<div class="tool-block">[router] ${escapeHtml(route.reason || 'Route selected locally')}</div>`
            );
            if(model && model.display_name) {
                toolContainer.insertAdjacentHTML(
                    'beforeend',
                    `<div class="tool-block">[model] ${escapeHtml(model.display_name)}${model.port ? ' on port ' + escapeHtml(model.port) : ''}</div>`
                );
            }
            (trace || []).forEach((step) => {
                toolContainer.insertAdjacentHTML(
                    'beforeend',
                    `<div class="tool-block">[${escapeHtml(step.status || 'info')}] ${escapeHtml(step.step || '')}${step.detail ? ' - ' + escapeHtml(step.detail) : ''}</div>`
                );
            });
        }

        function setProgressFromTrace(trace) {
            const steps = document.querySelectorAll('.progress-step');
            const stageLabels = [
                trace?.[0]?.step || 'Analyze request context',
                trace?.[1]?.step || 'Select model',
                trace?.[2]?.step || 'Generate response'
            ];
            steps.forEach((step, index) => {
                if(index < stageLabels.length) {
                    step.innerHTML = `<div class="step-icon done">✓</div><div class="step-text done text-sm">${escapeHtml(stageLabels[index])}</div>`;
                }
            });
        }

        async function submitPrompt() {
            const inputEl = document.getElementById('prompt-input');
            const text = inputEl.value.trim();
            if(!text) return;

            inputEl.value = '';
            inputEl.style.height = '48px';
            document.getElementById('home-view').classList.add('hidden');
            const chatView = document.getElementById('chat-view');
            chatView.style.display = 'flex';

            const inputWrapper = document.getElementById('main-input-wrapper');
            const floatContainer = document.getElementById('chat-input-container');
            floatContainer.classList.remove('hidden');
            floatContainer.insertBefore(inputWrapper, floatContainer.firstChild);

            const stream = document.getElementById('chat-stream');

            const userHtml = `
                <div class="msg user">
                    <div class="msg-bubble">${escapeHtml(text)}</div>
                </div>
            `;
            stream.insertAdjacentHTML('beforeend', userHtml);
            window.scrollTo(0, document.body.scrollHeight);

            document.getElementById('right-sidebar').classList.remove('hidden');
            resetProgress();
            updateProgress(0, 'active', 'Analyzing request context...');

            const agentContainerId = 'agent-msg-' + Date.now();
            const agentHtml = `
                <div class="msg agent" id="${agentContainerId}">
                    <div class="agent-header">
                        <div class="avatar" style="width:24px; height:24px; font-size:12px;">
                            <svg class="text-root" width="14" height="14" viewBox="0 0 24 24" fill="var(--bg-root)"><path d="M12 2L13.5 9.5L21 11L13.5 12.5L12 20L10.5 12.5L3 11L10.5 9.5L12 2Z"/></svg>
                        </div>
                        <span class="text-sm font-semibold">CounciLLM</span>
                    </div>
                    <div class="msg-bubble font-serif">
                        <div class="tool-tree hidden" id="tree-${agentContainerId}">
                            <div class="text-xs text-muted mb-2 font-sans">Local council trace</div>
                            <div class="tool-container flex flex-col gap-2"></div>
                        </div>
                        <div class="text-content font-serif"></div>
                    </div>
                </div>
            `;
            stream.insertAdjacentHTML('beforeend', agentHtml);
            
            const tree = document.getElementById(`tree-${agentContainerId}`);
            const toolContainer = tree.querySelector('.tool-container');
            const content = document.getElementById(agentContainerId).querySelector('.text-content');

            try {
                const response = await fetch(`${API_BASE}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: text,
                        history: conversation.slice(-16),
                        model: selectedModel,
                        attachments: []
                    })
                });
                const data = await response.json();
                if(!response.ok) {
                    throw new Error(data.message || 'Local backend request failed.');
                }

                const route = data.route || {};
                const model = data.model || {};
                const trace = data.trace || [];

                renderTrace(tree, toolContainer, route, model, trace);
                setProgressFromTrace(trace);
                updateProgress(0, 'done', trace[0]?.step || 'Analyze request context');
                updateProgress(1, 'done', trace[1]?.step || 'Select model');
                updateProgress(2, 'active', 'Generating response...');

                const reply = data.reply || '(The backend returned an empty response.)';
                await typeText(content, reply);
                updateProgress(2, 'done', trace[2]?.step || 'Generate response');
                document.getElementById('workflow-status').textContent = `Answered by ${model.display_name || model.id || 'local model'}`;
                conversation.push({ role: 'user', content: text });
                conversation.push({ role: 'assistant', content: reply });

                const compBar = document.getElementById('compaction-bar');
                compBar.classList.add('visible');
                await sleep(800);
                compBar.classList.remove('visible');
            } catch (error) {
                tree.classList.remove('hidden');
                toolContainer.insertAdjacentHTML('beforeend', `<div class="tool-block">[error] ${escapeHtml(error.message || String(error))}</div>`);
                await typeText(content, `Local backend error: ${error.message || error}`);
                updateProgress(0, 'done', 'Analyze request context');
                updateProgress(1, 'done', 'Select model');
                updateProgress(2, 'done', 'Generate response');
                document.getElementById('workflow-status').textContent = 'Backend error';
            }
        }

        // Utility: Sleep
        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        // Utility: Typewriter effect for realism
        async function typeText(element, text) {
            element.innerHTML = "";
            let htmlStr = escapeHtml(text).replace(/\n/g, "<br><br>");
            let currentStr = "";

            let i = 0;
            while(i < htmlStr.length) {
                let chunkSize = Math.floor(Math.random() * 5) + 2;
                currentStr += htmlStr.substring(i, i + chunkSize);
                element.innerHTML = currentStr;
                i += chunkSize;
                window.scrollTo(0, document.body.scrollHeight);
                await sleep(30);
            }
        }

        // Utility: Update Right Sidebar Progress
        function updateProgress(index, state, text) {
            const steps = document.querySelectorAll('.progress-step');
            const step = steps[index];
            if (!step) return;
            if(state === 'active') {
                step.innerHTML = `<div class="step-icon active"><span class="spinner" style="width:10px; height:10px; border-width:2px; border-color:var(--progress-blue); border-bottom-color:transparent;"></span></div><div class="step-text text-sm">${escapeHtml(text)}</div>`;
                document.getElementById('workflow-status').textContent = text;
            } else if (state === 'done') {
                step.innerHTML = `<div class="step-icon done">✓</div><div class="step-text done text-sm">${escapeHtml(text)}</div>`;
            }
        }

        // Trigger prompt via Enter key
        document.getElementById('prompt-input').addEventListener('keydown', function(e) {
            if(e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitPrompt();
            }
        });

        // --- 6. Real local application state (replaces sample sidebar content) ---
        let activeSessionId = null;
        let pendingAttachments = [];
        const api = (path, options = {}) => fetch(`${API_BASE}${path}`, {
            headers: {'Content-Type': 'application/json', ...(options.headers || {})}, ...options
        }).then(async response => {
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || data.error || 'Local request failed.');
            return data;
        });
        function historyButton(session) {
            const button = document.createElement('button'); button.textContent = session.title;
            button.title = 'Open this local chat';
            button.onclick = () => loadSession(session.id); return button;
        }
        function renderSessions(sessions) {
            const pinned = document.querySelectorAll('.chat-list')[0];
            const today = document.querySelectorAll('.chat-list')[1];
            const older = document.querySelectorAll('.chat-list')[2];
            [pinned, today, older].forEach(list => list.innerHTML = '');
            sessions.forEach((session, index) => {
                const target = session.pinned ? pinned : (index < 8 ? today : older);
                const item = document.createElement('li'); item.appendChild(historyButton(session)); target.appendChild(item);
            });
        }
        function renderFiles(files) {
            const pane = document.getElementById('panel-files'); pane.innerHTML = '';
            if (!files.length) pane.textContent = 'No files in this local project yet.';
            files.forEach(file => {
                const item = document.createElement('button'); item.className = 'file-tree-item';
                item.textContent = `${file.directory ? '📁' : '📄'} ${file.path}`;
                if (!file.directory) item.onclick = () => previewFile(file.path);
                pane.appendChild(item);
            });
        }
        async function previewFile(path) {
            const data = await api(`/api/files?path=${encodeURIComponent(path)}`);
            document.getElementById('prompt-input').value = `Please review the local file ${data.path}:\n\n${data.content.slice(0, 12000)}`;
            document.getElementById('prompt-input').focus();
        }
        async function loadSession(id) {
            const data = await api(`/api/sessions/${id}`); const session = data.session;
            activeSessionId = session.id; conversation.length = 0; document.getElementById('chat-stream').innerHTML = '';
            resetToHome();
            session.messages.forEach(message => {
                conversation.push({role: message.role, content: message.content});
                document.getElementById('chat-stream').insertAdjacentHTML('beforeend', `<div class="msg ${message.role === 'user' ? 'user' : 'agent'}"><div class="msg-bubble">${escapeHtml(message.content).replace(/\n/g, '<br>')}</div></div>`);
            });
            if (session.messages.length) { document.getElementById('home-view').classList.add('hidden'); document.getElementById('chat-view').style.display = 'flex'; }
        }
        async function bootstrap() {
            try {
                const data = await api('/api/bootstrap'); renderSessions(data.sessions); renderFiles(data.files);
                const badge = document.querySelector('.hardware-badge');
                badge.textContent = data.runtime_available ? 'Local Runtime Ready · Air-Gapped' : 'Local Runtime Missing';
                if (data.settings) {
                    document.querySelector('#settings-modal input').value = data.settings.name || '';
                    document.querySelector('#settings-modal textarea').value = data.settings.instructions || '';
                }
            } catch (error) { document.querySelector('.hardware-badge').textContent = 'Local backend unavailable'; }
        }
        const originalSubmitPrompt = submitPrompt;
        submitPrompt = async function() {
            const input = document.getElementById('prompt-input'); const text = input.value.trim();
            if (!text) return;
            const originalFetch = window.fetch;
            window.fetch = (url, options = {}) => {
                if (String(url).endsWith('/api/chat')) {
                    const body = JSON.parse(options.body); body.session_id = activeSessionId; body.attachments = pendingAttachments;
                    options.body = JSON.stringify(body);
                }
                return originalFetch(url, options).then(async response => {
                    if (String(url).endsWith('/api/chat')) {
                        const copy = response.clone(); copy.json().then(data => { if (data.session) { activeSessionId = data.session.id; bootstrap(); } });
                    }
                    return response;
                });
            };
            try { await originalSubmitPrompt(); } finally { window.fetch = originalFetch; pendingAttachments = []; }
        };
        const fileInput = Object.assign(document.createElement('input'), {type: 'file', multiple: true, accept: 'image/*,.pdf,.docx,.pptx,.xlsx,.xml,.rtf,.txt,.md,.py,.js,.ts,.html,.css,.json,.csv,.yaml,.yml,.sql'});
        fileInput.style.display = 'none'; document.body.appendChild(fileInput);
        fileInput.onchange = async () => {
            pendingAttachments = await Promise.all([...fileInput.files].slice(0,4).map(file => new Promise((resolve,reject) => { const reader = new FileReader(); reader.onload=()=>resolve({name:file.name,type:file.type,data_url:reader.result}); reader.onerror=reject; reader.readAsDataURL(file); })));
            document.getElementById('workflow-status').textContent = `${pendingAttachments.length} local file(s) attached`;
        };
        document.querySelector('#attach-dropdown button').onclick = () => { fileInput.click(); closeAllDropdowns(); };
        [...document.querySelectorAll('.action-menu button')].forEach(button => {
            if (button.textContent.includes('Projects')) button.onclick = () => document.getElementById('new-project-modal').showModal();
            if (button.textContent.includes('Artifacts')) button.onclick = () => document.getElementById('panel-files').scrollIntoView({behavior:'smooth'});
            if (button.textContent.includes('Customize')) button.onclick = () => document.getElementById('settings-modal').showModal();
        });
        document.querySelector('#settings-modal .btn-primary').onclick = async () => {
            const fields = document.querySelectorAll('#settings-modal input, #settings-modal textarea, #settings-modal select');
            await api('/api/settings', {method:'POST', body:JSON.stringify({name:fields[0].value,instructions:fields[1].value,font:fields[2].value})}); document.getElementById('settings-modal').close();
        };
        document.querySelector('#new-project-modal .btn-primary').onclick = async () => {
            const name = document.querySelector('#new-project-modal input').value;
            const data = await api('/api/projects',{method:'POST',body:JSON.stringify({name})}); document.getElementById('new-project-modal').close(); renderFiles([]); await bootstrap();
        };
        bootstrap();

        // Single UI source of truth for mode, active session and selected model.
        const uiState = { mode: 'cowork', model: 'auto', workflow: [], memory: [] };
        function recordWorkflow(event) {
            uiState.workflow.push({at: new Date(), ...event});
            const steps = document.getElementById('workflow-steps');
            steps.innerHTML = '';
            uiState.workflow.slice(-30).forEach((event, index) => {
                const row = document.createElement('div'); row.className = 'progress-step';
                row.innerHTML = `<div class="step-icon ${event.status === 'error' ? 'pending' : 'done'}">${event.status === 'error' ? '!' : '✓'}</div><div class="step-text text-sm"><strong>${escapeHtml(event.step)}</strong><br><span class="text-muted">${escapeHtml(event.detail || '')}</span></div>`;
                steps.appendChild(row);
            });
        }
        function renderMemory() {
            const pane = document.getElementById('panel-memory');
            pane.innerHTML = '<div class="text-xs font-semibold mb-2 text-muted uppercase">Active context</div>';
            const values = [...new Set(uiState.memory)].slice(-8);
            if (!values.length) { pane.insertAdjacentHTML('beforeend', '<div class="text-xs text-muted">Context will appear as you work locally.</div>'); return; }
            values.forEach((value, index) => pane.insertAdjacentHTML('beforeend', `<div class="progress-step"><div class="step-icon done">${index + 1}</div><div class="text-sm">${escapeHtml(value)}</div></div>`));
        }
        function setMode(mode) {
            uiState.mode = mode; uiState.model = mode === 'cowork' ? 'auto' : selectedModel === 'auto' ? 'general' : selectedModel;
            selectedModel = uiState.model;
            document.querySelectorAll('.mode-toggle button').forEach(button => button.classList.toggle('active', button.textContent.toLowerCase().includes(mode === 'cowork' ? 'cowork' : 'model hub')));
            const selector = document.getElementById('model-btn'); selector.style.display = mode === 'cowork' ? 'none' : 'flex';
            document.getElementById('active-model-name').textContent = mode === 'cowork' ? 'CounciLLM Router' : (selectedModel === 'general' ? 'Qwen3 General' : document.getElementById('active-model-name').textContent);
            uiState.memory.push(mode === 'cowork' ? 'Cowork routing is active.' : `Model Hub is active with ${document.getElementById('active-model-name').textContent}.`);
            renderMemory(); recordWorkflow({step: mode === 'cowork' ? 'Cowork mode enabled' : 'Model Hub enabled', detail: 'Conversation state preserved.', status: 'done'});
        }
        document.querySelectorAll('.mode-toggle button')[0].onclick = () => setMode('cowork');
        document.querySelectorAll('.mode-toggle button')[1].onclick = () => setMode('hub');
        const previousSetModel = setModel;
        setModel = (model, label) => { previousSetModel(model, label); uiState.model = model; if (uiState.mode === 'hub') { uiState.memory.push(`Selected local model: ${label}.`); renderMemory(); } };
        const originalLiveSubmit = submitPrompt;
        submitPrompt = async function () {
            selectedModel = uiState.mode === 'cowork' ? 'auto' : uiState.model;
            const prompt = document.getElementById('prompt-input').value.trim();
            if (prompt) { uiState.memory.push(`Current request: ${prompt.slice(0, 100)}`); renderMemory(); recordWorkflow({step:'Request submitted', detail: uiState.mode === 'cowork' ? 'Routing through the local council.' : `Using ${document.getElementById('active-model-name').textContent}.`, status:'done'}); }
            await originalLiveSubmit();
        };
        function updateGreeting() {
            const hour = new Date().getHours();
            document.getElementById('greeting-text').textContent = hour < 5 ? 'Working late?' : hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
        }
        updateGreeting(); setInterval(updateGreeting, 60 * 1000);
        const sendButton = document.getElementById('submit-btn');
        function updateSendState() { const active = Boolean(document.getElementById('prompt-input').value.trim()); sendButton.disabled = !active; sendButton.style.background = active ? 'var(--accent-coral)' : 'var(--border-default)'; sendButton.style.cursor = active ? 'pointer' : 'not-allowed'; }
        document.getElementById('prompt-input').addEventListener('input', updateSendState); updateSendState();

        // History actions use the existing persistent session API; no duplicate list.
        renderSessions = function(sessions) {
            const lists = [document.getElementById('pinned-sessions'), document.getElementById('recent-sessions'), document.getElementById('older-sessions')];
            lists.forEach(list => list.innerHTML = '');
            const active = sessions.filter(session => !session.archived);
            const archived = sessions.filter(session => session.archived);
            document.querySelectorAll('.chat-group-header span')[2].textContent = archived.length ? `Archived (${archived.length})` : 'Archived';
            const add = (session, list) => {
                const item = document.createElement('li'); item.className = 'history-row';
                item.appendChild(historyButton(session));
                const actions = document.createElement('button'); actions.className = 'history-actions'; actions.textContent = '⋯'; actions.title = 'Chat actions';
                actions.onclick = event => { event.stopPropagation(); showChatActions(session, actions); };
                item.appendChild(actions); list.appendChild(item);
            };
            active.filter(s => s.pinned).forEach(s => add(s, lists[0]));
            active.filter(s => !s.pinned).forEach(s => add(s, lists[1]));
            archived.forEach(s => add(s, lists[2]));
        };
        function showChatActions(session, anchor) {
            closeAllDropdowns(); const menu = document.createElement('div'); menu.className = 'dropdown show';
            menu.style.cssText = 'display:flex;position:fixed;min-width:150px;z-index:300;'; const box = anchor.getBoundingClientRect(); menu.style.left = `${box.left - 126}px`; menu.style.top = `${box.bottom + 4}px`;
            const action = (label, work) => { const button=document.createElement('button'); button.className='dropdown-item'; button.textContent=label; button.onclick=async()=>{ menu.remove(); await work(); await bootstrap(); }; menu.appendChild(button); };
            action(session.pinned ? 'Unpin chat' : 'Pin chat', () => api(`/api/sessions/${session.id}`, {method:'PATCH',body:JSON.stringify({pinned:!session.pinned})}));
            action(session.archived ? 'Restore chat' : 'Archive chat', () => api(`/api/sessions/${session.id}`, {method:'PATCH',body:JSON.stringify({archived:!session.archived})}));
            action('Delete chat', async () => { if (confirm(`Delete “${session.title}”? This cannot be undone.`)) { await api(`/api/sessions/${session.id}`, {method:'DELETE'}); if (activeSessionId === session.id) resetToHome(); } });
            document.body.appendChild(menu); setTimeout(()=>document.addEventListener('click',()=>menu.remove(),{once:true}),0);
        }
        function notify(text) { document.getElementById('workflow-status').textContent = text; }
        async function copyText(text) { try { await navigator.clipboard.writeText(text); notify('Copied to clipboard'); } catch { notify('Copy is unavailable in this browser.'); } }
        function decorateMessages() {
            document.querySelectorAll('#chat-stream .msg').forEach(message => {
                if (message.querySelector('.message-actions')) return;
                const text = message.querySelector('.msg-bubble')?.innerText || ''; const actions=document.createElement('div'); actions.className='message-actions';
                const add=(label,fn)=>{const button=document.createElement('button');button.textContent=label;button.onclick=fn;actions.appendChild(button);}; add('Copy',()=>copyText(text));
                if(message.classList.contains('user')) add('Edit',()=>{document.getElementById('prompt-input').value=text;updateSendState();document.getElementById('prompt-input').focus();});
                else { add('Retry',()=>{document.getElementById('prompt-input').value=conversation.filter(x=>x.role==='user').at(-1)?.content||'';updateSendState();submitPrompt();}); add('Try another model',()=>{setMode('hub');document.getElementById('model-btn').click();}); }
                message.appendChild(actions);
            });
        }
        const liveSubmitWithActions = submitPrompt;
        submitPrompt = async function() { await liveSubmitWithActions(); decorateMessages(); };
        const chips = document.createElement('div'); chips.id='attachment-chips'; document.getElementById('main-input-wrapper').prepend(chips);
        function renderAttachmentChips() { chips.innerHTML=''; pendingAttachments.forEach((file,index)=>{const chip=document.createElement('span');chip.className='attachment-chip';chip.innerHTML=`${file.type.startsWith('image/')?'🖼':'📄'} ${escapeHtml(file.name)} <button title="Remove">×</button>`;chip.querySelector('button').onclick=()=>{pendingAttachments.splice(index,1);renderAttachmentChips();};chips.appendChild(chip);}); }
        const priorFileChange=fileInput.onchange; fileInput.onchange=async()=>{await priorFileChange();renderAttachmentChips();};
        const priorSubmitForChips=submitPrompt; submitPrompt=async function(){await priorSubmitForChips();renderAttachmentChips();};
        document.querySelectorAll('#profile-dropdown button').forEach(button => {
            if (button.textContent.includes('Language')) { button.onclick=()=>{ closeAllDropdowns(); const language=prompt('Choose UI language: English, Hindi, or Spanish', document.querySelector('#settings-modal select')?.value || 'English'); if(language && ['English','Hindi','Spanish'].includes(language)) api('/api/settings',{method:'POST',body:JSON.stringify({language})}).then(()=>notify(`Language saved: ${language}`)); }; }
            if (button.textContent.includes('Add Local Models')) { button.remove(); }
        });
        document.getElementById('menu-btn').onclick = () => document.getElementById('left-sidebar').classList.toggle('hidden');
        // Replace the original design placeholders with actual current local state.
        renderMemory();
    