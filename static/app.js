/* ═════════════════════════════════════════════════════════════
   AgentFlow Dashboard — Application Logic
   ═════════════════════════════════════════════════════════════ */

const API = '';  // Same origin

// ─── State ──────────────────────────────────────────────────
let currentView = 'chat';
let searchTimeout = null;

// ─── Initialize ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadSystemStatus();
    setupChatInput();

    // Refresh status every 30s
    setInterval(loadSystemStatus, 30000);
});

// ─── Navigation ─────────────────────────────────────────────
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
        });
    });
}

function switchView(view) {
    currentView = view;

    // Update nav
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-view="${view}"]`).classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${view}`).classList.add('active');

    // Update header
    const titles = {
        chat: ['AI Chat', 'Talk to your agents naturally'],
        tasks: ['Task Manager', 'Track and manage your tasks'],
        calendar: ['Calendar', 'Manage your schedule and events'],
        notes: ['Notes', 'Organize your knowledge and ideas'],
        workflows: ['Workflows', 'Automate multi-step processes'],
        agents: ['Agents', 'View agent capabilities and activity'],
    };

    const [title, subtitle] = titles[view] || ['', ''];
    document.getElementById('page-title').textContent = title;
    document.getElementById('page-subtitle').textContent = subtitle;

    // Load data for view
    switch (view) {
        case 'tasks': loadTasks(); break;
        case 'calendar': loadEvents(); break;
        case 'notes': loadNotes(); break;
        case 'workflows': loadWorkflows(); break;
        case 'agents': loadAgents(); break;
    }
}

// ─── API Helpers ────────────────────────────────────────────
async function apiGet(endpoint) {
    try {
        const res = await fetch(`${API}${endpoint}`);
        return await res.json();
    } catch (e) {
        showToast('API Error: ' + e.message, 'error');
        return null;
    }
}

async function apiPost(endpoint, data) {
    try {
        const res = await fetch(`${API}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await res.json();
    } catch (e) {
        showToast('API Error: ' + e.message, 'error');
        return null;
    }
}

async function apiPut(endpoint, data) {
    try {
        const res = await fetch(`${API}${endpoint}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await res.json();
    } catch (e) {
        showToast('API Error: ' + e.message, 'error');
        return null;
    }
}

async function apiDelete(endpoint) {
    try {
        const res = await fetch(`${API}${endpoint}`, { method: 'DELETE' });
        return await res.json();
    } catch (e) {
        showToast('API Error: ' + e.message, 'error');
        return null;
    }
}

// ─── System Status ──────────────────────────────────────────
async function loadSystemStatus() {
    const data = await apiGet('/api/status');
    if (!data) return;

    const summary = data.data_summary || {};
    document.querySelector('#stat-tasks .stat-count').textContent = summary.total_tasks || 0;
    document.querySelector('#stat-events .stat-count').textContent = summary.total_events || 0;
    document.querySelector('#stat-notes .stat-count').textContent = summary.total_notes || 0;
}

// ─── Chat ───────────────────────────────────────────────────
function setupChatInput() {
    const input = document.getElementById('chat-input');
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    addChatMessage(message, 'user');

    // Show thinking indicator
    const thinking = addThinkingIndicator();

    const data = await apiPost('/api/chat', { message });
    thinking.remove();

    if (!data) {
        addChatMessage('Sorry, I encountered an error. Please try again.', 'agent');
        return;
    }

    // Format agent response
    formatAgentResponse(data);
    loadSystemStatus();
}

function sendQuickAction(message) {
    document.getElementById('chat-input').value = message;
    // Remove welcome on first interaction
    const welcome = document.querySelector('.chat-welcome');
    if (welcome) welcome.remove();
    sendChatMessage();
}

function addChatMessage(text, type) {
    const container = document.getElementById('chat-messages');
    const welcome = container.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    const div = document.createElement('div');
    div.className = `chat-msg ${type}`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function addThinkingIndicator() {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-thinking';
    div.innerHTML = `
        <div class="thinking-dots"><span></span><span></span><span></span></div>
        Agents processing...
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function formatAgentResponse(data) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-msg agent';

    let html = '';

    if (data.success === false) {
        html += `<p>${data.message || data.error || 'Request failed'}</p>`;
        if (data.suggestions) {
            html += '<div style="margin-top:10px;font-size:12px;color:var(--text-muted)">';
            html += '<strong>Try:</strong><br>';
            data.suggestions.forEach(s => {
                html += `<span style="cursor:pointer;color:var(--accent-primary)" onclick="sendQuickAction('${s.replace(/'/g, "\\'")}')">${s}</span><br>`;
            });
            html += '</div>';
        }
    } else {
        const agent = data.agent_used || '';
        const action = data.action_taken || '';

        if (agent) {
            html += `<span class="msg-agent-tag ${agent}">${agent} Agent → ${action}</span>`;
        }

        const result = data.result || {};
        const resultData = result.data;

        if (Array.isArray(resultData)) {
            if (resultData.length === 0) {
                html += '<p>No items found.</p>';
            } else {
                html += `<p>Found ${resultData.length} item(s):</p>`;
                html += '<div class="msg-data">';
                resultData.forEach(item => {
                    const title = item.title || item.name || 'Untitled';
                    const status = item.status || '';
                    const priority = item.priority || '';
                    let line = `• ${title}`;
                    if (status) line += ` [${status}]`;
                    if (priority) line += ` (${priority})`;
                    if (item.start_time) line += ` @ ${item.start_time}`;
                    html += line + '\n';
                });
                html += '</div>';
            }
        } else if (resultData && typeof resultData === 'object') {
            const title = resultData.title || resultData.name || '';
            html += `<p>✅ ${action === 'create' || action === 'create_task' || action === 'create_event' || action === 'create_note' ? 'Created' : 'Done'}: <strong>${title}</strong></p>`;
            if (resultData.id) html += `<span style="font-size:11px;color:var(--text-muted)">ID: ${resultData.id}</span>`;

            // Show warnings if any
            if (resultData.warnings) {
                html += '<div style="margin-top:8px;padding:8px;background:var(--amber-dim);border-radius:6px;font-size:12px;color:var(--amber)">';
                resultData.warnings.forEach(w => html += `⚠️ ${w}<br>`);
                html += '</div>';
            }
        } else {
            html += `<p>${JSON.stringify(resultData, null, 2)}</p>`;
        }
    }

    div.innerHTML = html;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ─── Tasks ──────────────────────────────────────────────────
