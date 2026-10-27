'use strict';
const $ = id => document.getElementById(id);
const binary = [
 ['hand','Bàn tay'],['ulna','Xương trụ'],['radius','Xương quay'],['humerus','Xương cánh tay'],
 ['foot','Bàn chân'],['tibia','Xương chày'],['fibula','Xương mác'],['femur','Xương đùi'],
 ['hip bone','Xương hông'],['ankle-joint','Khớp cổ chân'],['knee-joint','Khớp gối'],
 ['hip-joint','Khớp háng'],['elbow-joint','Khớp khuỷu'],['shoulder-joint','Khớp vai'],
 ['upper limb','Chi trên'],['lower limb','Chi dưới'],['pelvis','Vùng chậu'],
 ['frontal','Hướng thẳng'],['lateral','Hướng nghiêng'],['oblique','Hướng chếch']
];
const keys = ['age','gender', ...binary.map(x=>x[0])];
const labels = ['no-tumor','osteochondroma','multiple osteochondromas','simple bone cyst','giant cell tumor','osteofibroma','synovial osteochondroma','other bt','osteosarcoma','other mt'];
let selectedFile=null, objectUrl=null, importedCases=[], expectedImage=null, lastResult=null, busy=false, caseSaved=false;
const controls=new Map();
binary.forEach(([key,name],i)=>{
 const label=document.createElement('label');label.append(document.createTextNode(name));
 const small=document.createElement('small');small.textContent=key;label.append(small);
 const select=document.createElement('select');select.id=`meta-${i}`;select.required=true;select.setAttribute('aria-label',`${name} (${key})`);
 [['','Chưa nhập'],['0','0 — Không'],['1','1 — Có']].forEach(([value,text])=>select.add(new Option(text,value)));
 label.append(select);$('binary-fields').append(label);controls.set(key,select);
});
function count(){ $('completion').textContent=`${[...controls.values()].filter(x=>x.value!=='').length}/20 trường đã nhập`; }
function clearResult(){lastResult=null;caseSaved=false;$('result').hidden=true;$('empty-result').hidden=false;$('result-subtitle').textContent='Kết quả sẽ xuất hiện sau khi gửi ảnh.';hideSaveMessage();}
function error(text){$('message').textContent=text;$('message').hidden=false;}
function clearError(){$('message').hidden=true;$('message').textContent='';}
function changed(){clearResult();clearError();$('confirmed').checked=false;count();}
function showSaveMessage(text, isError){
  const el=$('save-message');el.textContent=text;el.hidden=false;
  el.className=isError?'save-message save-error':'save-message save-success';
}
function hideSaveMessage(){$('save-message').hidden=true;}
function validateMetadata(m){
 if(!m || typeof m!=='object' || Array.isArray(m) || Object.keys(m).length!==keys.length || keys.some(k=>!Object.hasOwn(m,k))) throw Error('Metadata phải chứa đúng 22 trường theo mẫu.');
 if(typeof m.age!=='number'||!Number.isFinite(m.age)||m.age<0||m.age>120) throw Error('Tuổi phải là số từ 0 đến 120.');
 if(!['M','F'].includes(m.gender)) throw Error('Giới tính phải là M hoặc F.');
 for(const [k] of binary) if(typeof m[k]!=='number'|| ![0,1].includes(m[k])) throw Error(`Trường ${k} phải là số 0 hoặc 1.`);
 return m;
}
function normalizedName(s){return String(s).replaceAll('\\','/').split('/').pop().toLowerCase().replace(/\.jpeg$/,'.jpg');}
function applyCase(index){
 const c=importedCases[index],m=validateMetadata(c.metadata);
 changed();$('age').value=m.age;$('gender').value=m.gender;
 for(const [k] of binary)controls.get(k).value=String(m[k]);
 expectedImage=c.image||null;
 $('import-note').textContent=expectedImage?`Đã nạp ${c.id || 'ca'}. Chọn ảnh tương ứng: ${expectedImage}. Vẫn cần kiểm tra đúng nội dung ảnh.`:'Đã nạp metadata. Hãy chọn và xác nhận ảnh tương ứng.';
 count();
}
$('metadata-file').addEventListener('change', async e=>{
 const file=e.target.files[0];if(!file)return;
 try{
  if(file.size>1024*1024)throw Error('Tệp metadata vượt quá 1 MiB. Chỉ chọn một vài ca kiểm thử.');
  const raw=JSON.parse((await file.text()).replace(/^\uFEFF/,''));
  const list=Array.isArray(raw)?raw:(raw.metadata?[raw]:[{metadata:raw}]);
  if(!list.length || list.length>100) throw Error('Tệp cần chứa từ 1 đến 100 ca.');
  list.forEach(c=>validateMetadata(c.metadata));
  importedCases=list;$('case-picker').replaceChildren();
  list.forEach((c,i)=>$('case-picker').add(new Option(`${c.id||'Ca '+(i+1)}${c.image?' · '+String(c.image).replaceAll('\\','/').split('/').pop():''}`,String(i))));
  $('case-picker-wrap').hidden=list.length===1;applyCase(0);
 }catch(err){error(`Không nạp được JSON: ${err.message}`);}
});
$('case-picker').addEventListener('change',e=>applyCase(Number(e.target.value)));
$('age').addEventListener('input',changed);$('gender').addEventListener('change',changed);
controls.forEach(c=>c.addEventListener('change',changed));
$('image').addEventListener('change', e=>{
 changed();selectedFile=null;
 if(objectUrl){URL.revokeObjectURL(objectUrl);objectUrl=null;}
 $('preview-wrap').hidden=true;$('preview').removeAttribute('src');$('preview-note').hidden=true;
 const f=e.target.files[0];if(!f)return;
 if(!/\.(jpe?g|png|bmp|tiff?)$/i.test(f.name)){error('Định dạng chưa hỗ trợ. Chọn JPG, PNG, BMP hoặc TIFF.');e.target.value='';return;}
 if(!f.size || f.size>30*1024*1024){error('Ảnh phải có nội dung và không vượt quá 30 MiB.');e.target.value='';return;}
 selectedFile=f;objectUrl=URL.createObjectURL(f);$('preview').hidden=false;$('preview').src=objectUrl;
 $('preview-wrap').hidden=false;$('image-name').textContent=`${f.name} · ${(f.size/1024/1024).toFixed(2)} MiB`;
});
$('preview').addEventListener('error',()=>{if(selectedFile){$('preview').hidden=true;$('preview-note').hidden=false;}});
async function checkHealth(){
 $('reconnect').disabled=true;
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
 try{
  const r=await fetch('/health',{signal:controller.signal,cache:'no-store'});if(!r.ok)throw Error();
  const d=await r.json();if(d.status!=='ready')throw Error();
  $('health').textContent=`Đã kết nối · ${d.device==='cuda'?'GPU':String(d.device).toUpperCase()}`;$('health').className='online';
 }catch{$('health').textContent='Chưa kết nối API';$('health').className='offline';}
 finally{clearTimeout(timer);$('reconnect').disabled=false;}
}
$('reconnect').addEventListener('click',checkHealth);
function validateResult(d){
 if(!d||!d.scores||Object.keys(d.scores).length!==10||labels.some(k=>!Object.hasOwn(d.scores,k)||typeof d.scores[k]!=='number'||!Number.isFinite(d.scores[k])||d.scores[k]<0||d.scores[k]>1))throw Error('API trả về điểm số không hợp lệ.');
 if(Math.abs(Object.values(d.scores).reduce((a,b)=>a+b,0)-1)>0.0001||!labels.includes(d.top1)||!Number.isFinite(d.prediction_seconds)||d.prediction_seconds<0)throw Error('Kết quả API không đúng cấu trúc mong đợi.');
 const ranked=Object.entries(d.scores).sort((a,b)=>b[1]-a[1]);
 if(ranked[0][0]!==d.top1)throw Error('Nhãn top-1 không khớp điểm số.');
 return ranked;
}
function render(d,ranked){
 const pct=v=>(v*100).toLocaleString('vi-VN',{minimumFractionDigits:2,maximumFractionDigits:2})+'%';
 $('empty-result').hidden=true;$('result').hidden=false;$('result-subtitle').textContent=`Ảnh: ${selectedFile.name}`;
 $('top-label').textContent=d.top1;$('top-score').textContent=pct(ranked[0][1]);
 $('top-three').replaceChildren();
 ranked.slice(0,3).forEach(([k,v],i)=>{const row=document.createElement('div');row.className='rank';const header=document.createElement('div');header.className='rank-heading';const name=document.createElement('span');name.textContent=`${String(i+1).padStart(2,'0')}  ${k}`;const score=document.createElement('strong');score.textContent=pct(v);header.append(name,score);const bar=document.createElement('div');bar.className='bar';const fill=document.createElement('span');fill.style.width=(v*100)+'%';bar.append(fill);row.append(header,bar);$('top-three').append(row);});
 $('duration').textContent=d.prediction_seconds.toFixed(3)+' giây';$('device').textContent=d.device==='cuda'?'GPU / CUDA':String(d.device).toUpperCase();
 $('all-scores').replaceChildren();ranked.forEach(([k,v])=>{const tr=document.createElement('tr');for(const text of [k,pct(v)]){const td=document.createElement('td');td.textContent=text;tr.append(td);}$('all-scores').append(tr);});
 // Reset save button
 caseSaved=false;
 $('save-case').disabled=false;
 $('save-case').textContent='💾 Lưu ca vào lịch sử';
}
$('analysis-form').addEventListener('submit',async e=>{
 e.preventDefault();if(busy)return;clearError();clearResult();
 let metadata;
 try{
  if(!selectedFile)throw Error('Hãy chọn ảnh trước khi phân tích.');
  if(expectedImage && normalizedName(expectedImage)!==normalizedName(selectedFile.name)) throw Error(`Metadata đã nạp thuộc ${expectedImage}. Hãy chọn đúng ảnh hoặc làm mới để nhập ca khác.`);
  metadata={age:Number($('age').value),gender:$('gender').value};
  if($('age').value==='')throw Error('Chưa nhập tuổi.');
  for(const [k] of binary){if(controls.get(k).value==='')throw Error(`Chưa nhập ${k}.`);metadata[k]=Number(controls.get(k).value);}
  validateMetadata(metadata);if(!$('confirmed').checked)throw Error('Hãy xác nhận ảnh và metadata thuộc cùng một ca.');
 }catch(err){error(err.message);return;}
 busy=true;$('inputs').disabled=true;$('loading').hidden=false;$('empty-result').hidden=true;$('result-subtitle').textContent='Đang chờ mô hình phản hồi…';
 const form=new FormData();form.append('file',selectedFile);form.append('metadata',JSON.stringify(metadata));
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),120000);
 try{
  const response=await fetch('/predict',{method:'POST',body:form,signal:controller.signal});
  let data;try{data=await response.json();}catch{throw Error('API không trả về JSON. Kiểm tra cửa sổ máy chủ.');}
  if(!response.ok){const messages={413:'Ảnh vượt giới hạn dung lượng hoặc kích thước.',415:'Ảnh hỏng hoặc định dạng chưa hỗ trợ.',422:'Ảnh hoặc metadata chưa hợp lệ.',429:'Mô hình đang xử lý yêu cầu khác. Đợi rồi thử lại.',500:'Mô hình gặp lỗi. Xem log trong cửa sổ máy chủ.',503:'Mô hình chưa sẵn sàng.'};throw Error((messages[response.status]||'Yêu cầu thất bại.')+(typeof data.detail==='string'?' '+data.detail:''));}
  const ranked=validateResult(data);lastResult={created_at:new Date().toISOString(),image_name:selectedFile.name,metadata,response:data};render(data,ranked);
 }catch(err){clearResult();error(err.name==='AbortError'?'Đã đợi quá 120 giây. Máy chủ có thể vẫn đang xử lý; kiểm tra log trước khi gửi lại.':err instanceof TypeError?'Không kết nối được API. Kiểm tra cửa sổ máy chủ vẫn đang mở.':err.message);}
 finally{clearTimeout(timer);busy=false;$('inputs').disabled=false;$('loading').hidden=true;}
});

