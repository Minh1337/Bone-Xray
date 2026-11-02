'use strict';

const form = document.getElementById('question-form');
const messages = document.getElementById('messages');
const input = document.getElementById('question');
const submit = document.getElementById('submit');
const clear = document.getElementById('clear-chat');
const liveStatus = document.getElementById('live-status');
const counter = document.getElementById('char-count');
const conversation = document.getElementById('conversation');
const initialWelcome = document.getElementById('welcome-block').cloneNode(true);
let activeController = null;
let conversationRevision = 0;
let stoppedByUser = false;
const stop = document.getElementById('stop-request');
const exportButton = document.getElementById('export-chat');
const sessionQuestions = document.getElementById('session-questions');
const sessionEmpty = document.getElementById('session-empty');
const transcript = [];
const chatHistory = [];
const chatMode = document.getElementById('chat-mode');

function boundedHistory() {
  const selected = [];
  let remaining = 12000;
  for (const item of chatHistory.slice(-12).reverse()) {
    const content = item.content.slice(0, Math.min(3000, remaining));
    if (!content) break;
    selected.unshift({ role: item.role, content });
    remaining -= content.length;
  }
  if (selected[0]?.role === 'assistant') selected.shift();
  return selected;
}
const providerLabels = { groq: 'Groq', openai: 'OpenAI' };
let providerLabel = 'AI';

async function loadProviderInfo() {
  try {
    const response = await fetch('/api/config', { cache: 'no-store' });
    if (!response.ok) return;
    const config = await response.json();
    providerLabel = providerLabels[config.provider] || 'AI';
    document.querySelectorAll('[data-provider-name]').forEach(node => { node.textContent = providerLabel; });
  } catch { /* Keep neutral AI labels when configuration cannot be read. */ }
}
loadProviderInfo();

function setBusy(busy) {
  submit.disabled = busy;
  submit.hidden = busy;
  stop.hidden = !busy;
  input.disabled = busy;
  chatMode.disabled = busy;
  form.toggleAttribute('aria-busy', busy);
  if (busy) form.setAttribute('aria-busy', 'true');
}

function announce(message) { liveStatus.textContent = message; }

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function icon(path) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  const shape = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  shape.setAttribute('d', path);
  svg.append(shape);
  return svg;
}

function assistantLabel(parent, label) {
  const row = element('div', 'message-label');
  const avatar = element('span', 'assistant-avatar');
  avatar.setAttribute('aria-hidden', 'true');
  avatar.append(icon('m12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4L12 3Z'));
  row.append(avatar, element('span', '', label));
  parent.append(row);
}

function bubble(kind, extraClass = '') {
  const node = element('article', `message ${kind}${extraClass ? ` ${extraClass}` : ''}`);
  node.setAttribute('aria-label', kind === 'user' ? 'Tin nhắn của bạn' : 'Phản hồi BoneScope');
  messages.append(node);
  return node;
}

function scrollToLatest() {
  conversation.scrollTop = conversation.scrollHeight;
}

function resetChat() {
  conversationRevision += 1;
  if (activeController) activeController.abort();
  activeController = null;
  messages.replaceChildren(initialWelcome.cloneNode(true));
  setBusy(false);
  transcript.length = 0;
  chatHistory.length = 0;
  sessionQuestions.replaceChildren();
  sessionEmpty.hidden = false;
  exportButton.disabled = true;
  setSidebar(false);
  input.value = '';
  resizeInput();
  updateCounter();
  announce('Đã bắt đầu cuộc trò chuyện mới.');
  input.focus();
  scrollToLatest();
}

clear.addEventListener('click', resetChat);
document.getElementById('mobile-new-chat').addEventListener('click', resetChat);
stop.addEventListener('click', () => {
  stoppedByUser = true;
  activeController?.abort();
});

function resizeInput() {
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
}

function updateCounter() {
  counter.textContent = `${input.value.length}/1000`;
  counter.classList.toggle('near-limit', input.value.length >= 900);
}

input.addEventListener('input', () => { resizeInput(); updateCounter(); });
messages.addEventListener('click', event => {
  const suggestion = event.target.closest('.suggestion');
  if (!suggestion) return;
  const text = suggestion.dataset.question;
  if (!text) return;
  input.value = text;
  resizeInput();
  updateCounter();
  form.requestSubmit();
});