async function loadTasks() {
    const status = document.getElementById('task-status-filter').value;
    const priority = document.getElementById('task-priority-filter').value;

    let endpoint = '/api/tasks?';
    if (status) endpoint += `status=${status}&`;
    if (priority) endpoint += `priority=${priority}&`;

    const data = await apiGet(endpoint);
    const grid = document.getElementById('tasks-grid');

    if (!data || !data.data || data.data.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
                <h3>No tasks yet</h3>
                <p>Create your first task to get started</p>
            </div>`;
        return;
    }

    grid.innerHTML = data.data.map(task => {
        const tags = tryParse(task.tags, []);
        return `
        <div class="card">
            <div class="card-header">
                <span class="card-title">${escHtml(task.title)}</span>
                <span class="badge ${task.priority}">${task.priority}</span>
            </div>
            ${task.description ? `<p class="card-desc">${escHtml(task.description)}</p>` : ''}
            <div class="card-meta">
                <span class="badge ${task.status}">${task.status.replace('_', ' ')}</span>
                ${task.due_date ? `<span class="badge category">Due: ${task.due_date}</span>` : ''}
                ${tags.map(t => `<span class="badge category">${escHtml(t)}</span>`).join('')}
            </div>
            <div class="card-actions">
                ${task.status !== 'completed' ? `<button class="btn-sm success" onclick="completeTask(${task.id})">✓ Complete</button>` : ''}
                <button class="btn-sm" onclick="showEditTaskModal(${task.id})">Edit</button>
                <button class="btn-sm danger" onclick="deleteTask(${task.id})">Delete</button>
            </div>
        </div>`;
    }).join('');
}

async function completeTask(id) {
    await apiPost(`/api/tasks/${id}/complete`);
    showToast('Task completed!', 'success');
    loadTasks();
    loadSystemStatus();
}

async function deleteTask(id) {
    await apiDelete(`/api/tasks/${id}`);
    showToast('Task deleted', 'success');
    loadTasks();
    loadSystemStatus();
}

function showCreateTaskModal() {
    showModal('Create Task', `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="form-task-title" placeholder="Task title">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="form-task-desc" placeholder="Optional description"></textarea>
        </div>
        <div class="form-group">
            <label>Priority</label>
            <select id="form-task-priority">
                <option value="low">Low</option>
                <option value="medium" selected>Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
            </select>
        </div>
        <div class="form-group">
            <label>Due Date</label>
            <input type="date" id="form-task-due">
        </div>
        <div class="form-group">
            <label>Tags (comma-separated)</label>
            <input type="text" id="form-task-tags" placeholder="e.g., frontend, bug">
        </div>
        <div class="form-actions">
            <button class="btn-cancel" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="submitCreateTask()">Create Task</button>
        </div>
    `);
}

async function submitCreateTask() {
    const title = document.getElementById('form-task-title').value.trim();
    if (!title) { showToast('Title is required', 'error'); return; }

    const tags = document.getElementById('form-task-tags').value
        .split(',').map(t => t.trim()).filter(Boolean);

    await apiPost('/api/tasks', {
        title,
        description: document.getElementById('form-task-desc').value,
        priority: document.getElementById('form-task-priority').value,
        due_date: document.getElementById('form-task-due').value || null,
        tags: tags.length ? tags : null
    });

    closeModal();
    showToast('Task created!', 'success');
    loadTasks();
    loadSystemStatus();
}

async function showEditTaskModal(id) {
    const data = await apiGet(`/api/tasks/${id}`);
    if (!data || !data.data) return;
    const task = data.data;
    const tags = tryParse(task.tags, []);

    showModal('Edit Task', `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="form-task-title" value="${escAttr(task.title)}">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="form-task-desc">${escHtml(task.description || '')}</textarea>
        </div>
        <div class="form-group">
            <label>Status</label>
            <select id="form-task-status">
                <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>Pending</option>
                <option value="in_progress" ${task.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
                <option value="cancelled" ${task.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
            </select>
        </div>
        <div class="form-group">
            <label>Priority</label>
            <select id="form-task-priority">
                <option value="low" ${task.priority === 'low' ? 'selected' : ''}>Low</option>
                <option value="medium" ${task.priority === 'medium' ? 'selected' : ''}>Medium</option>
                <option value="high" ${task.priority === 'high' ? 'selected' : ''}>High</option>
                <option value="critical" ${task.priority === 'critical' ? 'selected' : ''}>Critical</option>
            </select>
        </div>
        <div class="form-group">
            <label>Due Date</label>
            <input type="date" id="form-task-due" value="${task.due_date || ''}">
        </div>
        <div class="form-group">
            <label>Tags (comma-separated)</label>
            <input type="text" id="form-task-tags" value="${tags.join(', ')}">
        </div>
        <div class="form-actions">
            <button class="btn-cancel" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="submitEditTask(${id})">Save Changes</button>
        </div>
    `);
}

async function submitEditTask(id) {
    const tags = document.getElementById('form-task-tags').value
        .split(',').map(t => t.trim()).filter(Boolean);

    await apiPut(`/api/tasks/${id}`, {
        title: document.getElementById('form-task-title').value.trim(),
        description: document.getElementById('form-task-desc').value,
        status: document.getElementById('form-task-status').value,
        priority: document.getElementById('form-task-priority').value,
        due_date: document.getElementById('form-task-due').value || null,
        tags: tags.length ? tags : null
    });

    closeModal();
    showToast('Task updated!', 'success');
    loadTasks();
    loadSystemStatus();
}

// ─── Events ─────────────────────────────────────────────────
async function loadEvents() {
    const data = await apiGet('/api/events');
    const grid = document.getElementById('events-list');

    if (!data || !data.data || data.data.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                <h3>No events scheduled</h3>
                <p>Create your first event to get started</p>
            </div>`;
        return;
    }

    grid.innerHTML = data.data.map(event => {
        const attendees = tryParse(event.attendees, []);
        return `
        <div class="card">
            <div class="card-header">
                <span class="card-title">${escHtml(event.title)}</span>
            </div>
            ${event.description ? `<p class="card-desc">${escHtml(event.description)}</p>` : ''}
            <div class="card-meta">
                <span class="badge in_progress">🕐 ${formatDateTime(event.start_time)}</span>
                ${event.end_time ? `<span class="badge category">→ ${formatDateTime(event.end_time)}</span>` : ''}
                ${event.location ? `<span class="badge category">📍 ${escHtml(event.location)}</span>` : ''}
                ${attendees.map(a => `<span class="badge low">👤 ${escHtml(a)}</span>`).join('')}
            </div>
            <div class="card-actions">
                <button class="btn-sm" onclick="showEditEventModal(${event.id})">Edit</button>
                <button class="btn-sm danger" onclick="deleteEvent(${event.id})">Delete</button>
            </div>
        </div>`;
    }).join('');
}

async function deleteEvent(id) {
    await apiDelete(`/api/events/${id}`);
    showToast('Event deleted', 'success');
    loadEvents();
    loadSystemStatus();
}

function showCreateEventModal() {
    showModal('Create Event', `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="form-event-title" placeholder="Event title">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="form-event-desc" placeholder="Optional description"></textarea>
        </div>
        <div class="form-group">
            <label>Start Time</label>
            <input type="datetime-local" id="form-event-start">
        </div>
        <div class="form-group">
            <label>End Time</label>
            <input type="datetime-local" id="form-event-end">
        </div>
        <div class="form-group">
            <label>Location</label>
            <input type="text" id="form-event-location" placeholder="Optional location">
        </div>
        <div class="form-group">
            <label>Attendees (comma-separated)</label>
            <input type="text" id="form-event-attendees" placeholder="e.g., Alice, Bob">
        </div>
        <div class="form-actions">
            <button class="btn-cancel" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="submitCreateEvent()">Create Event</button>
        </div>
    `);
}

async function submitCreateEvent() {
    const title = document.getElementById('form-event-title').value.trim();
    const start = document.getElementById('form-event-start').value;
    if (!title || !start) { showToast('Title and start time are required', 'error'); return; }

    const attendees = document.getElementById('form-event-attendees').value
        .split(',').map(t => t.trim()).filter(Boolean);

    await apiPost('/api/events', {
        title,
        description: document.getElementById('form-event-desc').value,
        start_time: start,
        end_time: document.getElementById('form-event-end').value || null,
        location: document.getElementById('form-event-location').value || '',
        attendees: attendees.length ? attendees : null
    });

    closeModal();
    showToast('Event created!', 'success');
    loadEvents();
    loadSystemStatus();
}

async function showEditEventModal(id) {
    const data = await apiGet(`/api/events/${id}`);
    if (!data || !data.data) return;
    const ev = data.data;
    const attendees = tryParse(ev.attendees, []);

    showModal('Edit Event', `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="form-event-title" value="${escAttr(ev.title)}">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="form-event-desc">${escHtml(ev.description || '')}</textarea>
        </div>
        <div class="form-group">
            <label>Start Time</label>
            <input type="datetime-local" id="form-event-start" value="${ev.start_time || ''}">
        </div>
        <div class="form-group">
            <label>End Time</label>
            <input type="datetime-local" id="form-event-end" value="${ev.end_time || ''}">
        </div>
        <div class="form-group">
            <label>Location</label>
            <input type="text" id="form-event-location" value="${escAttr(ev.location || '')}">
        </div>
        <div class="form-group">
            <label>Attendees (comma-separated)</label>
            <input type="text" id="form-event-attendees" value="${attendees.join(', ')}">
        </div>
        <div class="form-actions">
            <button class="btn-cancel" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="submitEditEvent(${id})">Save Changes</button>
        </div>
    `);
}

async function submitEditEvent(id) {
    const attendees = document.getElementById('form-event-attendees').value
        .split(',').map(t => t.trim()).filter(Boolean);

    await apiPut(`/api/events/${id}`, {
        title: document.getElementById('form-event-title').value.trim(),
        description: document.getElementById('form-event-desc').value,
        start_time: document.getElementById('form-event-start').value || null,
        end_time: document.getElementById('form-event-end').value || null,
        location: document.getElementById('form-event-location').value || '',
        attendees: attendees.length ? attendees : null
    });

    closeModal();
    showToast('Event updated!', 'success');
    loadEvents();
    loadSystemStatus();
}

// ─── Notes ──────────────────────────────────────────────────
async function loadNotes() {
    const category = document.getElementById('note-category-filter').value;
    const search = document.getElementById('note-search').value.trim();

    let endpoint = '/api/notes?';
    if (category) endpoint += `category=${category}&`;
    if (search) endpoint += `search=${encodeURIComponent(search)}&`;

    const data = await apiGet(endpoint);
    const grid = document.getElementById('notes-grid');

    if (!data || !data.data || data.data.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
                <h3>No notes found</h3>
                <p>Create your first note to get started</p>
            </div>`;
        return;
    }

    grid.innerHTML = data.data.map(note => {
        const tags = tryParse(note.tags, []);
        return `
        <div class="card">
            <div class="card-header">
                <span class="card-title">${note.pinned ? '📌 ' : ''}${escHtml(note.title)}</span>
                <span class="badge category">${note.category}</span>
            </div>
            ${note.content ? `<p class="card-desc">${escHtml(note.content).substring(0, 200)}${note.content.length > 200 ? '...' : ''}</p>` : ''}
            <div class="card-meta">
                ${tags.map(t => `<span class="badge low">${escHtml(t)}</span>`).join('')}
                <span style="font-size:11px;color:var(--text-muted)">${formatDateTime(note.updated_at)}</span>
            </div>
            <div class="card-actions">
                <button class="btn-sm" onclick="togglePinNote(${note.id}, ${note.pinned ? 'false' : 'true'})">${note.pinned ? '📌 Unpin' : '📌 Pin'}</button>
                <button class="btn-sm" onclick="showEditNoteModal(${note.id})">Edit</button>
                <button class="btn-sm danger" onclick="deleteNote(${note.id})">Delete</button>
            </div>
        </div>`;
    }).join('');
}

function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadNotes, 300);
}

async function togglePinNote(id, pin) {
    await apiPut(`/api/notes/${id}`, { pinned: pin });
    loadNotes();
}

async function deleteNote(id) {
    await apiDelete(`/api/notes/${id}`);
    showToast('Note deleted', 'success');
    loadNotes();
    loadSystemStatus();
}

function showCreateNoteModal() {
    showModal('Create Note', `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="form-note-title" placeholder="Note title">
        </div>
        <div class="form-group">
            <label>Content</label>
            <textarea id="form-note-content" placeholder="Write your note..." style="min-height:120px"></textarea>
        </div>
        <div class="form-group">
            <label>Category</label>
            <select id="form-note-category">
                <option value="general">General</option>
                <option value="meeting">Meeting</option>
                <option value="project">Project</option>
                <option value="idea">Idea</option>
                <option value="reference">Reference</option>
            </select>
        </div>
        <div class="form-group">
            <label>Tags (comma-separated)</label>
            <input type="text" id="form-note-tags" placeholder="e.g., important, review">
        </div>
        <div class="form-actions">
            <button class="btn-cancel" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="submitCreateNote()">Create Note</button>
        </div>
    `);
}

async function submitCreateNote() {
    const title = document.getElementById('form-note-title').value.trim();
    if (!title) { showToast('Title is required', 'error'); return; }

    const tags = document.getElementById('form-note-tags').value
        .split(',').map(t => t.trim()).filter(Boolean);

    await apiPost('/api/notes', {
        title,
        content: document.getElementById('form-note-content').value,
        category: document.getElementById('form-note-category').value,
        tags: tags.length ? tags : null
    });

    closeModal();
    showToast('Note created!', 'success');
    loadNotes();
    loadSystemStatus();
}

async function showEditNoteModal(id) {
    const data = await apiGet(`/api/notes/${id}`);
    if (!data || !data.data) return;
    const note = data.data;
    const tags = tryParse(note.tags, []);

    showModal('Edit Note', `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="form-note-title" value="${escAttr(note.title)}">
        </div>
        <div class="form-group">
            <label>Content</label>
            <textarea id="form-note-content" style="min-height:120px">${escHtml(note.content || '')}</textarea>
        </div>
        <div class="form-group">
            <label>Category</label>
            <select id="form-note-category">
                <option value="general" ${note.category === 'general' ? 'selected' : ''}>General</option>
                <option value="meeting" ${note.category === 'meeting' ? 'selected' : ''}>Meeting</option>
                <option value="project" ${note.category === 'project' ? 'selected' : ''}>Project</option>
                <option value="idea" ${note.category === 'idea' ? 'selected' : ''}>Idea</option>
                <option value="reference" ${note.category === 'reference' ? 'selected' : ''}>Reference</option>
            </select>
        </div>
        <div class="form-group">
            <label>Tags (comma-separated)</label>
            <input type="text" id="form-note-tags" value="${tags.join(', ')}">
        </div>
        <div class="form-actions">
            <button class="btn-cancel" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="submitEditNote(${id})">Save Changes</button>
        </div>
    `);
}

async function submitEditNote(id) {
    const tags = document.getElementById('form-note-tags').value
        .split(',').map(t => t.trim()).filter(Boolean);

    await apiPut(`/api/notes/${id}`, {
        title: document.getElementById('form-note-title').value.trim(),
        content: document.getElementById('form-note-content').value,
        category: document.getElementById('form-note-category').value,
        tags: tags.length ? tags : null
    });

    closeModal();
    showToast('Note updated!', 'success');
    loadNotes();
    loadSystemStatus();
}

// ─── Workflows ──────────────────────────────────────────────
async function loadWorkflows() {
    // Load templates
    const templates = await apiGet('/api/workflows/templates/list');
    const templatesGrid = document.getElementById('workflow-templates');

    const templateIcons = {
        daily_standup: '☀️',
        project_setup: '🚀',
        weekly_review: '📊',
        meeting_prep: '📋'
    };

    if (templates && templates.data) {
        const tmpl = templates.data;
        templatesGrid.innerHTML = Object.entries(tmpl).map(([key, val]) => `
            <div class="template-card" onclick="createFromTemplate('${key}')">
                <div class="template-icon">${templateIcons[key] || '⚡'}</div>
                <div class="template-name">${escHtml(val.name)}</div>
                <div class="template-desc">${escHtml(val.description)}</div>
                <div class="template-steps">${val.step_count} steps</div>
            </div>
        `).join('');
    }

    // Load existing workflows
    const data = await apiGet('/api/workflows');
    const list = document.getElementById('workflows-list');

    if (!data || !data.data || data.data.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <h3>No workflows created</h3>
                <p>Use a template above or create a custom workflow</p>
            </div>`;
        return;
    }

    list.innerHTML = data.data.map(wf => {
        const steps = tryParse(wf.steps, []);
        const results = tryParse(wf.results, {});
        return `
        <div class="card">
            <div class="card-header">
                <span class="card-title">${escHtml(wf.name)}</span>
                <span class="badge ${wf.status}">${wf.status}</span>
            </div>
            ${wf.description ? `<p class="card-desc">${escHtml(wf.description)}</p>` : ''}
            <div class="card-meta">
                <span class="badge category">${steps.length} steps</span>
                <span class="badge low">Step ${wf.current_step}/${steps.length}</span>
            </div>
            <div class="card-actions">
                ${wf.status !== 'completed' && wf.status !== 'running' ?
                    `<button class="btn-sm success" onclick="executeWorkflow(${wf.id})">▶ Execute</button>` : ''}
                <button class="btn-sm" onclick="viewWorkflowDetails(${wf.id})">Details</button>
            </div>
        </div>`;
    }).join('');
}

async function createFromTemplate(templateName) {
    const data = await apiPost('/api/workflows/from-template', { template_name: templateName });
    if (data) {
        showToast('Workflow created from template!', 'success');
        loadWorkflows();
    }
}

async function executeWorkflow(id) {
    showToast('Executing workflow...', 'success');
    const data = await apiPost(`/api/workflows/${id}/execute`);
    if (data && data.data) {
        const result = data.data;
        showToast(`Workflow ${result.status}: ${result.completed_steps}/${result.total_steps} steps succeeded`, 'success');
    }
    loadWorkflows();
    loadSystemStatus();
}

async function viewWorkflowDetails(id) {
    const data = await apiGet(`/api/workflows/${id}`);
    if (!data || !data.data) return;
    const wf = data.data;
    const steps = tryParse(wf.steps, []);
    const results = tryParse(wf.results, {});
    const stepResults = results.step_results || [];

    let html = `<p style="color:var(--text-secondary);margin-bottom:16px">${escHtml(wf.description || '')}</p>`;
    html += `<div style="margin-bottom:12px"><span class="badge ${wf.status}">${wf.status}</span></div>`;

    html += '<div style="display:flex;flex-direction:column;gap:8px">';
    steps.forEach((step, i) => {
        const sr = stepResults[i];
        const statusIcon = sr ? (sr.status === 'success' ? '✅' : '❌') : '⏳';
        html += `<div class="log-entry">
            <span>${statusIcon}</span>
            <span class="log-agent">${step.agent}</span>
            <span class="log-action">${step.label || step.action}</span>
        </div>`;
    });
    html += '</div>';

    showModal(`Workflow: ${wf.name}`, html);
}

function showCreateWorkflowModal() {
    showModal('Create Custom Workflow', `
        <div class="form-group">
            <label>Name</label>
            <input type="text" id="form-wf-name" placeholder="Workflow name">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="form-wf-desc" placeholder="What does this workflow do?"></textarea>
        </div>
        <p style="color:var(--text-muted);font-size:12px;margin-bottom:16px">
            You can add steps after creation, or use a template for pre-configured workflows.
        </p>
        <div class="form-actions">
            <button class="btn-cancel" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="submitCreateWorkflow()">Create Workflow</button>
        </div>
    `);
}

async function submitCreateWorkflow() {
    const name = document.getElementById('form-wf-name').value.trim();
    if (!name) { showToast('Name is required', 'error'); return; }

    await apiPost('/api/workflows', {
        name,
        description: document.getElementById('form-wf-desc').value,
        steps: []
    });

    closeModal();
    showToast('Workflow created!', 'success');
    loadWorkflows();
}

// ─── Agents ─────────────────────────────────────────────────
async function loadAgents() {
    const data = await apiGet('/api/agents');
    const grid = document.getElementById('agents-grid');

    if (!data || !data.agents) return;

    const agentColors = {
        task: 'task-agent',
        calendar: 'calendar-agent',
        notes: 'notes-agent',
        workflow: 'workflow-agent'
    };

    const agentIcons = {
        task: '✅',
        calendar: '📅',
        notes: '📝',
        workflow: '⚡'
    };

    grid.innerHTML = Object.entries(data.agents).map(([key, agent]) => `
        <div class="agent-card ${agentColors[key] || ''}">
            <div style="font-size:28px;margin-bottom:12px">${agentIcons[key] || '🤖'}</div>
            <div class="agent-name">${escHtml(agent.name)}</div>
            <div class="agent-desc">${escHtml(agent.description)}</div>
            <div class="tool-list">
                ${Object.entries(agent.tools || {}).map(([tool, desc]) =>
                    `<span class="tool-tag" title="${escAttr(desc)}">${tool}</span>`
                ).join('')}
            </div>
        </div>
    `).join('');

    // Load logs
    const logsData = await apiGet('/api/logs?limit=20');
    const logsContainer = document.getElementById('agent-logs');

    if (!logsData || !logsData.data || logsData.data.length === 0) {
        logsContainer.innerHTML = '<div class="empty-state"><p>No agent activity yet</p></div>';
        return;
    }

    logsContainer.innerHTML = logsData.data.map(log => `
        <div class="log-entry">
            <div class="log-status ${log.status}"></div>
            <span class="log-agent">${escHtml(log.agent_name)}</span>
            <span class="log-action">${escHtml(log.action)}</span>
            <span class="log-time">${formatDateTime(log.timestamp)}</span>
        </div>
    `).join('');
}

// ─── Modal ──────────────────────────────────────────────────
function showModal(title, bodyHtml) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHtml;
    document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

// ─── Toast ──────────────────────────────────────────────────
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// ─── Utilities ──────────────────────────────────────────────
function escHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escAttr(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function tryParse(str, fallback) {
    if (Array.isArray(str) || (typeof str === 'object' && str !== null)) return str;
    try {
        return JSON.parse(str);
    } catch {
        return fallback;
    }
}

function formatDateTime(str) {
    if (!str) return '';
    try {
        const d = new Date(str);
        if (isNaN(d.getTime())) return str;
        return d.toLocaleDateString('en-US', {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    } catch {
        return str;
    }
}
