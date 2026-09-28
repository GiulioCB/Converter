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
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_cors(); self.end_headers()
        self.wfile.write(json.dumps({'status':'ready','version':'3.1'}).encode())
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
