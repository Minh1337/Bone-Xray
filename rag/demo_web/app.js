'use strict';

const form = document.getElementById('question-form');
const messages = document.getElementById('messages');
const input = document.getElementById('question');
const submit = document.getElementById('submit');
const imageInput = document.getElementById('image-input');
const imageAttachment = document.getElementById('image-attachment');
const attachmentPreview = document.getElementById('attachment-preview');
const imageViewer = document.getElementById('image-viewer');
const viewedImage = document.getElementById('viewed-image');
const messageImageUrls = new Set();
const savedMessageImages = new Map();
const imageHistoryNote = '[Đã gửi kèm ảnh ngữ cảnh; ảnh không được lưu]';
const imageFollowupNote = '[Đã dùng ảnh ngữ cảnh; ảnh không được lưu]';
const defaultImagePrompt = 'Hãy mô tả ảnh và những gì có thể quan sát được.';
let attachedImage = null;
let attachmentPreviewUrl = null;
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
const transcript = [];
const chatHistory = [];
const savedConversations = document.getElementById('saved-conversations');
const savedEmpty = document.getElementById('saved-empty');
let activeConversationId = null;
const conversationImageContexts = new Map();
let draftConversationContextKey = createDraftConversationContextKey();
let conversationHadImageContext = false;
let openConversationRequest = 0;
const imageContextBanner = document.getElementById('image-context-banner');
const imageContextTitle = document.getElementById('image-context-title');
const imageContextName = document.getElementById('image-context-name');
const imageContextNote = document.getElementById('image-context-note');
const removeImageContext = document.getElementById('remove-image-context');
const reattachImageContext = document.getElementById('reattach-image-context');
const chatMode = document.getElementById('chat-mode');
const attachImage = document.getElementById('attach-image');
const modeHint = document.getElementById('mode-hint');
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
const caseImageMatchNote = document.getElementById('case-image-match-note');
const caseReferenceId = document.getElementById('case-reference-id');
const caseReferenceLoad = document.getElementById('case-reference-load');
const askAiAboutCaseImage = document.getElementById('ask-ai-about-case-image');
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
let referenceImageRequest = 0;
let caseBusy = false;
let caseStep = 0;
let caseController = null;

function boundedHistory(forImage = false) {
  const selected = [];
  let remaining = forImage ? 9000 : 12000;
  const maxMessages = forImage ? 8 : 12;
  for (const item of chatHistory.slice(-maxMessages).reverse()) {
    const content = item.content.slice(0, Math.min(3000, remaining));
    if (!content) break;
    selected.unshift({ role: item.role, content });
    remaining -= content.length;
  }
  if (selected[0]?.role === 'assistant') selected.shift();
  return selected;
}
const providerLabels = { openrouter: 'OpenRouter · Free', groq: 'Groq · dự phòng Free' };
const paidFallbackModel = 'qwen/qwen3.5-flash-02-23';
function providerLabelFor(provider, model) {
  if (provider === 'openrouter' && model === paidFallbackModel) {
    return 'OpenRouter · Qwen3.5 Flash · trả phí dự phòng';
  }
  return providerLabels[provider] || 'AI';
}
let providerLabel = 'AI';

function createDraftConversationContextKey() {
  return `draft:${Date.now()}:${Math.random().toString(36).slice(2)}`;
}

function currentImageContextKey() {
  return activeConversationId ? `saved:${activeConversationId}` : draftConversationContextKey;
}

