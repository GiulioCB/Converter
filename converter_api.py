CONVERTER_APP_HTML = '''
<!DOCTYPE html>
<html>
<head>
<title>MC Chart Converter</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Calibre',Arial,sans-serif;background:#f0f1ef;min-height:100vh;display:flex;align-items:center;justify-content:center}
  :root{--green:#003F2D;--sage:#80BBAD;--accent:#17E88F;--light:#f0f1ef}

  /* Password screen */
  #pwScreen{background:#fff;border-radius:12px;padding:48px 40px;text-align:center;width:360px;box-shadow:0 4px 24px rgba(0,0,0,.10)}
  #pwScreen h1{color:var(--green);font-size:22px;margin-bottom:8px}
  #pwScreen p{color:#666;font-size:13px;margin-bottom:24px}
  #pwInput{width:100%;padding:12px;border:2px solid #ddd;border-radius:6px;font-size:16px;text-align:center;letter-spacing:4px;outline:none}
  #pwInput:focus{border-color:var(--sage)}
  #pwBtn{width:100%;margin-top:12px;padding:12px;background:var(--green);color:#fff;border:none;border-radius:6px;font-size:15px;cursor:pointer}
  #pwBtn:hover{background:#004d3a}
  #pwError{color:#c00;font-size:13px;margin-top:8px;display:none}

  /* Main app */
  #app{display:none;width:100%;max-width:960px;padding:24px}
  .header{background:var(--green);color:#fff;padding:16px 24px;border-radius:10px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
  .header h1{font-size:18px}
  .header p{font-size:12px;opacity:.7}
  .status-bar{background:#fff;border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:12px;color:#666;display:flex;align-items:center;gap:8px}
  .status-dot{width:8px;height:8px;border-radius:50%;background:#ccc}
  .status-dot.green{background:var(--accent)}
  .status-dot.orange{background:orange}

  .charts-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px}
  .chart-slot{background:#fff;border-radius:10px;padding:16px;border:2px dashed #ddd;transition:border-color .2s}
  .chart-slot.has-image{border-style:solid;border-color:var(--sage)}
  .chart-slot h3{font-size:13px;color:var(--green);margin-bottom:10px;font-weight:600}
  .paste-zone{background:#f8f9f8;border:2px dashed #ccc;border-radius:6px;padding:20px;text-align:center;font-size:12px;color:#888;cursor:pointer;min-height:90px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px}
  .paste-zone:focus{outline:none;border-color:var(--sage);background:#f0faf7}
  .paste-zone b{font-size:11px;color:var(--green)}
  .preview-img{width:100%;border-radius:4px;margin-top:8px;border:1px solid #eee}
  .chart-info{font-size:10px;color:#888;margin-top:4px;text-align:center}
  .chart-actions{display:flex;gap:6px;margin-top:8px}
  .btn-sm{flex:1;padding:6px;font-size:11px;border-radius:4px;cursor:pointer;border:1px solid}
  .btn-clear{color:#888;border-color:#ddd;background:#fff}
  .btn-clear:hover{background:#fee}
  .btn-send{color:#fff;border-color:var(--green);background:var(--green)}
  .btn-send:hover{background:#004d3a}
  .btn-send:disabled{opacity:.4;cursor:default}

  .bottom-bar{background:#fff;border-radius:10px;padding:16px 20px;display:flex;gap:12px;align-items:center}
  .btn-primary{padding:10px 24px;background:var(--green);color:#fff;border:none;border-radius:6px;font-size:14px;cursor:pointer}
  .btn-primary:hover{background:#004d3a}
  .btn-primary:disabled{opacity:.4;cursor:default}
  .note{font-size:12px;color:#888;flex:1}
  .converting{color:orange;font-weight:600}
  .success{color:green;font-weight:600}
  .error-msg{color:#c00;font-weight:600}
</style>
</head>
<body>

<!-- Password screen -->
<div id="pwScreen">
  <h1>🔒 MC Chart Converter</h1>
  <p>CBRE Research — Chart Image Tool</p>
  <input id="pwInput" type="password" placeholder="Password" autocomplete="off">
  <button id="pwBtn">Enter</button>
  <div id="pwError">Incorrect password</div>
</div>

<!-- Main app -->
<div id="app">
  <div class="header">
    <div>
      <h1>MC Chart Converter</h1>
      <p>Ctrl+C chart in Excel → click zone → Ctrl+V → Send to Builder</p>
    </div>
    <div style="font-size:11px;opacity:.7" id="serverStatus">Checking server…</div>
  </div>

  <div class="status-bar">
    <div class="status-dot" id="statusDot"></div>
    <span id="statusText">Connecting to conversion server…</span>
  </div>

  <div class="charts-grid" id="chartsGrid"></div>

  <div class="bottom-bar">
    <span class="note" id="bottomNote">Paste charts above, then send all to MC Builder.</span>
    <button class="btn-primary" id="sendAllBtn" disabled>Send All to MC Builder</button>
    <button class="btn-primary" style="background:#435254" id="closeBtn">Close Window</button>
  </div>
</div>

<script>
// ── Password ──────────────────────────────────────────────
var PASSWORD = 'CBRE';
var CONVERTER_URL = 'https://mc-converter.onrender.com';

function checkPw(){
  if(document.getElementById('pwInput').value === PASSWORD){
    document.getElementById('pwScreen').style.display = 'none';
    document.getElementById('app').style.display = 'block';
    init();
  } else {
    document.getElementById('pwError').style.display = 'block';
    document.getElementById('pwInput').value = '';
  }
}
document.getElementById('pwBtn').addEventListener('click', checkPw);
document.getElementById('pwInput').addEventListener('keydown', function(e){ if(e.key==='Enter') checkPw(); });

// ── Chart slots ───────────────────────────────────────────
var SLOTS = [
  {id:'c1', label:'Supply & Demand'},
  {id:'c2', label:'Market Performance'},
  {id:'c3', label:'Pipeline'},
];
var chartData = {}; // id -> {dataUrl, w, h}

function init(){
  checkServer();
  buildGrid();
  // Listen for opener (MC Builder window)
  window.addEventListener('message', function(e){
    if(e.data && e.data.type === 'MC_INIT'){
      document.getElementById('bottomNote').textContent = 'Connected to MC Builder — paste charts and send.';
    }
  });
  if(window.opener) window.opener.postMessage({type:'MC_CONVERTER_READY'}, '*');
}

function checkServer(){
  fetch(CONVERTER_URL, {method:'GET', mode:'cors'})
    .then(function(r){ return r.json(); })
    .then(function(d){
      document.getElementById('statusDot').className = 'status-dot green';
      document.getElementById('statusText').textContent = 'Conversion server ready (v' + (d.version||'?') + ')';
      document.getElementById('serverStatus').textContent = '✓ Server online';
    }).catch(function(){
      document.getElementById('statusDot').className = 'status-dot orange';
      document.getElementById('statusText').textContent = 'Server offline — SVG will render locally (lower quality)';
      document.getElementById('serverStatus').textContent = '⚠ Server offline';
    });
}

function buildGrid(){
  var grid = document.getElementById('chartsGrid');
  grid.innerHTML = '';
  SLOTS.forEach(function(slot){
    var div = document.createElement('div');
    div.className = 'chart-slot';
    div.id = 'slot_'+slot.id;
    div.innerHTML = '<h3>'+slot.label+'</h3>'
      + '<div class="paste-zone" id="zone_'+slot.id+'" tabindex="0">'
      + '<b>Click here</b><br>then Ctrl+V to paste<br><span style="font-size:10px;margin-top:4px">In Excel: Ctrl+C on chart</span>'
      + '</div>'
      + '<div class="chart-info" id="info_'+slot.id+'"></div>'
      + '<div class="chart-actions" id="actions_'+slot.id+'" style="display:none">'
      + '<button class="btn-sm btn-clear" onclick="clearSlot(\''+slot.id+'\')">✕ Clear</button>'
      + '<button class="btn-sm btn-send" onclick="sendOne(\''+slot.id+'\')">→ Send to Builder</button>'
      + '</div>';
    grid.appendChild(div);

    // Focus + paste on zone click
    var zone = document.getElementById('zone_'+slot.id);
    zone.addEventListener('click', function(){ zone.focus(); });
    zone.addEventListener('focus', function(){ zone.style.borderColor='#80BBAD'; });
    zone.addEventListener('blur',  function(){ zone.style.borderColor='#ccc'; });
    zone.addEventListener('paste', function(e){ handlePaste(e, slot.id); });
  });
}

function handlePaste(e, slotId){
  e.preventDefault();
  var cd = e.clipboardData || window.clipboardData;
  var items = cd.items;
  var note = document.getElementById('info_'+slotId);

  // Try SVG first (Excel Ctrl+C)
  for(var i=0;i<items.length;i++){
    if(items[i].type === 'image/svg+xml'){
      items[i].getAsString(function(svgStr){
        note.textContent = 'Converting SVG…';
        note.className = 'chart-info converting';
        convertSVG(svgStr, slotId);
      });
      return;
    }
  }
  // Fallback: PNG
  for(var i=0;i<items.length;i++){
    if(items[i].type.indexOf('image')===0){
      var file = items[i].getAsFile();
      var reader = new FileReader();
      reader.onload = function(ev){
        note.textContent = 'Upscaling PNG…';
        note.className = 'chart-info converting';
        convertPNG(ev.target.result, slotId);
      };
      reader.readAsDataURL(file);
      return;
    }
  }
  note.textContent = 'Nothing found — try Ctrl+C on the chart first';
  note.className = 'chart-info error-msg';
}

function convertSVG(svgStr, slotId){
  var b64 = btoa(unescape(encodeURIComponent(svgStr)));
  fetch(CONVERTER_URL, {
    method:'POST', mode:'cors',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({image: b64, format:'svg'})
  }).then(function(r){ return r.json(); })
    .then(function(data){
      if(data.error) throw new Error(data.error);
      setSlotImage(slotId, data.image, data.out_w, data.src_h, 'server');
    }).catch(function(){
      // Local SVG fallback
      var blob = new Blob([svgStr], {type:'image/svg+xml'});
      var url = URL.createObjectURL(blob);
      var img = new Image();
      img.onload = function(){
        var cv = document.createElement('canvas');
        var scale = 2400 / img.width;
        cv.width = Math.round(img.width*scale);
        cv.height = Math.round(img.height*scale);
        cv.getContext('2d').drawImage(img,0,0,cv.width,cv.height);
        URL.revokeObjectURL(url);
        setSlotImage(slotId, cv.toDataURL('image/png'), cv.width, cv.height, 'local');
      };
      img.src = url;
    });
}

function convertPNG(dataUrl, slotId){
  var b64 = dataUrl.split(',')[1];
  fetch(CONVERTER_URL, {
    method:'POST', mode:'cors',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({image: b64, format:'png'})
  }).then(function(r){ return r.json(); })
    .then(function(data){
      if(data.error) throw new Error(data.error);
      setSlotImage(slotId, data.image, data.out_w, data.src_h, 'server');
    }).catch(function(){
      setSlotImage(slotId, dataUrl, null, null, 'local-only');
    });
}

function setSlotImage(slotId, dataUrl, w, h, source){
  chartData[slotId] = {dataUrl: dataUrl, w: w, h: h};
  var zone = document.getElementById('zone_'+slotId);
  zone.innerHTML = '<img class="preview-img" src="'+dataUrl+'">';
  zone.style.padding = '4px';
  document.getElementById('slot_'+slotId).className = 'chart-slot has-image';
  var info = document.getElementById('info_'+slotId);
  info.textContent = (w && h ? w+'×'+h+'px · ' : '') + (source==='server'?'✓ Server converted':'⚠ Local render');
  info.className = 'chart-info ' + (source==='server'?'success':'converting');
  document.getElementById('actions_'+slotId).style.display = 'flex';
  updateSendAll();
}

function clearSlot(slotId){
  delete chartData[slotId];
  var zone = document.getElementById('zone_'+slotId);
  var slot = SLOTS.find(function(s){ return s.id===slotId; });
  zone.innerHTML = '<b>Click here</b><br>then Ctrl+V to paste<br><span style="font-size:10px;margin-top:4px">In Excel: Ctrl+C on chart</span>';
  zone.style.padding = '20px';
  document.getElementById('slot_'+slotId).className = 'chart-slot';
  document.getElementById('info_'+slotId).textContent = '';
  document.getElementById('actions_'+slotId).style.display = 'none';
  updateSendAll();
}

function sendOne(slotId){
  if(!chartData[slotId]) return;
  if(window.opener){
    window.opener.postMessage({type:'MC_CHART_IMAGE', chartId: slotId, image: chartData[slotId].dataUrl}, '*');
    var info = document.getElementById('info_'+slotId);
    info.textContent += ' · Sent ✓';
  } else {
    alert('MC Builder window not found — open this from the MC Builder tool.');
  }
}

function updateSendAll(){
  var hasAny = Object.keys(chartData).length > 0;
  document.getElementById('sendAllBtn').disabled = !hasAny;
}

document.getElementById('sendAllBtn').addEventListener('click', function(){
  Object.keys(chartData).forEach(function(id){ sendOne(id); });
  document.getElementById('bottomNote').textContent = 'All charts sent to MC Builder ✓';
  setTimeout(function(){ window.close(); }, 1500);
});

document.getElementById('closeBtn').addEventListener('click', function(){ window.close(); });
</script>
</body>
</html>

'''

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, base64, io, os