function renderSource(hit, index) {
  const details = document.createElement('details');
  details.className = 'source-card';
  const summary = document.createElement('summary');
  summary.append(element('span', 'source-number', `S${index + 1}`));
  summary.append(element('span', 'source-title', hit.title || hit.source_id || `Nguồn ${index + 1}`));
  details.append(summary);

  const body = element('div', 'source-body');
  const sourceMeta = [hit.publisher, hit.section, hit.chunk_id].filter(Boolean).join(' · ');
  if (sourceMeta) body.append(element('p', 'source-meta', sourceMeta));
  body.append(element('p', 'source-text', hit.text || 'Không có nội dung đoạn nguồn.'));
  const provenance = [];
  if (hit.license) provenance.push(`Giấy phép: ${hit.license}`);
  if (hit.source_id) provenance.push(`Mã nguồn: ${hit.source_id}`);
  if (hit.text_sha256) provenance.push(`SHA-256 đoạn: ${hit.text_sha256}`);
  if (hit.source_sha256) provenance.push(`SHA-256 nguồn: ${hit.source_sha256}`);
  if (provenance.length) {
    const metadata = element('details', 'source-provenance');
    metadata.append(element('summary', '', 'Thông tin nguồn và đối chiếu dữ liệu'));
    metadata.append(element('p', '', provenance.join('\n')));
    body.append(metadata);
  }
  if (typeof hit.url === 'string' && /^https:\/\//i.test(hit.url)) {
    const link = element('a', 'source-link', 'Mở nguồn gốc ↗');
    link.href = hit.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    body.append(link);
  }
  details.append(body);
  return details;
}

// Build a small, safe Markdown subset with text nodes; AI output never becomes HTML.
function appendInline(parent, text, sourceCards) {
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[S(\d+)\])/g;
  let offset = 0;
  for (const match of text.matchAll(pattern)) {
    parent.append(document.createTextNode(text.slice(offset, match.index)));
    if (match[0].startsWith('**')) parent.append(element('strong', '', match[0].slice(2, -2)));
    else if (match[0].startsWith('`')) parent.append(element('code', '', match[0].slice(1, -1)));
    else {
      const source = sourceCards[Number(match[2]) - 1];
      if (source) {
        const citation = element('button', 'citation', match[0]);
        citation.type = 'button';
        citation.setAttribute('aria-label', `Đọc nguồn S${match[2]}`);
        citation.addEventListener('click', () => {
          source.open = true;
          source.scrollIntoView({ block: 'nearest', behavior: 'auto' });
          source.querySelector('summary').focus();
        });
        parent.append(citation);
      } else parent.append(document.createTextNode(match[0]));
    }
    offset = match.index + match[0].length;
  }
  parent.append(document.createTextNode(text.slice(offset)));
}

function renderAnswer(text, sourceCards) {
  const body = element('div', 'answer-copy');
  let paragraph = null;
  let list = null;
  for (const line of text.split('\n')) {
    if (!line.trim()) { paragraph = null; list = null; continue; }
    const heading = line.match(/^#{1,6}\s+(.+)$/);
    const bullet = line.match(/^\s*(?:[-*]\s+|\d+[.)]\s+)(.+)$/);
    if (heading) {
      const title = element('h3');
      appendInline(title, heading[1], sourceCards);
      body.append(title); paragraph = null; list = null;
    } else if (bullet) {
      const type = /^\s*\d/.test(line) ? 'ol' : 'ul';
      if (!list || list.localName !== type) { list = element(type); body.append(list); }
      const item = element('li'); appendInline(item, bullet[1], sourceCards); list.append(item); paragraph = null;
    } else {
      list = null;
      if (!paragraph) { paragraph = element('p'); body.append(paragraph); }
      else paragraph.append(document.createTextNode('\n'));
      appendInline(paragraph, line, sourceCards);
    }
  }
  return body;
}

