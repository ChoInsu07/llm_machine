class ChatPanel {
  constructor(onFileCreated) {
    this.messagesEl = document.getElementById('chat-messages');
    this.inputEl = document.getElementById('chat-input');
    this.sendBtn = document.getElementById('chat-send');
    this.planToggle = document.getElementById('plan-toggle');
    this.onFileCreated = onFileCreated;

    this.sendBtn.addEventListener('click', () => this.send());
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    });
  }

  async send() {
    const text = this.inputEl.value.trim();
    if (!text) return;

    this.addMessage('user', text);
    this.inputEl.value = '';
    this.sendBtn.disabled = true;

    const statusMsg = this.addMessage('assistant', '');

    try {
      const res = await window.api.chat(text, this.planToggle.checked);

      statusMsg.remove();

      if (res.events) {
        for (const ev of res.events) {
          this.renderEvent(ev);
        }
      }

      if (res.files && res.files.length > 0) {
        this.addMessage('tool', `📁 Files created/modified: ${res.files.join(', ')}`);
        if (this.onFileCreated) {
          for (const f of res.files) {
            this.onFileCreated(f);
          }
        }
      }

      if (res.result) {
        this.addMessage('assistant', `✅ ${res.result}`);
      }
    } catch (err) {
      statusMsg.querySelector('.msg-content').textContent = `Error: ${err.message}`;
      statusMsg.querySelector('.msg-content').style.color = '#f44747';
    } finally {
      this.sendBtn.disabled = false;
      this.inputEl.focus();
    }
  }

  renderEvent(ev) {
    switch (ev.type) {
      case 'plan':
        this.renderPlan(ev.steps);
        break;
      case 'think':
        this.addMessage('assistant', ev.content);
        break;
      case 'tool':
        this.addMessage('tool', `🔧 ${ev.name}(${JSON.stringify(ev.args, null, 1)})`);
        break;
      case 'result':
        if (ev.success) {
          this.addMessage('tool', `✅ ${ev.output}`);
        } else {
          this.addMessage('error', `❌ ${ev.error || ev.output}`);
        }
        break;
      case 'finish':
        this.addMessage('assistant', `🏁 ${ev.content}`);
        break;
      case 'file':
        this.addMessage('tool', `📄 ${ev.action} → ${ev.path}`);
        break;
    }
  }

  renderPlan(steps) {
    const lines = steps.map((s, i) => `${i + 1}. ${s.description} [${s.tool}]`).join('\n');
    const msg = this.addMessage('assistant', `📋 Plan:\n${lines}`);
    return msg;
  }

  addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const roleLabel = document.createElement('div');
    roleLabel.className = 'msg-role';
    roleLabel.textContent = role;
    div.appendChild(roleLabel);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'msg-content';
    contentDiv.textContent = content;
    contentDiv.style.whiteSpace = 'pre-wrap';
    div.appendChild(contentDiv);

    this.messagesEl.appendChild(div);
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;

    return div;
  }

  addToolMessage(content) {
    return this.addMessage('tool', content);
  }
}