def svg_to_png(svg_bytes, target_w=2400):
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
        f.write(svg_bytes); tmp = f.name
    drawing = svg2rlg(tmp)
    os.unlink(tmp)
    scale = target_w / drawing.width
    drawing.width = target_w
    drawing.height = drawing.height * scale
    drawing.transform = (scale, 0, 0, scale, 0, 0)
    png_bytes = renderPM.drawToString(drawing, fmt='PNG')
    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes))
    w, h = img.size
    out = io.BytesIO(); img.save(out, 'PNG', optimize=True)
    return out.getvalue(), w, h

def upscale_png(png_bytes, target_w=2400):
    from PIL import Image, ImageFilter, ImageEnhance
    img = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    w, h = img.size
    if w >= target_w:
        out = io.BytesIO(); img.save(out,'PNG'); return out.getvalue(), w, h, w
    scale = target_w / w
    new_w, new_h = round(w*scale), round(h*scale)
    step1 = img.resize((w*2, h*2), Image.LANCZOS)
    step2 = step1.resize((new_w, new_h), Image.LANCZOS)
    step3 = step2.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=2))
    step4 = ImageEnhance.Contrast(step3).enhance(1.08)
    out = io.BytesIO(); step4.save(out,'PNG',optimize=True)
    return out.getvalue(), w, h, new_w

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST,GET,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
    def do_OPTIONS(self):
        self.send_response(200); self.send_cors(); self.end_headers()
    def do_GET(self):
        if self.path == '/app':
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_cors(); self.end_headers()
            self.wfile.write(CONVERTER_APP_HTML.encode('utf-8'))
            return
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_cors(); self.end_headers()
        self.wfile.write(json.dumps({'status':'ready','version':'3.2'}).encode())
    def do_POST(self):
        length = int(self.headers.get('Content-Length',0))
        body = json.loads(self.rfile.read(length)) if length else {}
        try:
            fmt = body.get('format','png').lower()
            raw = base64.b64decode(body['image'])
            if fmt == 'svg':
                png_bytes, sw, sh = svg_to_png(raw, target_w=2400)
                out_w = sw
            else:
                png_bytes, sw, sh, out_w = upscale_png(raw)
            result = {
                'image': 'data:image/png;base64,' + base64.b64encode(png_bytes).decode(),
                'src_w': sw, 'src_h': sh, 'out_w': out_w, 'format': fmt
            }
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_cors(); self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type','application/json')
            self.send_cors(); self.end_headers()
            self.wfile.write(json.dumps({'error':str(e)}).encode())

port = int(os.environ.get('PORT', 8765))
print(f'MC Converter v3.1 starting on port {port}')
HTTPServer(('0.0.0.0', port), Handler).serve_forever()
