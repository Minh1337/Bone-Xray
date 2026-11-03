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
let activeCase = null;
const caseBanner = document.getElementById('active-case-banner');
const caseDialog = document.getElementById('case-dialog');
const caseForm = document.getElementById('case-form');
const caseError = document.getElementById('case-error');
const caseImage = document.getElementById('case-image');
const caseImageLabel = document.getElementById('case-image-label');
const caseJson = document.getElementById('case-json');
const casePreviewRow = document.getElementById('case-preview-row');
const casePreviewImg = document.getElementById('case-preview-img');
const casePreviewName = document.getElementById('case-preview-name');
const caseJsonNote = document.getElementById('case-json-note');
const caseJsonPickerWrap = document.getElementById('case-json-picker-wrap');
const caseJsonSelect = document.getElementById('case-json-select');
const caseAge = document.getElementById('case-age');
const caseGender = document.getElementById('case-gender');
const caseBinaryStatus = document.getElementById('case-binary-status');
const caseBinaryGrid = document.getElementById('case-binary-grid');
const caseConfirmed = document.getElementById('case-confirmed');
const submitCaseButton = document.getElementById('submit-case');
const BINARY_FIELDS = [
  ['hand', 'Bàn tay'], ['ulna', 'Xương trụ'], ['radius', 'Xương quay'], ['humerus', 'Xương cánh tay'],
  ['foot', 'Bàn chân'], ['tibia', 'Xương chày'], ['fibula', 'Xương mác'], ['femur', 'Xương đùi'],
  ['hip bone', 'Xương hông'], ['ankle-joint', 'Khớp cổ chân'], ['knee-joint', 'Khớp gối'],
  ['hip-joint', 'Khớp háng'], ['elbow-joint', 'Khớp khuỷu'], ['shoulder-joint', 'Khớp vai'],
  ['upper limb', 'Chi trên'], ['lower limb', 'Chi dưới'], ['pelvis', 'Vùng chậu'],
  ['frontal', 'Hướng thẳng (frontal)'], ['lateral', 'Hướng nghiêng (lateral)'], ['oblique', 'Hướng chếch (oblique)'],
];
const VIEW_KEYS = new Set(['frontal', 'lateral', 'oblique']);
const binaryControls = new Map();
let importedCases = [];
let expectedCaseImage = null;
let previewObjectUrl = null;
let caseBusy = false;
let caseStep = 0;
let caseController = null;

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