// --- Save case to database ---
$('save-case').addEventListener('click', async ()=>{
 if(!lastResult || caseSaved) return;
 $('save-case').disabled=true;
 $('save-case').textContent='Đang lưu…';
 hideSaveMessage();
 try{
  const d=lastResult.response;
  const ranked=Object.entries(d.scores).sort((a,b)=>b[1]-a[1]);
  const body={
   image_filename: lastResult.image_name,
   image_sha256: d.image_sha256,
   metadata: lastResult.metadata,
   scores: d.scores,
   top1: d.top1,
   top1_score: ranked[0][1],
   prediction_seconds: d.prediction_seconds,
   device: d.device,
   model_sha256: d.model_sha256,
   api_version: d.api_version || '0.1.0',
  };
  const r=await fetch('/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!r.ok){const err=await r.json().catch(()=>({}));throw Error(err.detail||'Lỗi khi lưu ca');}
  const saved=await r.json();
  caseSaved=true;
  $('save-case').textContent='✅ Đã lưu';
  showSaveMessage(`Đã lưu ca ${saved.id}. Xem trong Lịch sử.`, false);
 }catch(err){
  $('save-case').disabled=false;
  $('save-case').textContent='💾 Lưu ca vào lịch sử';
  showSaveMessage(`Lỗi: ${err.message}`, true);
 }
});

$('reset').addEventListener('click',()=>{
 HTMLFormElement.prototype.reset.call($('analysis-form'));selectedFile=null;expectedImage=null;importedCases=[];
 if(objectUrl)URL.revokeObjectURL(objectUrl);objectUrl=null;
 $('preview').removeAttribute('src');$('preview-wrap').hidden=true;$('case-picker-wrap').hidden=true;$('case-picker').replaceChildren();$('import-note').textContent='';changed();
});
$('download').addEventListener('click',()=>{
 if(!lastResult)return;const blob=new Blob([JSON.stringify(lastResult,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='xray_ui_result_'+new Date().toISOString().replaceAll(':','-')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
count();checkHealth();
