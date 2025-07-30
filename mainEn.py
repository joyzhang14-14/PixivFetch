import os
import io
import zipfile
from flask import (
    Flask, request, Response, render_template_string,
    abort, url_for
)
import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
PIXIV_COOKIE = os.getenv("PIXIV_COOKIE")
if not PIXIV_COOKIE:
    raise RuntimeError("Please set PIXIV_COOKIE in your .env file")

USER_AGENT = "Mozilla/5.0"
app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<title>Pixiv Image/GIF Viewer</title>
<h2>Enter Pixiv Illustration ID (PID)<br>to view static image or animated GIF</h2>
<form action="/pixiv" method="get">
  PID: <input name="pid" required>
  Page: <input name="page" value="0" style="width:3em">
  <button>View</button>
</form>
"""

def fetch_json(url, referer):
    resp = requests.get(url, headers={
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Cookie": PIXIV_COOKIE
    })
    resp.raise_for_status()
    return resp.json()

def fetch_static_pages(pid: str):
    api = f"https://www.pixiv.net/ajax/illust/{pid}/pages"
    data = fetch_json(api, f"https://www.pixiv.net/artworks/{pid}") \
           .get("body", [])
    return [p["urls"]["original"] for p in data]

def fetch_ugoira_metadata(pid: str):
    api = f"https://www.pixiv.net/ajax/illust/{pid}/ugoira_meta"
    data = fetch_json(api, f"https://www.pixiv.net/artworks/{pid}") \
           .get("body", {})
    return data["originalSrc"], data["frames"]

def create_gif(zip_bytes: bytes, frames: list[dict]):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        images, durations = [], []
        for frame in frames:
            img_data = z.read(frame["file"])
            img = Image.open(io.BytesIO(img_data)).convert("RGBA")
            images.append(img)
            durations.append(frame["delay"])
    buf = io.BytesIO()
    images[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        disposal=2
    )
    buf.seek(0)
    return buf.getvalue()

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/pixiv")
def view_pixiv():
    pid = request.args.get("pid", "").strip()
    try:
        page = int(request.args.get("page", "0"))
    except ValueError:
        page = 0
    if not pid.isdigit():
        abort(400, "PID must be numeric")

    # Try Ugoira (animated) first
    try:
        fetch_ugoira_metadata(pid)
        img_url = url_for("serve_ugoira", pid=pid, _external=True)
        html = f"""
        <!doctype html>
        <html lang="en">
          <head><meta charset="utf-8"><title>Pixiv Ugoira {pid}</title></head>
          <body style="margin:0; background:#000; text-align:center">
            <img src="{img_url}" style="max-width:100%;height:auto" alt="Pixiv Ugoira {pid}">
            <p>
              <a href="{img_url}" download="{pid}.gif"
                 style="display:inline-block; margin:10px; padding:10px;
                        background:#fff; color:#000; text-decoration:none;
                        border-radius:4px;">
                ⬇️ Download as GIF
              </a>
            </p>
          </body>
        </html>
        """
        return html
    except Exception:
        pass

    # Otherwise static image
    pages = fetch_static_pages(pid)
    if page < 0 or page >= len(pages):
        abort(404, "Page out of range")
    img_url = url_for("serve_static", pid=pid, page=page, _external=True)
    html = f"""
    <!doctype html>
    <html lang="en">
      <head><meta charset="utf-8"><title>Pixiv {pid} p{page}</title></head>
      <body style="margin:0; background:#000; text-align:center">
        <img src="{img_url}" style="max-width:100%;height:auto" alt="Pixiv {pid} p{page}">
      </body>
    </html>
    """
    return html

@app.route("/pixiv/proxy")
def serve_static():
    pid = request.args.get("pid","").strip()
    page = int(request.args.get("page","0") or 0)
    if not pid.isdigit():
        abort(400, "PID must be numeric")
    pages = fetch_static_pages(pid)
    if page < 0 or page >= len(pages):
        abort(404, "Page out of range")
    resp = requests.get(
        pages[page],
        headers={
            "User-Agent": USER_AGENT,
            "Referer": f"https://www.pixiv.net/artworks/{pid}"
        },
        stream=True
    )
    resp.raise_for_status()
    return Response(
        resp.iter_content(8192),
        content_type=resp.headers.get("Content-Type","image/png")
    )

@app.route("/pixiv/ugoira")
def serve_ugoira():
    pid = request.args.get("pid","").strip()
    if not pid.isdigit():
        abort(400, "PID must be numeric")
    zip_url, frames = fetch_ugoira_metadata(pid)
    resp = requests.get(zip_url, headers={
        "User-Agent": USER_AGENT,
        "Referer": f"https://www.pixiv.net/artworks/{pid}"
    })
    resp.raise_for_status()
    gif_data = create_gif(resp.content, frames)
    headers = {"Content-Disposition": f'attachment; filename="{pid}.gif"'}
    return Response(gif_data, content_type="image/gif", headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