function resetChat(options = {}) {
  conversationRevision += 1;
  if (activeController) activeController.abort();
  activeController = null;
  if (!options.keepCase && activeCase?.case_id) {
    const staleId = activeCase.case_id;
    activeCase = null;
    renderCaseBanner();
    fetch(`/api/case/${encodeURIComponent(staleId)}`, { method: 'DELETE', cache: 'no-store' }).catch(() => {});
  }
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

clear.addEventListener('click', () => resetChat());
document.getElementById('mobile-new-chat').addEventListener('click', () => resetChat());
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
  if (suggestion.dataset.action === 'open-case') {
    openCaseModal();
    return;
  }
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
  if (!['greeting', 'out_of_scope', 'insufficient_evidence', 'candidates_found', 'conversation', 'case_explanation'].includes(data.status)) throw new Error('Định dạng kết quả không hợp lệ.');
  if (data.status === 'candidates_found' && (!Array.isArray(data.passages) || !data.passages.length)) throw new Error('Định dạng nguồn không hợp lệ.');
  if (data.status === 'case_explanation' && !Array.isArray(data.passages)) throw new Error('Định dạng nguồn không hợp lệ.');
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
    if (data.case_hint) {
      answer.append(element('p', 'message-meta', 'Gợi ý: trợ lý không nhìn thấy ảnh trực tiếp. Hãy hỏi về đầu ra mô hình của ca đang mở (ví dụ: “Giải thích ý nghĩa nhãn Top-1 và giới hạn của điểm softmax”) hoặc hỏi kiến thức chung về thuật ngữ trong tài liệu.'));
    }
    announce('Chưa tìm được bằng chứng phù hợp.');
    return;
  }
  const isChat = data.status === 'conversation';
  const isCaseExplain = data.status === 'case_explanation';
  if (!isCaseExplain && ((!isChat && data.status !== 'candidates_found') || !Array.isArray(data.passages) || (isChat ? data.passages.length !== 0 : !data.passages.length))) {
    throw new Error('Định dạng kết quả không hợp lệ.');
  }

  let badge = `${providerLabels[data.provider] || 'AI'} · ${isChat ? 'trò chuyện · kiến thức chung' : 'bản nháp chưa kiểm chứng'}`;
  if (data.case_context_used) badge += ' · ngữ cảnh ca ảnh';
  if (isCaseExplain) {
    badge = data.basis === 'documents'
      ? `${providerLabels[data.provider] || 'AI'} · giải thích ca học tập · chưa kiểm chứng`
      : 'BoneScope · tóm tắt ca học tập (mẫu máy chủ)';
  }
  assistantLabel(answer, badge);
  const answerText = data.answer || 'Chưa tạo được câu trả lời.';
  const sourceCards = data.passages.map(renderSource);
  answer.append(renderAnswer(answerText, sourceCards));
  if (data.draft_error) {
    answer.append(element('p', 'message-meta', `Lưu ý bản nháp AI: ${data.draft_error}`));
  }
  const caveat = element('p', 'answer-caveat');
  caveat.append(icon('M12 3.5 20 18H4L12 3.5Z M12 9v4m0 2.5h.01'));
  caveat.append(document.createTextNode('Nội dung do AI tạo, chưa được kiểm chứng tự động. Hãy đối chiếu từng ý với nguồn bên dưới.'));
  if (!isChat && (!isCaseExplain || data.basis === 'documents')) answer.append(caveat);

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
  const payload = { question, history, mode };
  if (activeCase?.case_id) payload.case_id = activeCase.case_id;
  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      cache: 'no-store',
      signal: controller.signal,
    });
    if (response.status === 410 && activeCase) {
      activeCase = null;
      renderCaseBanner();
    }
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
  document.querySelector('meta[name="theme-color"]').content = isDark ? '#141e19' : '#f5f8f7';
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
  if (activeCase) {
    const topList = (activeCase.top3 || []).map(item => `- ${item.display || item.label}: ${Number(item.score).toFixed(3)}`).join('\n');
    chunks.push('## Ca ảnh học tập đang mở', `Top-1: ${activeCase.top1_display || activeCase.top1}\n${topList}\n${activeCase.notice || ''}`);
  }
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

// ---------------------------------------------------------------------------
// Educational image-case flow (Swin + Metadata -> RAG -> Conversation)
// ---------------------------------------------------------------------------

BINARY_FIELDS.forEach(([key, labelText]) => {
  if (['hand', 'ankle-joint', 'upper limb', 'frontal'].includes(key)) {
    const labels = { hand: 'Xương', 'ankle-joint': 'Khớp', 'upper limb': 'Vùng giải phẫu', frontal: 'Tư thế chụp · chọn đúng một hướng' };
    caseBinaryGrid.append(element('h4', 'binary-group-title', labels[key]));
  }
  const wrap = element('label', `case-binary-item${VIEW_KEYS.has(key) ? ' is-view' : ''}`);
  const title = element('span', 'case-binary-label', labelText);
  const code = element('small', '', key);
  const select = document.createElement('select');
  select.required = true;
  select.setAttribute('aria-label', `${labelText} (${key})`);
  [['', '—'], ['0', '0 · Không'], ['1', '1 · Có']].forEach(([val, text]) => select.add(new Option(text, val)));
  select.addEventListener('change', () => {
    caseConfirmed.checked = false;
    updateBinaryCounter();
  });
  wrap.append(title, code, select);
  caseBinaryGrid.append(wrap);
  binaryControls.set(key, select);
});

function updateBinaryCounter() {
  const filled = [...binaryControls.values()].filter(ctrl => ctrl.value !== '').length;
  caseBinaryStatus.textContent = `Vị trí & tư thế (${filled}/20 đã chọn)`;
  document.getElementById('metadata-progress').value = filled;
}

function showCaseError(msg) {
  caseError.textContent = msg;
  caseError.hidden = !msg;
  if (msg && caseDialog.open) {
    caseError.focus();
    caseError.scrollIntoView({ block: 'nearest' });
  }
}