function renderResult(data) {
  if (data.answer_ready !== false) throw new Error('Trạng thái kết quả không hợp lệ.');
  if (!['greeting', 'out_of_scope', 'insufficient_evidence', 'candidates_found', 'conversation'].includes(data.status)) throw new Error('Định dạng kết quả không hợp lệ.');
  if (data.status === 'candidates_found' && (!Array.isArray(data.passages) || !data.passages.length)) throw new Error('Định dạng nguồn không hợp lệ.');
  const answer = bubble('assistant');
  if (data.status === 'greeting') {
    assistantLabel(answer, 'BoneScope');
    answer.append(element('p', '', data.answer || 'Xin chào! Mình có thể giúp bạn tra cứu tài liệu.'));
    announce('Đã nhận phản hồi chào hỏi.');
    return;
  }
  if (data.status === 'out_of_scope') {
    assistantLabel(answer, 'Ngoài phạm vi tra cứu');
    answer.append(element('p', '', 'Câu hỏi này nằm ngoài phạm vi kho tài liệu hiện tại. Hãy thử hỏi về nội dung trong các tài liệu BoneScope.'));
    announce('Câu hỏi nằm ngoài phạm vi kho tài liệu.');
    return;
  }
  if (data.status === 'insufficient_evidence') {
    assistantLabel(answer, 'Chưa đủ nguồn');
    answer.append(element('p', '', 'Chưa tìm được bằng chứng phù hợp trong kho tài liệu. Bạn có thể thử diễn đạt lại hoặc hỏi về một chủ đề cụ thể hơn.'));
    announce('Chưa tìm được bằng chứng phù hợp.');
    return;
  }
  const isChat = data.status === 'conversation';
  if ((!isChat && data.status !== 'candidates_found') || !Array.isArray(data.passages) || (isChat ? data.passages.length !== 0 : !data.passages.length)) {
    throw new Error('Định dạng kết quả không hợp lệ.');
  }

  assistantLabel(answer, `${providerLabels[data.provider] || 'AI'} · ${isChat ? 'trò chuyện · kiến thức chung' : 'bản nháp chưa kiểm chứng'}`);
  const answerText = data.answer || 'Chưa tạo được câu trả lời.';
  const sourceCards = data.passages.map(renderSource);
  answer.append(renderAnswer(answerText, sourceCards));
  const caveat = element('p', 'answer-caveat');
  caveat.append(icon('M12 3.5 20 18H4L12 3.5Z M12 9v4m0 2.5h.01'));
  caveat.append(document.createTextNode('Nội dung do AI tạo, chưa được kiểm chứng tự động. Hãy đối chiếu từng ý với nguồn bên dưới.'));
  if (!isChat) answer.append(caveat);

  const sourceList = element('div', 'source-list');
  sourceList.setAttribute('aria-label', 'Nguồn tham khảo');
  sourceList.append(element('div', 'sources-heading', `ĐOẠN NGUỒN THAM KHẢO · ${data.passages.length}`));
  sourceCards.forEach(card => sourceList.append(card));
  if (sourceCards.length) answer.append(sourceList);

  const actions = element('div', 'assistant-tools');
  const copy = element('button', 'text-action', 'Sao chép câu trả lời');
  copy.type = 'button';
  copy.append(icon('M8 8V5.5A1.5 1.5 0 0 1 9.5 4h9A1.5 1.5 0 0 1 20 5.5v10a1.5 1.5 0 0 1-1.5 1.5H16M6 8h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Z'));
  copy.prepend(copy.lastChild);
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(answerText);
      copy.lastChild.textContent = 'Đã sao chép';
      announce('Đã sao chép câu trả lời.');
      setTimeout(() => { if (copy.isConnected) copy.lastChild.textContent = 'Sao chép câu trả lời'; }, 1800);
    } catch {
      announce('Trình duyệt không cho phép sao chép ở trang này.');
    }
  });
  actions.append(copy);
  answer.append(actions);
  announce(isChat ? 'Đã nhận phản hồi trò chuyện, không tra cứu kho tài liệu ở lượt này.' : `Đã tìm thấy câu trả lời và ${data.passages.length} đoạn nguồn tham khảo. Câu trả lời AI chưa được kiểm chứng.`);
}

