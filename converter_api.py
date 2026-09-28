"""
MC Builder Chart Converter API — v2
Accepts PNG (bitmap) or PDF (vector) uploads.
PDF is converted at 300 DPI for crisp chart text.
Deploy to Render.com: pip install -r requirements.txt, python converter_api.py
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, base64, io, os

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

def pdf_to_png(pdf_bytes, dpi=300):
    """Convert first page of PDF to PNG at given DPI using pypdfium2."""
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(pdf_bytes)
    page = pdf[0]
    scale = dpi / 72  # PDF points are 72/inch
    bitmap = page.render(scale=scale, rotation=0)
    pil_img = bitmap.to_pil()
    out = io.BytesIO()
    pil_img.save(out, 'PNG', optimize=True)
    w, h = pil_img.size
    return out.getvalue(), w, h

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
        self.wfile.write(json.dumps({'status':'ready','version':'2.0'}).encode())
    def do_POST(self):
        length = int(self.headers.get('Content-Length',0))
        body = json.loads(self.rfile.read(length)) if length else {}
        try:
            raw = base64.b64decode(body['image'])
            fmt = body.get('format','png').lower()

            if fmt == 'pdf':
                png_bytes, sw, sh = pdf_to_png(raw, dpi=300)
                out_w = sw
            else:
                png_bytes, sw, sh, out_w = upscale_png(raw)

            result = {
                'image': 'data:image/png;base64,' + base64.b64encode(png_bytes).decode(),
                'src_w': sw, 'src_h': sh, 'out_w': out_w,
                'dpi_est': round(sw / 3.74),
                'format': fmt
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
print(f'MC Converter v2 starting on port {port}')
HTTPServer(('0.0.0.0', port), Handler).serve_forever()