function resetCaseForm() {
  caseController?.abort();
  caseForm.reset();
  caseForm.removeAttribute('aria-busy');
  caseForm.querySelectorAll('input, select, button').forEach(node => { node.disabled = false; });
  document.getElementById('cancel-case').textContent = 'Hủy';
  submitCaseButton.disabled = false;
  submitCaseButton.querySelector('span').textContent = 'Chạy mô hình & giải thích';
  caseImage.value = '';
  caseJson.value = '';
  caseJsonSelect.replaceChildren();
  caseJsonPickerWrap.hidden = true;
  caseJsonNote.textContent = '';
  importedCases = [];
  expectedCaseImage = null;
  binaryControls.forEach(ctrl => { ctrl.value = ''; });
  caseImageLabel.textContent = 'Chọn ảnh X-quang';
  casePreviewRow.hidden = true;
  casePreviewImg.hidden = true;
  casePreviewImg.removeAttribute('src');
  casePreviewName.textContent = '';
  document.getElementById('case-preview-hint').textContent = 'Kiểm tra ảnh trước khi tiếp tục.';
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = null;
  }
  caseConfirmed.checked = false;
  updateBinaryCounter();
  showCaseError('');
}

function normalizedFilename(name) {
  return String(name || '').replaceAll('\\', '/').split('/').pop().toLowerCase().replace(/\.jpeg$/, '.jpg');
}

function openCaseModal() {
  if (caseBusy || submit.disabled) {
    announce('Hãy đợi yêu cầu hiện tại hoàn tất hoặc dừng chờ trước khi mở ca.');
    return;
  }
  setSidebar(false);
  resetCaseForm();
  showCaseError('');
  setCaseStep(0, false);
  caseDialog.showModal();
  caseImage.focus();
}

document.getElementById('open-case-dialog').addEventListener('click', openCaseModal);
document.getElementById('composer-case-button').addEventListener('click', openCaseModal);
function closeCaseModal() {
  caseController?.abort();
  if (!caseBusy) resetCaseForm();
  caseDialog.close();
}
document.getElementById('close-case-dialog').addEventListener('click', closeCaseModal);
document.getElementById('cancel-case').addEventListener('click', closeCaseModal);
caseDialog.addEventListener('cancel', () => caseController?.abort());
caseDialog.addEventListener('click', event => {
  if (event.target === caseDialog) {
    const bounds = caseDialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) closeCaseModal();
  }
});

document.getElementById('case-fill-zeros').addEventListener('click', () => {
  binaryControls.forEach(ctrl => { if (ctrl.value === '') ctrl.value = '0'; });
  caseConfirmed.checked = false;
  updateBinaryCounter();
});

document.getElementById('case-clear-fields').addEventListener('click', () => {
  caseAge.value = '';
  caseGender.value = '';
  binaryControls.forEach(ctrl => { ctrl.value = ''; });
  expectedCaseImage = null;
  caseJsonNote.textContent = '';
  caseConfirmed.checked = false;
  updateBinaryCounter();
  showCaseError('');
});