function renderImageContext(key = currentImageContextKey()) {
  const file = conversationImageContexts.get(key) || null;
  const hasImageContext = Boolean(file || conversationHadImageContext);
  imageContextBanner.hidden = !hasImageContext;
  imageContextTitle.textContent = file
    ? 'Ảnh đang làm ngữ cảnh cho chat này'
    : 'Ảnh đã gửi trước đây không còn trong bộ nhớ tab';
  imageContextName.textContent = file
    ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MiB`
    : 'Lịch sử chỉ lưu văn bản, không lưu tệp ảnh.';
  imageContextNote.textContent = file
    ? (chatMode.value === 'local' ? 'Ảnh được giữ trong tab. Chuyển sang chế độ AI để hỏi về ảnh.'
      : 'Ảnh sẽ được gửi lại cùng câu hỏi tiếp theo trong tab này; không lưu vào lịch sử.')
    : 'Hãy đính kèm lại ảnh để tiếp tục hỏi về nội dung ảnh.';
  removeImageContext.hidden = !file;
  reattachImageContext.hidden = Boolean(file);
}

document.getElementById('close-image-viewer').addEventListener('click', () => imageViewer.close());
imageViewer.addEventListener('close', () => {
  if (!imageViewer.open) viewedImage.removeAttribute('src');
});

function clearMessageImages() {
  if (imageViewer.open) imageViewer.close();
  viewedImage.removeAttribute('src');
  for (const url of messageImageUrls) URL.revokeObjectURL(url);
  messageImageUrls.clear();
}

function appendMessageImage(message, file) {
  const url = URL.createObjectURL(file);
  messageImageUrls.add(url);
  const button = element('button', 'message-image');
  button.type = 'button';
  button.setAttribute('aria-label', 'Mở ảnh đính kèm');
  const image = document.createElement('img');
  image.src = url;
  image.alt = 'Ảnh đã gửi';
  button.append(image);
  button.addEventListener('click', () => {
    viewedImage.src = url;
    imageViewer.showModal();
  });
  message.append(button);
}

function savedImageNote(text) {
  return [imageHistoryNote, imageFollowupNote].find(note => text === note || text.endsWith(`\n\n${note}`));
}

async function loadProviderInfo() {
  try {
    const response = await fetch('/api/config', { cache: 'no-store' });
    if (!response.ok) return;
    const config = await response.json();
    if (!config.configured && !form.matches('[aria-busy="true"]') && chatMode.value === 'auto' && !input.value && !attachedImage && transcript.length === 0) {
      chatMode.value = 'local';
      updateChatMode();
    }
    const fallbackAfter = Number(config.free_fallback_after_seconds) || 15;
    providerLabel = config.paid_fallback_model
      ? `OpenRouter · Free trước, Qwen trả phí nếu chờ ${fallbackAfter}s`
      : providerLabelFor(config.provider, config.model);
    document.querySelectorAll('[data-provider-name]').forEach(node => {
      node.textContent = providerLabel;
      if (config.paid_fallback_model) {
        node.title = `Model miễn phí chạy trước. OpenRouter có thể gọi ${config.paid_fallback_model} tính phí nếu model miễn phí bị giới hạn, trả lời chưa hoàn tất hoặc quá ${fallbackAfter} giây.`;
      }
    });
  } catch { /* Keep neutral AI labels when configuration cannot be read. */ }
}
loadProviderInfo();
loadSavedConversations();

async function loadSavedConversations() {
  try {
    const res = await fetch('/api/conversations', { cache: 'no-store' });
    if (!res.ok) return;
    const data = await res.json();
    savedConversations.replaceChildren();
    for (const item of data.conversations || []) {
      const row = element('div', 'saved-row');
      const open = element('button', 'session-question saved-open', item.title);
      open.type = 'button'; open.title = item.title;
      open.addEventListener('click', () => openSavedConversation(item.id));
      const rename = element('button', 'saved-action', 'Đổi tên'); rename.type = 'button';
      rename.addEventListener('click', () => renameSavedConversation(item));
      const remove = element('button', 'saved-action saved-delete', 'Xóa'); remove.type = 'button';
      remove.addEventListener('click', () => deleteSavedConversation(item));
      row.append(open, rename, remove); savedConversations.append(row);
    }
    savedEmpty.hidden = (data.conversations || []).length > 0;
  } catch { /* Chat remains usable when local history is unavailable. */ }
}

async function openSavedConversation(id) {
  const openingRevision = conversationRevision;
  const openingRequest = ++openConversationRequest;
  try {
    const res = await fetch(`/api/conversations/${encodeURIComponent(id)}`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Không mở được cuộc trò chuyện đã lưu.');
    const data = await res.json();
    if (openingRevision !== conversationRevision || openingRequest !== openConversationRequest) return;
    conversationRevision++;
    clearAttachedImage();
    activeController?.abort(); activeController = null; activeCase = null; renderCaseBanner();
    clearMessageImages();
    messages.replaceChildren(); transcript.length = 0; chatHistory.length = 0;
    if (!activeConversationId) conversationImageContexts.delete(currentImageContextKey());
    activeConversationId = id;
    conversationHadImageContext = data.messages.some(item => item.role === 'user' && savedImageNote(item.content));
    renderImageContext(); setBusy(false); setSidebar(false);
    for (const [index, item] of data.messages.entries()) {
      const previous = data.messages[index - 1];
      const savedImageAnswer = item.role === 'assistant' && previous?.role === 'user'
        && savedImageNote(previous.content);
      const msg = bubble(item.role === 'user' ? 'user' : 'assistant');
      if (item.role === 'assistant') assistantLabel(msg, savedImageAnswer
        ? 'Đã lưu trên máy · phân tích ảnh chưa kiểm chứng' : 'Đã lưu trên máy · hội thoại học tập');
      const sourceCards = (item.sources || []).map(renderSource);
      if (item.role === 'assistant') msg.append(renderAnswer(item.content, savedImageAnswer ? [] : sourceCards));
      else {
        const file = savedMessageImages.get(id)?.get(item.id);
        const note = savedImageNote(item.content);
        const caption = note ? item.content.slice(0, -note.length).trimEnd() : item.content;
        if (file) appendMessageImage(msg, file);
        if (caption) msg.append(element('p', '', caption));
        if (!file && note === imageHistoryNote) {
          msg.append(element('p', 'message-meta', 'Ảnh không còn trong phiên này.'));
        }
      }
      if (item.role === 'assistant' && item.sources?.length) {
        const list = element('div', 'source-list');
        list.append(element('div', 'sources-heading', savedImageAnswer
          ? `TÀI LIỆU ĐỌC THÊM ĐÃ LƯU · ${item.sources.length}` : `NGUỒN ĐÃ LƯU · ${item.sources.length}`));
        if (savedImageAnswer) msg.append(element('p', 'message-meta',
          'Tài liệu đọc thêm không xác nhận dấu hiệu trên ảnh. Tệp ảnh không được lưu; hãy đính kèm lại để hỏi tiếp.'));
        sourceCards.forEach(card => list.append(card));
        msg.append(list);
      }
      transcript.push({ role: item.role === 'user' ? 'Bạn' : 'BoneScope', text: item.content, passages: item.sources || [] });
      const note = item.role === 'user' ? savedImageNote(item.content) : null;
      const content = note ? item.content.slice(0, -note.length).trimEnd() || defaultImagePrompt : item.content;
      chatHistory.push({ role: item.role, content });
    }
    exportButton.disabled = transcript.length === 0; scrollToLatest(); announce('Đã mở cuộc trò chuyện đã lưu.');
  } catch (error) { if (openingRequest === openConversationRequest) announce(error.message); }
}

async function renameSavedConversation(item) {
  const title = prompt('Tên mới cho cuộc trò chuyện:', item.title)?.trim();
  if (!title || title === item.title) return;
  const res = await fetch(`/api/conversations/${encodeURIComponent(item.id)}`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({title}) });
  if (res.ok) loadSavedConversations();
}

async function deleteSavedConversation(item) {
  if (!confirm(`Xóa vĩnh viễn cuộc trò chuyện “${item.title}” khỏi máy này?`)) return;
  const res = await fetch(`/api/conversations/${encodeURIComponent(item.id)}`, { method: 'DELETE' });
  if (res.ok) {
    conversationImageContexts.delete(`saved:${item.id}`);
    savedMessageImages.delete(item.id);
    if (activeConversationId === item.id) resetChat();
    loadSavedConversations(); announce('Đã xóa cuộc trò chuyện khỏi máy.');
  }
}

async function persistTurn(question, answer, sources = [], imageContextKey = null, messageImage = null) {
  const savingRevision = conversationRevision;
  const savingConversationId = activeConversationId;
  try {
    const res = await fetch('/api/conversations/turn', { method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({conversation_id:savingConversationId,question,answer,sources}), cache:'no-store' });
    if (!res.ok) throw new Error('Lưu lịch sử không thành công.');
    const { conversation_id: savedId, message_id: messageId } = await res.json();
    if (messageImage && Number.isInteger(messageId) && savingRevision === conversationRevision) {
      const images = savedMessageImages.get(savedId) || new Map();
      images.set(messageId, messageImage);
      savedMessageImages.set(savedId, images);
    }
    const savedImageContextKey = `saved:${savedId}`;
    if (imageContextKey && conversationImageContexts.has(imageContextKey)) {
      const file = conversationImageContexts.get(imageContextKey);
      conversationImageContexts.delete(imageContextKey);
      conversationImageContexts.set(savedImageContextKey, file);
    }
    if (savingRevision === conversationRevision && activeConversationId === savingConversationId) {
      activeConversationId = savedId;
      renderImageContext();
    }
    loadSavedConversations();
  } catch { announce('Câu trả lời đã hiển thị, nhưng chưa lưu được lịch sử SQLite.'); }
}

function setBusy(busy) {
  submit.disabled = busy;
  submit.hidden = busy;
  stop.hidden = !busy;
  input.disabled = busy;
  chatMode.disabled = busy;
  attachImage.disabled = busy || chatMode.value === 'local';
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
  clearAttachedImage();
  clearMessageImages();
  if (!activeConversationId) conversationImageContexts.delete(currentImageContextKey());
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
  activeConversationId = null;
  draftConversationContextKey = createDraftConversationContextKey();
  conversationHadImageContext = false;
  renderImageContext();
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
  if (suggestion.dataset.mode === 'local') {
    chatMode.value = 'local';
    updateChatMode();
  }
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
          source.classList.remove('is-highlighted');
          void source.offsetWidth;
          source.classList.add('is-highlighted');
          source.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
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
  if (!['greeting', 'out_of_scope', 'insufficient_evidence', 'candidates_found', 'conversation', 'case_explanation', 'image_chat'].includes(data.status)) throw new Error('Định dạng kết quả không hợp lệ.');
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
  if (data.basis === 'local_retrieval') {
    assistantLabel(answer, 'Tra cứu trên máy');
    answer.append(element('p', '', data.answer));
    const sources = element('div', 'source-list');
    sources.setAttribute('aria-label', 'Nguồn tham khảo');
    sources.append(element('div', 'sources-heading', `ĐOẠN NGUỒN THAM KHẢO · ${data.passages.length}`));
    sources.append(...data.passages.map(renderSource));
    answer.append(sources);
    announce(data.answer);
    return;
  }
  const isImageChat = data.status === 'image_chat';
  const isChat = data.status === 'conversation' || isImageChat;
  const isCaseExplain = data.status === 'case_explanation';
  if (!isCaseExplain && (!Array.isArray(data.passages)
    || (data.status === 'conversation' && data.passages.length !== 0)
    || (data.status === 'candidates_found' && !data.passages.length))) {
    throw new Error('Định dạng kết quả không hợp lệ.');
  }

  const answerProviderLabel = providerLabelFor(data.provider, data.model);
  let badge = `${answerProviderLabel} · ${isImageChat ? 'phân tích ảnh · chưa kiểm chứng' : isChat ? 'trò chuyện · kiến thức chung' : 'bản nháp chưa kiểm chứng'}`;
  if (data.case_context_used) badge += ' · ngữ cảnh ca ảnh';
  if (isCaseExplain) {
    badge = data.basis === 'documents'
      ? `${answerProviderLabel} · giải thích ca học tập · chưa kiểm chứng`
      : 'BoneScope · tóm tắt ca học tập (mẫu máy chủ)';
  }
  assistantLabel(answer, badge);
  const answerText = data.answer || 'Chưa tạo được câu trả lời.';
  const sourceCards = data.passages.map(renderSource);
  answer.append(renderAnswer(answerText, isImageChat ? [] : sourceCards));
  if (isImageChat && data.image_metadata_match) {
    const siteLabels = { 'hip bone': 'xương hông', pelvis: 'vùng chậu', 'hip-joint': 'khớp háng',
      'knee-joint': 'khớp gối', femur: 'xương đùi', humerus: 'xương cánh tay',
      tibia: 'xương chày', fibula: 'xương mác', ulna: 'xương trụ', radius: 'xương quay',
      hand: 'bàn tay', foot: 'bàn chân', 'ankle-joint': 'khớp cổ chân', 'elbow-joint': 'khớp khuỷu',
      'shoulder-joint': 'khớp vai', 'upper limb': 'chi trên', 'lower limb': 'chi dưới' };
    const match = data.image_metadata_match;
    const sites = (match.sites || []).map(site => siteLabels[site] || site).join(', ') || 'không có trường vị trí';
    const views = (match.views || []).join(', ') || 'không có trường tư thế';
    answer.append(element('p', 'message-meta',
      `Metadata BTXRD khớp SHA-256 với ${match.image_id}: ${sites}; tư thế ${views}. Đây là metadata nguồn, không phải kết luận AI nhìn thấy.`));
  }
  if (data.draft_error) {
    answer.append(element('p', 'message-meta', `Lưu ý bản nháp AI: ${data.draft_error}`));
  }
  const caveat = element('p', 'answer-caveat');
  caveat.append(icon('M12 3.5 20 18H4L12 3.5Z M12 9v4m0 2.5h.01'));
  caveat.append(document.createTextNode('Nội dung do AI tạo, chưa được kiểm chứng tự động. Hãy đối chiếu từng ý với nguồn bên dưới.'));
  if (isImageChat) {
    caveat.textContent = 'Phân tích ảnh do AI tạo, có thể sai; metadata không nhìn thấy trong ảnh không được suy đoán. Ảnh không được lưu vào lịch sử.';
    answer.append(caveat);
  } else if (!isChat && (!isCaseExplain || data.basis === 'documents')) answer.append(caveat);

  if (isImageChat && data.passages.length) {
    answer.append(element('p', 'message-meta',
      'Các nguồn dưới đây được tìm theo câu hỏi và phần mô tả ảnh. Đây là tài liệu đọc thêm, không xác nhận dấu hiệu trên ảnh hoặc chẩn đoán.'));
  }

  const sourceList = element('div', 'source-list');
  sourceList.setAttribute('aria-label', 'Nguồn tham khảo');
  sourceList.append(element('div', 'sources-heading', isImageChat
    ? `TÀI LIỆU LIÊN QUAN ĐỂ ĐỌC THÊM · ${data.passages.length}`
    : `ĐOẠN NGUỒN THAM KHẢO · ${data.passages.length}`));
  sourceCards.forEach(card => sourceList.append(card));
  if (sourceCards.length) answer.append(sourceList);
  else if (isImageChat) {
    const sourceNote = data.source_lookup_status === 'timeout'
      ? 'Phân tích ảnh hoàn tất, nhưng tra cứu nguồn bị quá thời gian. Bạn có thể hỏi lại sau.'
      : data.source_lookup_status === 'unavailable'
        ? 'Phân tích ảnh hoàn tất, nhưng kho tài liệu cục bộ hiện không truy xuất được.'
        : 'Chưa tìm thấy đoạn tài liệu phù hợp trong kho BoneScope. Điều này không xác nhận ảnh bình thường hay không có bất thường.';
    answer.append(element('p', 'message-meta', sourceNote));
  }

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
  announce(isImageChat
    ? data.passages.length
      ? `Đã nhận phân tích ảnh và ${data.passages.length} tài liệu liên quan.`
      : 'Đã nhận phân tích ảnh; chưa tìm thấy tài liệu liên quan trong kho.'
    : isChat ? 'Đã nhận phản hồi trò chuyện, không tra cứu kho tài liệu ở lượt này.'
      : `Đã tìm thấy câu trả lời và ${data.passages.length} đoạn nguồn tham khảo. Câu trả lời AI chưa được kiểm chứng.`);
}

function showError(message, question, imageFile = null, mode = chatMode.value, showAttachment = Boolean(imageFile)) {
  transcript.push({ role: 'BoneScope · Lỗi', text: message });
  const error = bubble('assistant', 'error-message');
  assistantLabel(error, 'Không thể hoàn tất yêu cầu');
  error.append(element('p', '', message));
  const retry = element('button', 'text-action', imageFile ? 'Thử lại với ảnh đã gửi' : 'Thử lại');
  retry.type = 'button';
  retry.append(icon('M20 7v5h-5M4 17v-5h5m-3.5-3A7 7 0 0 1 18 7l2 5M4 12l2 5a7 7 0 0 0 12.5-2'));
  retry.prepend(retry.lastChild);
  const retryRevision = conversationRevision;
  retry.addEventListener('click', () => {
    if (retryRevision === conversationRevision && chatMode.value === mode) {
      sendQuestion(question, imageFile, currentImageContextKey(), showAttachment);
    }
    else if (retryRevision === conversationRevision) announce('Chọn lại chế độ đã dùng để thử lại yêu cầu.');
  });
  error.append(retry);
  announce(message);
}

async function sendQuestion(question, newlyAttachedImage = null, imageContextKey = currentImageContextKey(), showAttachment = Boolean(newlyAttachedImage)) {
  if (submit.disabled) return;
  const mode = chatMode.value;
  const localLookup = mode === 'local';
  if (newlyAttachedImage && !localLookup) conversationImageContexts.set(imageContextKey, newlyAttachedImage);
  const imageFile = localLookup ? null : newlyAttachedImage || conversationImageContexts.get(imageContextKey) || null;
  if (!question && !imageFile) return;
  if (imageFile) conversationHadImageContext = true;
  const messageImage = showAttachment ? imageFile : null;
  const caption = question;
  question = caption || defaultImagePrompt;
  if (imageContextKey === currentImageContextKey()) renderImageContext(imageContextKey);
  stoppedByUser = false;
  const history = localLookup ? [] : boundedHistory(Boolean(imageFile));
  const revision = conversationRevision;
  if (messages.querySelector('.welcome-block')) messages.replaceChildren();
  const user = bubble('user');
  if (messageImage) appendMessageImage(user, messageImage);
  if (caption) user.append(element('p', '', caption));
  transcript.push({ role: 'Bạn', text: caption || 'Ảnh đính kèm' });
  exportButton.disabled = false;
  setBusy(true);
  const pending = bubble('assistant', 'pending-message');
  assistantLabel(pending, localLookup ? 'Đang tra cứu trên máy' : mode === 'auto' ? 'Đang suy nghĩ và trả lời' : 'Đang tra cứu và soạn bản nháp');
  const title = element('div', 'pending-title');
  title.append(element('span', 'spinner'));
  const progressText = element('span', '', 'Đang xử lý câu hỏi…');
  title.append(progressText);
  pending.append(title);
  pending.append(element('p', 'message-meta', localLookup ? 'Lần đầu có thể cần nạp mô hình tìm kiếm.'
    : mode === 'auto' ? `${providerLabel} đang đọc ngữ cảnh hội thoại. Câu hỏi về xương sẽ được tra cứu tài liệu.`
      : `${providerLabel} sẽ soạn bản nháp từ các đoạn tìm được.`));
  announce('Đang xử lý câu hỏi và ngữ cảnh hội thoại.');
  scrollToLatest();

  const controller = new AbortController();
  activeController = controller;
  const startedAt = Date.now();
  const progressTimer = setInterval(() => {
    progressText.textContent = `Đang xử lý câu hỏi · ${Math.floor((Date.now() - startedAt) / 1000)} giây`;
  }, 1000);
  // The query API allows 105s; leave time for its error/result to reach the UI.
  const timer = setTimeout(() => controller.abort(), imageFile ? 90000 : 110000);
  const payload = { question, history, mode };
  if (!localLookup && activeCase?.case_id) payload.case_id = activeCase.case_id;
  try {
    let response;
    if (imageFile) {
      progressText.textContent = 'Đang gửi ảnh tới AI để phân tích…';
      const formData = new FormData();
      formData.append('file', imageFile);
      formData.append('question', question);
      formData.append('history', JSON.stringify(history));
      response = await fetch('/api/image-chat', { method: 'POST', body: formData,
        cache: 'no-store', signal: controller.signal });
    } else {
      response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        cache: 'no-store',
        signal: controller.signal,
      });
    }
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
    const savedQuestion = imageFile
      ? [caption, messageImage ? imageHistoryNote : imageFollowupNote].filter(Boolean).join('\n\n') : question;
    await persistTurn(savedQuestion, data.answer || messages.lastElementChild.innerText, data.passages || [], imageContextKey, messageImage);
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
      } else showError(localLookup ? 'Tra cứu trên máy quá thời gian chờ. Hãy thử lại.'
        : `Đã hết thời gian chờ ${imageFile ? 'phân tích ảnh' : 'tra cứu và tạo bản nháp'}. Hãy kiểm tra kết nối ${providerLabel} hoặc thử lại sau.`, caption, imageFile, mode, showAttachment);
    } else {
      showError(error.message || 'Đã xảy ra lỗi khi tra cứu.', caption, imageFile, mode, showAttachment);
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

function setAttachedImage(file) {
  if (attachmentPreviewUrl) URL.revokeObjectURL(attachmentPreviewUrl);
  attachedImage = file;
  attachmentPreviewUrl = URL.createObjectURL(file);
  attachmentPreview.src = attachmentPreviewUrl;
  imageAttachment.hidden = false;
}

function clearAttachedImage() {
  attachedImage = null;
  imageInput.value = '';
  imageAttachment.hidden = true;
  attachmentPreview.removeAttribute('src');
  if (attachmentPreviewUrl) URL.revokeObjectURL(attachmentPreviewUrl);
  attachmentPreviewUrl = null;
}

function tryAttachImageFile(file) {
  if (!file) return false;
  if (chatMode.value === 'local') {
    announce('Chuyển sang chế độ AI để đính kèm ảnh.');
    return false;
  }
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    clearAttachedImage(); announce('Chỉ nhận ảnh JPEG, PNG hoặc WEBP.'); return false;
  }
  if (!file.size || file.size > 10 * 1024 * 1024) {
    clearAttachedImage(); announce('Ảnh phải có nội dung và không vượt quá 10 MiB.'); return false;
  }
  setAttachedImage(file);
  announce('Đã đính kèm ảnh. Khi gửi, ảnh sẽ được chuyển tới nhà cung cấp AI để phân tích.');
  return true;
}

function updateChatMode() {
  const localLookup = chatMode.value === 'local';
  if (localLookup) clearAttachedImage();
  attachImage.disabled = submit.disabled || localLookup;
  modeHint.textContent = localLookup
    ? 'Câu hỏi được tra cứu trên máy. Chuyển sang chế độ AI để gửi ảnh.'
    : 'Bản học tập. Khi gửi ảnh trong chế độ AI, ảnh được chuyển tới nhà cung cấp đã cấu hình.';
  renderImageContext();
  reattachImageContext.disabled = localLookup;
}
chatMode.addEventListener('change', updateChatMode);
attachImage.addEventListener('click', () => imageInput.click());
document.getElementById('remove-image-attachment').addEventListener('click', clearAttachedImage);
removeImageContext.addEventListener('click', () => {
  conversationImageContexts.delete(currentImageContextKey());
  renderImageContext();
  announce('Đã xóa ảnh khỏi ngữ cảnh cuộc trò chuyện hiện tại.');
});
reattachImageContext.addEventListener('click', () => imageInput.click());
imageInput.addEventListener('change', () => tryAttachImageFile(imageInput.files?.[0]));

input.addEventListener('paste', event => {
  const items = event.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      const file = item.getAsFile();
      if (file) {
        event.preventDefault();
        tryAttachImageFile(file);
        return;
      }
    }
  }
});

['dragenter', 'dragover'].forEach(type => form.addEventListener(type, event => {
  if (!event.dataTransfer?.types?.includes('Files')) return;
  event.preventDefault();
  form.classList.add('is-dragging');
}));
['dragleave', 'drop'].forEach(type => form.addEventListener(type, event => {
  form.classList.remove('is-dragging');
  if (type === 'drop' && event.dataTransfer?.files?.length) {
    event.preventDefault();
    tryAttachImageFile(event.dataTransfer.files[0]);
  }
}));

form.addEventListener('submit', event => {
  event.preventDefault();
  if (submit.disabled) return;
  const question = input.value.trim();
  if (!question && !attachedImage) return;
  const image = attachedImage;
  const imageContextKey = currentImageContextKey();
  clearAttachedImage();
  input.value = '';
  resizeInput();
  updateCounter();
  sendQuestion(question, image, imageContextKey);
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
  document.querySelector('meta[name="theme-color"]').content = isDark ? '#0b0e14' : '#f6f8fb';
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
  chunks.splice(1, 0, 'Đã xuất từ cuộc trò chuyện đang hiển thị. Hình ảnh X-quang và metadata ca không được lưu trong lịch sử chat.');
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
  referenceImageRequest++;
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
  caseImageMatchNote.textContent = '';
  askAiAboutCaseImage.hidden = true;
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

caseImage.addEventListener('change', async () => {
  referenceImageRequest++;
  showCaseError('');
  caseImageMatchNote.textContent = '';
  askAiAboutCaseImage.hidden = true;
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
    caseImageMatchNote.textContent = '';
    askAiAboutCaseImage.hidden = true;
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
  caseAge.value = '';
  caseGender.value = '';
  binaryControls.forEach(ctrl => { ctrl.value = ''; });
  expectedCaseImage = null;
  caseJsonNote.textContent = '';
  updateBinaryCounter();
  previewObjectUrl = URL.createObjectURL(file);
  casePreviewImg.hidden = false;
  casePreviewImg.src = previewObjectUrl;
  casePreviewName.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MiB`;
  caseImageLabel.textContent = file.name;
  casePreviewRow.hidden = false;
  caseImageMatchNote.textContent = 'Đang kiểm tra ảnh gốc trong BTXRD để tự ghép metadata…';
  askAiAboutCaseImage.hidden = true;
  try {
    const matchForm = new FormData();
    matchForm.append('file', file);
    const response = await fetch('/api/case/metadata-match', {
      method: 'POST', body: matchForm, cache: 'no-store'
    });
    if (!response.ok) throw new Error('Không kiểm tra được ảnh với chỉ mục BTXRD.');
    const match = await response.json();
    if (caseImage.files[0] !== file) return;
    if (match.matched) {
      const meta = validateMetadataObject(match.metadata);
      caseAge.value = String(meta.age);
      caseGender.value = meta.gender;
      BINARY_FIELDS.forEach(([key]) => { binaryControls.get(key).value = String(meta[key]); });
      expectedCaseImage = null;
      caseConfirmed.checked = false;
      updateBinaryCounter();
      caseImageMatchNote.textContent = `Khớp chính xác ${match.image_id}; đã lấy metadata từ BTXRD. Nhãn tham chiếu: ${match.ground_truth || 'không có'}. Checkpoint hiện cũng dùng BTXRD làm nguồn huấn luyện, nên đây không phải đánh giá độc lập.`;
    } else {
      caseImageMatchNote.textContent = match.reason === 'ambiguous_metadata'
        ? 'Ảnh trùng nội dung với nhiều dòng BTXRD nhưng metadata khác nhau. Không tự điền; cần đối chiếu nguồn gốc ảnh trước khi chạy Swin.'
        : 'Không khớp ảnh gốc trong BTXRD. Không thể tự suy ra tuổi/giới tính; chọn “Hỏi AI về ảnh” để nhận mô tả trực quan, hoặc nhập metadata có nguồn để chạy Swin.';
      askAiAboutCaseImage.hidden = !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024;
    }
  } catch (error) {
    if (caseImage.files[0] === file) {
      caseImageMatchNote.textContent = error.message;
      askAiAboutCaseImage.hidden = !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)
        || file.size > 10 * 1024 * 1024;
    }
  }
});