function showError(message, question) {
  transcript.push({ role: 'BoneScope · Lỗi', text: message });
  const error = bubble('assistant', 'error-message');
  assistantLabel(error, 'Không thể hoàn tất yêu cầu');
  error.append(element('p', '', message));
  const retry = element('button', 'text-action', 'Thử lại');
  retry.type = 'button';
  retry.append(icon('M20 7v5h-5M4 17v-5h5m-3.5-3A7 7 0 0 1 18 7l2 5M4 12l2 5a7 7 0 0 0 12.5-2'));
  retry.prepend(retry.lastChild);
  retry.addEventListener('click', () => sendQuestion(question));
  error.append(retry);
  announce(message);
}

async function sendQuestion(question) {
  if (!question || submit.disabled) return;
  stoppedByUser = false;
  const history = boundedHistory();
  const mode = chatMode.value;
  const revision = conversationRevision;
  if (messages.querySelector('.welcome-block')) messages.replaceChildren();
  const user = bubble('user');
  user.append(element('p', '', question));
  transcript.push({ role: 'Bạn', text: question });
  exportButton.disabled = false;
  sessionEmpty.hidden = true;
  const shortcut = element('button', 'session-question', question);
  shortcut.type = 'button'; shortcut.title = question;
  shortcut.addEventListener('click', () => { setSidebar(false); user.scrollIntoView({ block: 'start', behavior: 'auto' }); });
  sessionQuestions.append(shortcut);
  setBusy(true);
  const pending = bubble('assistant', 'pending-message');
  assistantLabel(pending, mode === 'auto' ? 'Đang suy nghĩ và trả lời' : 'Đang tra cứu và soạn bản nháp');
  const title = element('div', 'pending-title');
  title.append(element('span', 'spinner'));
  const progressText = element('span', '', 'Đang xử lý câu hỏi…');
  title.append(progressText);
  pending.append(title);
  pending.append(element('p', 'message-meta', mode === 'auto' ? `${providerLabel} đang đọc ngữ cảnh hội thoại. Câu hỏi về xương sẽ được tra cứu tài liệu.` : `${providerLabel} sẽ soạn bản nháp từ các đoạn tìm được. Lần tra cứu đầu có thể cần nạp mô hình tìm kiếm.`));
  announce('Đang xử lý câu hỏi và ngữ cảnh hội thoại.');
  scrollToLatest();

  const controller = new AbortController();
  activeController = controller;
  const startedAt = Date.now();
  const progressTimer = setInterval(() => {
    progressText.textContent = `Đang xử lý câu hỏi · ${Math.floor((Date.now() - startedAt) / 1000)} giây`;
  }, 1000);
  const timer = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history, mode }),
      cache: 'no-store',
      signal: controller.signal,
    });
    if (!response.ok) {
      let detail = 'Không thể tra cứu nguồn lúc này.';
      try {
        const body = await response.json();
        if (typeof body.detail === 'string') detail = body.detail;
      } catch { /* Keep the readable fallback for non-JSON server errors. */ }
      throw new Error(detail);
    }
    const data = await response.json();
    if (revision !== conversationRevision) return;
    pending.remove();
    renderResult(data);
    chatHistory.push({ role: 'user', content: question });
    chatHistory.push({ role: 'assistant', content: data.answer || messages.lastElementChild.innerText });
    transcript.push({ role: 'BoneScope', text: data.answer || messages.lastElementChild.innerText, passages: data.passages || [] });
  } catch (error) {
    if (revision !== conversationRevision) return;
    pending.remove();
    if (error.name === 'AbortError') {
      if (stoppedByUser) {
        transcript.push({ role: 'BoneScope', text: 'Đã dừng chờ phản hồi. Yêu cầu đã gửi có thể vẫn được máy chủ xử lý.' });
        const cancelled = bubble('assistant');
        assistantLabel(cancelled, 'Đã dừng chờ phản hồi');
        cancelled.append(element('p', 'message-meta', 'Bạn có thể gửi câu hỏi khác. Yêu cầu đã gửi có thể vẫn được máy chủ xử lý.'));
        announce('Đã dừng chờ phản hồi.');
      } else showError(`Đã hết thời gian chờ tra cứu và tạo bản nháp. Hãy kiểm tra kết nối ${providerLabel} hoặc thử lại sau.`, question);
    } else {
      showError(error.message || 'Đã xảy ra lỗi khi tra cứu.', question);
    }
  } finally {
    clearTimeout(timer);
    clearInterval(progressTimer);
    if (activeController === controller) activeController = null;
    if (revision === conversationRevision) {
      setBusy(false);
      input.focus();
      scrollToLatest();
    }
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = '';
  resizeInput();
  updateCounter();
  sendQuestion(question);
});