caseImage.addEventListener('change', () => {
  showCaseError('');
  caseConfirmed.checked = false;
  if (previewObjectUrl) { URL.revokeObjectURL(previewObjectUrl); previewObjectUrl = null; }
  casePreviewRow.hidden = true;
  casePreviewImg.hidden = true;
  casePreviewImg.removeAttribute('src');
  casePreviewName.textContent = '';
  caseImageLabel.textContent = 'Chọn ảnh X-quang';
  const file = caseImage.files[0];
  if (!file) {
    casePreviewRow.hidden = true;
    caseImageLabel.textContent = 'Chọn ảnh X-quang (JPG, PNG, BMP, TIFF ≤ 30 MiB)';
    return;
  }
  if (!/\.(jpe?g|png|bmp|tiff?)$/i.test(file.name)) {
    showCaseError('Định dạng chưa hỗ trợ. Chọn JPG, PNG, BMP hoặc TIFF.');
    caseImage.value = '';
    return;
  }
  if (!file.size || file.size > 30 * 1024 * 1024) {
    showCaseError('Ảnh phải có nội dung và không vượt quá 30 MiB.');
    caseImage.value = '';
    return;
  }
  previewObjectUrl = URL.createObjectURL(file);
  casePreviewImg.hidden = false;
  casePreviewImg.src = previewObjectUrl;
  casePreviewName.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MiB`;
  caseImageLabel.textContent = file.name;
  casePreviewRow.hidden = false;
});

casePreviewImg.addEventListener('error', () => {
  casePreviewImg.hidden = true;
  document.getElementById('case-preview-hint').textContent = 'Trình duyệt không xem trước được ảnh này. Máy chủ sẽ kiểm tra định dạng khi phân tích.';
});
casePreviewImg.addEventListener('load', () => {
  document.getElementById('case-preview-hint').textContent = 'Kiểm tra ảnh trước khi tiếp tục.';
});

const dropZone = document.querySelector('.case-file-picker');
['dragenter', 'dragover'].forEach(type => dropZone.addEventListener(type, event => {
  event.preventDefault();
  if (!caseBusy) dropZone.classList.add('is-dragging');
}));
['dragleave', 'drop'].forEach(type => dropZone.addEventListener(type, () => dropZone.classList.remove('is-dragging')));
dropZone.addEventListener('drop', event => {
  event.preventDefault();
  if (caseBusy) return;
  if (event.dataTransfer.files.length !== 1) {
    showCaseError('Chọn một ảnh cho mỗi lần phân tích.');
    return;
  }
  caseImage.files = event.dataTransfer.files;
  caseImage.dispatchEvent(new Event('change'));
});

function setCaseStep(step, moveFocus = true) {
  caseStep = step;
  document.querySelectorAll('[data-case-step]').forEach((node, index) => { node.hidden = index !== step; });
  document.querySelectorAll('.case-stepper li').forEach((node, index) => {
    if (index === step) node.setAttribute('aria-current', 'step');
    else node.removeAttribute('aria-current');
    node.classList.toggle('is-complete', index < step);
  });
  document.getElementById('case-back').hidden = step === 0;
  document.getElementById('case-next').hidden = step === 2;
  submitCaseButton.hidden = step !== 2;
  document.getElementById('case-step-label').textContent = `Bước ${step + 1} / 3`;
  caseDialog.scrollTop = 0;
  if (moveFocus) document.querySelector(`[data-case-step="${step}"] h3`).focus({ preventScroll: true });
}

function collectCaseMetadata() {
  const file = caseImage.files[0];
  if (!file) throw new Error('Hãy chọn ảnh X-quang trước khi phân tích.');
  if (expectedCaseImage && normalizedFilename(expectedCaseImage) !== normalizedFilename(file.name)) {
    throw new Error(`Metadata đang chọn thuộc ảnh ${expectedCaseImage}. Hãy chọn đúng ảnh hoặc bấm "Xóa trắng" để nhập ca khác.`);
  }
  if (caseAge.value === '' || !caseAge.validity.valid) throw new Error('Nhập tuổi hợp lệ từ 0 đến 120.');
  const meta = { age: Number(caseAge.value), gender: caseGender.value };
  for (const [key, label] of BINARY_FIELDS) {
    const value = binaryControls.get(key).value;
    if (value === '') throw new Error(`Chưa chọn giá trị cho ${label} (${key}).`);
    meta[key] = Number(value);
  }
  validateMetadataObject(meta);
  if (!BINARY_FIELDS.some(([key]) => !VIEW_KEYS.has(key) && meta[key] === 1)) throw new Error('Chọn ít nhất 1 vị trí xương, khớp hoặc vùng giải phẫu (= 1).');
  if ([...VIEW_KEYS].filter(key => meta[key] === 1).length !== 1) throw new Error('Chọn đúng 1 tư thế chụp: frontal, lateral hoặc oblique (= 1).');
  return meta;
}

function advanceCaseStep() {
  if (caseBusy) return;
  showCaseError('');
  try {
    if (caseStep === 0 && !caseImage.files[0]) throw new Error('Chọn một ảnh X-quang để tiếp tục.');
    if (caseStep === 1) {
      const meta = collectCaseMetadata();
      const review = document.getElementById('case-review');
      review.replaceChildren();
      const selected = BINARY_FIELDS.filter(([key]) => meta[key] === 1);
      const rows = [
        ['Ảnh đã chọn', caseImage.files[0].name],
        ['Thông tin ca', `${meta.age} tuổi · ${meta.gender === 'M' ? 'Nam' : 'Nữ'}`],
        ['Vị trí', selected.filter(([key]) => !VIEW_KEYS.has(key)).map(([, label]) => label).join(', ')],
        ['Tư thế chụp', selected.filter(([key]) => VIEW_KEYS.has(key)).map(([, label]) => label).join(', ')],
        ['Metadata', 'Đã nhập đủ 22 trường'],
      ];
      rows.forEach(([title, value]) => {
        const row = element('div', 'review-row');
        row.append(element('span', '', title), element('strong', '', value));
        review.append(row);
      });
    }
    setCaseStep(Math.min(caseStep + 1, 2));
  } catch (error) { showCaseError(error.message); }
}
document.getElementById('case-next').addEventListener('click', advanceCaseStep);
document.getElementById('case-back').addEventListener('click', () => {
  if (caseBusy) return;
  showCaseError('');
  caseConfirmed.checked = false;
  setCaseStep(Math.max(0, caseStep - 1));
});
caseForm.addEventListener('input', event => {
  if (event.target !== caseConfirmed) caseConfirmed.checked = false;
});

function validateMetadataObject(meta) {
  const required = ['age', 'gender', ...BINARY_FIELDS.map(([k]) => k)];
  if (!meta || typeof meta !== 'object' || Array.isArray(meta) || Object.keys(meta).length !== required.length || required.some(k => !Object.hasOwn(meta, k))) {
    throw new Error('Metadata phải chứa đúng 22 trường theo mẫu.');
  }
  if (typeof meta.age !== 'number' || !Number.isFinite(meta.age) || meta.age < 0 || meta.age > 120) {
    throw new Error('Tuổi phải là số từ 0 đến 120.');
  }
  if (!['M', 'F'].includes(meta.gender)) {
    throw new Error('Giới tính phải là M hoặc F.');
  }
  for (const [key] of BINARY_FIELDS) {
    if (typeof meta[key] !== 'number' || ![0, 1].includes(meta[key])) {
      throw new Error(`Trường ${key} phải là số 0 hoặc 1.`);
    }
  }
  return meta;
}

function applyImportedCase(index) {
  const entry = importedCases[index];
  if (!entry) return;
  const meta = validateMetadataObject(entry.metadata);
  caseAge.value = String(meta.age);
  caseGender.value = meta.gender;
  BINARY_FIELDS.forEach(([key]) => { binaryControls.get(key).value = String(meta[key]); });
  expectedCaseImage = entry.image || null;
  caseJsonNote.textContent = expectedCaseImage
    ? `Đã nạp ${entry.id || 'ca'}. Hãy chọn đúng ảnh: ${expectedCaseImage}`
    : 'Đã nạp metadata 22 trường.';
  casePreviewRow.hidden = !caseImage.files[0];
  caseConfirmed.checked = false;
  updateBinaryCounter();
}

caseJson.addEventListener('change', async () => {
  showCaseError('');
  const file = caseJson.files[0];
  if (!file) return;
  try {
    if (file.size > 1024 * 1024) throw new Error('Tệp JSON vượt quá 1 MiB.');
    const raw = JSON.parse((await file.text()).replace(/^\uFEFF/, ''));
    const list = Array.isArray(raw) ? raw : (raw.metadata ? [raw] : [{ metadata: raw }]);
    if (!list.length || list.length > 100) throw new Error('Tệp JSON cần chứa từ 1 đến 100 ca.');
    list.forEach(item => validateMetadataObject(item.metadata));
    importedCases = list;
    caseJsonSelect.replaceChildren();
    list.forEach((item, idx) => {
      const imgLabel = item.image ? ` · ${String(item.image).replaceAll('\\', '/').split('/').pop()}` : '';
      caseJsonSelect.add(new Option(`${item.id || `Ca ${idx + 1}`}${imgLabel}`, String(idx)));
    });
    caseJsonPickerWrap.hidden = list.length <= 1;
    applyImportedCase(0);
  } catch (err) {
    showCaseError(`Không nạp được JSON: ${err.message}`);
  }
});

caseJsonSelect.addEventListener('change', () => applyImportedCase(Number(caseJsonSelect.value)));

function renderCaseBanner() {
  caseBanner.replaceChildren();
  if (!activeCase) {
    caseBanner.hidden = true;
    return;
  }
  caseBanner.hidden = false;
  const header = element('div', 'case-banner-head');
  const titleWrap = element('div', 'case-banner-title');
  titleWrap.append(element('span', 'case-pill', 'CA ẢNH ĐANG MỞ'));
  titleWrap.append(element('strong', '', `${activeCase.top1_display || activeCase.top1} (${Number(activeCase.top3?.[0]?.score ?? 0).toFixed(3)})`));
  if (activeCase.mapping?.status) {
    titleWrap.append(element('span', 'case-mapping-tag', `Ánh xạ: ${activeCase.mapping.status}`));
  }
  const actions = element('div', 'case-banner-actions');
  const switchBtn = element('button', 'text-action', 'Đổi ảnh / ca khác');
  switchBtn.type = 'button';
  switchBtn.addEventListener('click', openCaseModal);
  const clearBtn = element('button', 'text-action', 'Xóa ca');
  clearBtn.type = 'button';
  clearBtn.addEventListener('click', () => {
    resetChat();
    announce('Đã xóa ca ảnh và làm mới ngữ cảnh hội thoại.');
  });
  actions.append(switchBtn, clearBtn);
  header.append(titleWrap, actions);

  const topRow = element('div', 'case-top3-row');
  (activeCase.top3 || []).forEach((item, idx) => {
    const chip = element('span', 'case-score-chip', `#${idx + 1} ${item.display || item.label}: ${Number(item.score).toFixed(3)}`);
    topRow.append(chip);
  });
  const note = element('p', 'case-banner-note', `${activeCase.mapping?.note || ''} ${activeCase.notice || ''}`.trim());
  caseBanner.append(header, topRow, note);
}