async function loadReferenceImage() {
  const imageId = caseReferenceId.value.trim().toUpperCase().replace(/\.JPEG$/, '');
  if (!/^IMG\d{6}$/.test(imageId)) {
    showCaseError('Nhập mã ảnh BTXRD dạng IMG000001.');
    return;
  }
  const requestId = ++referenceImageRequest;
  caseReferenceLoad.disabled = true;
  showCaseError('');
  caseImageMatchNote.textContent = `Đang nạp ${imageId} từ BTXRD cục bộ…`;
  try {
    const response = await fetch(`/api/reference-images/${imageId}`, { cache: 'no-store' });
    if (!response.ok) {
      let detail = 'Không tìm thấy ảnh này trong BTXRD cục bộ. Kiểm tra mã và thư mục dữ liệu.';
      try { const body = await response.json(); if (typeof body.detail === 'string') detail = body.detail; } catch { /* Keep fallback. */ }
      throw new Error(detail);
    }
    const blob = await response.blob();
    if (!caseDialog.open || requestId !== referenceImageRequest) return;
    const transfer = new DataTransfer();
    transfer.items.add(new File([blob], `${imageId}.jpeg`, { type: 'image/jpeg' }));
    caseImage.files = transfer.files;
    caseImage.dispatchEvent(new Event('change'));
  } catch (error) {
    if (caseDialog.open && requestId === referenceImageRequest) {
      caseImageMatchNote.textContent = '';
      showCaseError(error.message || 'Không nạp được ảnh BTXRD.');
    }
  } finally {
    caseReferenceLoad.disabled = false;
  }
}