input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

const themeToggle = document.getElementById('theme-toggle');
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const isDark = theme === 'dark';
  themeToggle.setAttribute('aria-label', isDark ? 'Bật giao diện sáng' : 'Bật giao diện tối');
  themeToggle.title = isDark ? 'Bật giao diện sáng' : 'Bật giao diện tối';
  document.querySelector('meta[name="theme-color"]').content = isDark ? '#111418' : '#f7f8fc';
}
let savedTheme = 'light';
try { savedTheme = localStorage.getItem('bonescope-theme') === 'dark' ? 'dark' : 'light'; } catch { /* Storage may be unavailable in restricted browser contexts. */ }
applyTheme(savedTheme);
themeToggle.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem('bonescope-theme', next); } catch { /* Theme still works for this page view. */ }
});

updateCounter();

const sidebar = document.getElementById('sidebar');
const menuToggle = document.getElementById('menu-toggle');
const backdrop = document.getElementById('sidebar-backdrop');
const mobileQuery = matchMedia('(max-width: 760px)');
function setSidebar(open) {
  const active = open && mobileQuery.matches;
  sidebar.classList.toggle('is-open', active);
  sidebar.inert = mobileQuery.matches && !active;
  document.getElementById('main').inert = active;
  backdrop.hidden = !active;
  menuToggle.setAttribute('aria-expanded', String(active));
  if (active) clear.focus();
  else if (sidebar.contains(document.activeElement)) menuToggle.focus();
}
menuToggle.addEventListener('click', () => setSidebar(true));
backdrop.addEventListener('click', () => { setSidebar(false); menuToggle.focus(); });
mobileQuery.addEventListener('change', () => setSidebar(false));
sidebar.querySelector('.primary-nav a').addEventListener('click', () => { setSidebar(false); input.focus(); });
document.addEventListener('keydown', event => {
  if (!sidebar.classList.contains('is-open')) return;
  if (event.key === 'Escape') { setSidebar(false); menuToggle.focus(); }
  if (event.key === 'Tab') {
    const targets = [...sidebar.querySelectorAll('a, button')].filter(node => !node.disabled);
    const first = targets[0], last = targets[targets.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});
setSidebar(false);

const helpDialog = document.getElementById('help-dialog');
document.getElementById('help-button').addEventListener('click', () => { setSidebar(false); helpDialog.showModal(); });
document.getElementById('close-help').addEventListener('click', () => helpDialog.close());
helpDialog.addEventListener('click', event => { if (event.target === helpDialog) {
  const bounds = helpDialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) helpDialog.close();
} });

exportButton.addEventListener('click', () => {
  const chunks = ['# BoneScope · Cuộc trò chuyện', 'Bản demo học tập. Nội dung AI chưa được kiểm chứng; cần đối chiếu tài liệu gốc.'];
  transcript.forEach(entry => {
    chunks.push(`## ${entry.role}`, entry.text);
    entry.passages?.forEach((hit, index) => {
      chunks.push(`### [S${index + 1}] ${hit.title || hit.source_id || 'Nguồn'}`, hit.text || '');
      if (hit.url) chunks.push(`Nguồn gốc: ${hit.url}`);
      if (hit.license) chunks.push(`Giấy phép: ${hit.license}`);
    });
  });
  const url = URL.createObjectURL(new Blob(['\ufeff' + chunks.join('\n\n')], { type: 'text/markdown;charset=utf-8' }));
  const link = element('a'); link.href = url; link.download = `bonescope-${new Date().toISOString().slice(0, 10)}.md`;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  announce('Đã xuất nội dung cuộc trò chuyện.');
});