function renderCaseSummaryBubble(caseData, fileName) {
  const card = bubble('assistant', 'case-summary-message');
  assistantLabel(card, `Mô hình phân loại cục bộ · ${ (caseData.device || 'CPU').toUpperCase() } · ${Number(caseData.prediction_seconds || 0).toFixed(2)}s`);
  const heading = element('p', '', `Kết quả phân loại cho ảnh học tập (${fileName}): Top-1 là ${caseData.top1_display || caseData.top1}.`);
  card.append(heading);
  const list = element('ul', 'case-top3-list');
  (caseData.top3 || []).forEach(item => {
    const row = element('li');
    const score = Math.min(1, Math.max(0, Number(item.score) || 0));
    const heading = element('div', 'score-heading');
    heading.append(element('span', '', item.display || item.label), element('strong', '', Number(item.score).toFixed(4)));
    const track = element('div', 'score-track');
    track.setAttribute('aria-hidden', 'true');
    const fill = element('span', 'score-fill');
    fill.style.width = `${score * 100}%`;
    track.append(fill);
    row.append(heading, track);
    list.append(row);
  });
  card.append(list);
  if (caseData.mapping?.note) {
    card.append(element('p', 'message-meta', `Ghi chú ánh xạ nhãn → tài liệu: ${caseData.mapping.note}`));
  }
  card.append(element('p', 'answer-caveat', caseData.notice || 'Điểm softmax chưa hiệu chỉnh, không phải xác suất mắc bệnh hay chẩn đoán.'));
}

