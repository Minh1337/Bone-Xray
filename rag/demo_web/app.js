'use strict';
const form=document.getElementById('question-form');
const messages=document.getElementById('messages');
const input=document.getElementById('question');
const submit=document.getElementById('submit');
const clear=document.getElementById('clear-chat');
function resetChat(){messages.replaceChildren();line(messages,'p','Cuộc trò chuyện mới. Hãy nhập câu hỏi về tài liệu trong kho.','welcome');input.focus();}
clear.addEventListener('click',resetChat);
document.querySelectorAll('.suggestion').forEach(button=>button.addEventListener('click',()=>{input.value=button.textContent;form.requestSubmit();}));
function line(parent,tag,value,className){
  const node=document.createElement(tag);node.textContent=value;
  if(className)node.className=className;
  parent.append(node);return node;
}
function bubble(kind){const node=document.createElement('article');node.className=`message ${kind}`;messages.append(node);return node;}
function renderResult(data){
  const answer=bubble('assistant');
  if(data.answer_ready!==false)throw Error('Trạng thái kết quả không hợp lệ.');
  if(data.status==='greeting'){line(answer,'p',data.answer||'Xin chào!');return;}
  if(data.status==='out_of_scope'){line(answer,'p','Câu hỏi nằm ngoài phạm vi kho tài liệu hiện tại.');return;}
  if(data.status==='insufficient_evidence'){line(answer,'p','Chưa tìm được bằng chứng phù hợp hoặc câu hỏi cần chuyên gia đánh giá.');return;}
  if(data.status!=='candidates_found'||!Array.isArray(data.passages)||!data.passages.length)throw Error('Định dạng kết quả không hợp lệ.');
  line(answer,'p',data.answer||'Chưa tạo được câu trả lời.');
  line(answer,'p','Câu trả lời được tạo từ các đoạn dưới đây; hãy đối chiếu nguồn.','meta');
  for(const hit of data.passages){
    const card=document.createElement('section');card.className='source-card';
    line(card,'h3',hit.title||hit.source_id);
    line(card,'p',`${hit.publisher||''} · ${hit.section||''} · ${hit.chunk_id||''}`,'meta');
    line(card,'p',`Quyền nguồn: ${hit.license||'Chưa rõ'} · SHA-256: ${hit.text_sha256||'Chưa rõ'}`,'meta');
    line(card,'pre',hit.text||'');
    if(typeof hit.url==='string'&&/^https:\/\//i.test(hit.url)){
      const link=document.createElement('a');link.href=hit.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Mở nguồn gốc';card.append(link);
    }
    answer.append(card);
  }
}
form.addEventListener('submit',async event=>{
  event.preventDefault();const question=input.value.trim();if(!question)return;
  const user=bubble('user');line(user,'p',question);input.value='';submit.disabled=true;input.disabled=true;form.setAttribute('aria-busy','true');
  const pending=bubble('assistant');line(pending,'p','Đang tìm trong tài liệu…');
  try{
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),120000);
    line(pending,'p','Sau khi tìm được nguồn, tôi sẽ nhờ Gemini soạn câu trả lời…','meta');
    let response;
    try{response=await fetch('/api/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question}),cache:'no-store',signal:controller.signal});}
    finally{clearTimeout(timer);}
    if(!response.ok){let detail='Không thể tra cứu nguồn lúc này.';try{const body=await response.json();if(body.detail)detail=body.detail;}catch{}throw Error(detail);}
    const data=await response.json();pending.remove();renderResult(data);
  }catch(error){pending.remove();const message=error.name==='AbortError'?'Quá thời gian chờ phản hồi. Hãy thử lại hoặc kiểm tra kết nối.':(error.message||'Lỗi tra cứu.');line(bubble('assistant'),'p',message);}
  finally{submit.disabled=false;input.disabled=false;form.removeAttribute('aria-busy');input.focus();}
});
input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();form.requestSubmit();}});