caseReferenceLoad.addEventListener('click', loadReferenceImage);
document.querySelectorAll('.btxrd-sample-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    caseReferenceId.value = chip.dataset.btxrdId || '';
    loadReferenceImage();
  });
});
caseReferenceId.addEventListener('keydown', event => {
  if (event.key === 'Enter') { event.preventDefault(); loadReferenceImage(); }
});

askAiAboutCaseImage.addEventListener('click', () => {
  const file = caseImage.files[0];
  if (!file) return;
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024) {
    showCaseError('Luồng hỏi ảnh cần JPEG, PNG hoặc WEBP không quá 10 MiB.');
    return;
  }
  if (chatMode.value === 'local') {
    chatMode.value = 'auto';
    updateChatMode();
  }
  setAttachedImage(file);
  closeCaseModal();
  input.focus();
  announce('Ảnh được đính kèm. Khi gửi, ảnh sẽ được chuyển tới nhà cung cấp AI.');
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
    if (caseController.signal.aborted) throw new DOMException('Analysis cancelled', 'AbortError');
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

    renderCaseSummaryBubble(caseData, file.name);
    scrollToLatest();

    const explainMode = chatMode.value === 'local' ? 'local' : 'documents';
    setBusy(true);
    const revision = conversationRevision;
    const pending = bubble('assistant', 'pending-message');
    assistantLabel(pending, 'Đang đối chiếu kho tài liệu cho nhãn dự đoán');
    const pendingRow = element('div', 'pending-title');
    pendingRow.append(element('span', 'spinner'), element('span', '', explainMode === 'local'
      ? 'Đang tìm tài liệu trên máy…' : 'Đang tra cứu nguồn và tạo giải thích học thuật…'));
    pending.append(pendingRow);
    scrollToLatest();

    try {
      activeController = caseController;
      stoppedByUser = false;
      caseTimer = setTimeout(() => caseController?.abort(), 90000);
      const explainRes = await fetch(`/api/case/${encodeURIComponent(caseData.case_id)}/explain?mode=${explainMode}`, {
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
      if (caseController.signal.aborted) return;
      if (revision !== conversationRevision) return;
      pending.remove();
      renderResult(explainData);
      const assistantText = explainData.answer || messages.lastElementChild.innerText;
      chatHistory.push({ role: 'user', content: `Đã phân tích ca ảnh học tập; mô hình dự đoán Top-1 là ${caseData.top1} (${Number(caseData.top3?.[0]?.score ?? 0).toFixed(3)}). Hãy giải thích học thuật.` });
      chatHistory.push({ role: 'assistant', content: assistantText });
      transcript.push({ role: 'BoneScope', text: assistantText, passages: explainData.passages || [] });
      await persistTurn('Phân tích ca ảnh học tập. Không lưu ảnh, tên tệp hoặc metadata ca.', assistantText, explainData.passages || []);
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