caseForm.addEventListener('submit', async event => {
  event.preventDefault();
  if (caseBusy || submit.disabled) return;
  if (caseStep !== 2) { advanceCaseStep(); return; }
  showCaseError('');
  const file = caseImage.files[0];
  let caseTimer;
  try {
    const meta = collectCaseMetadata();
    if (!caseConfirmed.checked) throw new Error('Hãy đánh dấu xác nhận dữ liệu học tập và cùng một ca.');

    caseBusy = true;
    caseController = new AbortController();
    caseForm.setAttribute('aria-busy', 'true');
    caseForm.querySelectorAll('input, select, button').forEach(node => { if (node.id !== 'cancel-case') node.disabled = true; });
    document.getElementById('cancel-case').textContent = 'Dừng chờ';
    submitCaseButton.disabled = true;
    submitCaseButton.querySelector('span').textContent = 'Đang chạy mô hình…';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(meta));
    caseTimer = setTimeout(() => caseController?.abort(), 180000);
    const res = await fetch('/api/case', { method: 'POST', body: formData, cache: 'no-store', signal: caseController.signal });
    clearTimeout(caseTimer);
    if (!res.ok) {
      let detail = 'Không phân tích được ca ảnh.';
      try {
        const errBody = await res.json();
        if (typeof errBody.detail === 'string') detail = errBody.detail;
      } catch { /* fallback */ }
      throw new Error(detail);
    }
    const caseData = await res.json();
    if (caseData.answer_ready !== false || !caseData.case_id) throw new Error('Phản hồi ca ảnh không hợp lệ.');

    // Replacing an image always clears prior chat and deletes the old case context.
    resetChat({ keepCase: true });
    if (activeCase?.case_id && activeCase.case_id !== caseData.case_id) {
      fetch(`/api/case/${encodeURIComponent(activeCase.case_id)}`, { method: 'DELETE', cache: 'no-store' }).catch(() => {});
    }
    activeCase = caseData;
    renderCaseBanner();
    caseDialog.close();

    if (messages.querySelector('.welcome-block')) messages.replaceChildren();
    const userMsg = `Phân tích ca ảnh học tập (${file.name}) · ${meta.gender}, ${meta.age} tuổi`;
    const userBubble = bubble('user');
    userBubble.append(element('p', '', userMsg));
    transcript.push({ role: 'Bạn', text: userMsg });
    exportButton.disabled = false;
    sessionEmpty.hidden = true;
    const shortcut = element('button', 'session-question', userMsg);
    shortcut.type = 'button';
    shortcut.title = userMsg;
    shortcut.addEventListener('click', () => { setSidebar(false); userBubble.scrollIntoView({ block: 'start', behavior: 'auto' }); });
    sessionQuestions.append(shortcut);

    renderCaseSummaryBubble(caseData, file.name);
    scrollToLatest();

    // Automatically request the grounded academic explanation for the new case.
    setBusy(true);
    const revision = conversationRevision;
    const pending = bubble('assistant', 'pending-message');
    assistantLabel(pending, 'Đang đối chiếu kho tài liệu cho nhãn dự đoán');
    const pendingRow = element('div', 'pending-title');
    pendingRow.append(element('span', 'spinner'), element('span', '', 'Đang tra cứu nguồn và tạo giải thích học thuật…'));
    pending.append(pendingRow);
    scrollToLatest();

    try {
      activeController = caseController;
      stoppedByUser = false;
      caseTimer = setTimeout(() => caseController?.abort(), 90000);
      const explainRes = await fetch(`/api/case/${encodeURIComponent(caseData.case_id)}/explain`, {
        signal: caseController.signal,
        method: 'POST',
        cache: 'no-store',
      });
      if (!explainRes.ok) {
        let detail = 'Không tạo được giải thích cho ca ảnh.';
        try {
          const body = await explainRes.json();
          if (typeof body.detail === 'string') detail = body.detail;
        } catch { /* fallback */ }
        throw new Error(detail);
      }
      const explainData = await explainRes.json();
      if (revision !== conversationRevision) return;
      pending.remove();
      renderResult(explainData);
      const assistantText = explainData.answer || messages.lastElementChild.innerText;
      chatHistory.push({ role: 'user', content: `Đã phân tích ca ảnh học tập; mô hình dự đoán Top-1 là ${caseData.top1} (${Number(caseData.top3?.[0]?.score ?? 0).toFixed(3)}). Hãy giải thích học thuật.` });
      chatHistory.push({ role: 'assistant', content: assistantText });
      transcript.push({ role: 'BoneScope', text: assistantText, passages: explainData.passages || [] });
    } catch (explainErr) {
      if (revision === conversationRevision) {
        pending.remove();
        showError(explainErr.name === 'AbortError' ? (stoppedByUser ? 'Đã dừng chờ giải thích. Kết quả phân loại vẫn được giữ; tác vụ trên máy chủ có thể vẫn đang chạy.' : 'Đã hết thời gian chờ giải thích. Bạn có thể hỏi tiếp về kết quả đã có.') : (explainErr.message || 'Không lấy được giải thích tài liệu.'), `Giải thích ý nghĩa nhãn ${caseData.top1} và giới hạn của điểm mô hình`);
      }
    } finally {
      if (revision === conversationRevision) {
        setBusy(false);
        input.focus();
        scrollToLatest();
      }
    }
  } catch (err) {
    if (caseDialog.open) showCaseError(err.name === 'AbortError' ? 'Đã hết thời gian chờ phân tích. Máy chủ có thể vẫn đang xử lý; hãy thử lại sau.' : (err.message || 'Không thể phân tích ca ảnh.'));
  } finally {
    clearTimeout(caseTimer);
    if (activeController === caseController) activeController = null;
    caseController = null;
    caseBusy = false;
    caseForm.removeAttribute('aria-busy');
    caseForm.querySelectorAll('input, select, button').forEach(node => { node.disabled = false; });
    document.getElementById('cancel-case').textContent = 'Hủy';
    submitCaseButton.disabled = false;
    submitCaseButton.querySelector('span').textContent = 'Chạy mô hình & giải thích';
  }
});
