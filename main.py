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
    raise RuntimeError("请在 .env 文件里设置 PIXIV_COOKIE")

USER_AGENT = "Mozilla/5.0"
app = Flask(__name__)


INDEX_HTML = """
<!doctype html>
<title>Pixiv 原图/GIF 下载</title>
<h2>输入 Pixiv 作品 PID<br>查看静图或动图 GIF</h2>
<form action="/pixiv" method="get">
  PID: <input name="pid" required>
  页码: <input name="page" value="0" style="width:3em">
  <button>查看</button>
</form>
"""

def fetch_json(api_url, referer):
    r = requests.get(api_url, headers={
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Cookie": PIXIV_COOKIE
    })
    r.raise_for_status()
    return r.json()

def fetch_original_pages(pid: str):
    api = f"https://www.pixiv.net/ajax/illust/{pid}/pages"
    body = fetch_json(api, f"https://www.pixiv.net/artworks/{pid}")\
           .get("body") or []
    return [p["urls"]["original"] for p in body]

def fetch_ugoira_meta(pid: str):
    api = f"https://www.pixiv.net/ajax/illust/{pid}/ugoira_meta"
    body = fetch_json(api, f"https://www.pixiv.net/artworks/{pid}")\
           .get("body") or {}
    return body["originalSrc"], body["frames"]

def make_gif_from_zip(zip_bytes: bytes, frames: list[dict]):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        images, durations = [], []
        for frame in frames:
            data = zf.read(frame["file"])
            img = Image.open(io.BytesIO(data)).convert("RGBA")
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
def pixiv_view():
    pid = request.args.get("pid","").strip()
    page = int(request.args.get("page","0") or 0)
    if not pid.isdigit():
        abort(400, "PID 必须为数字")

    # —— Ugoira 分支 —— #
    try:
        fetch_ugoira_meta(pid)
        img_src = url_for("pixiv_ugoira", pid=pid, _external=True)
        download_link = img_src  
        html = f"""
        <!doctype html>
        <html lang="zh-CN">
          <head><meta charset="utf-8"><title>Pixiv 动图 {pid}</title></head>
          <body style="margin:0;background:#000;text-align:center">
            <img src="{img_src}" style="max-width:100%;height:auto" alt="Ugoira {pid}">
            <p>
              <a href="{download_link}" download="{pid}.gif"
                 style="display:inline-block;margin:10px;padding:10px;
                        background:#fff;color:#000;text-decoration:none;
                        border-radius:4px;">
                点击下载为GIF文件
              </a>
            </p>
          </body>
        </html>
        """
        return html
    except Exception:
        pass

    # —— 静图分支 —— #
    pages = fetch_original_pages(pid)
    if page<0 or page>=len(pages):
        abort(404, "页码超范围")
    img_src = url_for("pixiv_proxy", pid=pid, page=page, _external=True)
    html = f"""
    <!doctype html>
    <html lang="zh-CN">
      <head><meta charset="utf-8"><title>Pixiv {pid} p{page}</title></head>
      <body style="margin:0;background:#000;text-align:center">
        <img src="{img_src}" style="max-width:100%;height:auto" alt="Pixiv {pid} p{page}">
      </body>
    </html>
    """
    return html

@app.route("/pixiv/proxy")
def pixiv_proxy():
    pid = request.args.get("pid","").strip()
    page = int(request.args.get("page","0") or 0)
    if not pid.isdigit():
        abort(400, "PID 必须为数字")
    pages = fetch_original_pages(pid)
    if page<0 or page>=len(pages):
        abort(404, "页码超范围")
    upstream = requests.get(
        pages[page],
        headers={
            "User-Agent": USER_AGENT,
            "Referer": f"https://www.pixiv.net/artworks/{pid}"
        },
        stream=True
    )
    upstream.raise_for_status()
    return Response(
        upstream.iter_content(8192),
        content_type=upstream.headers.get("Content-Type","image/png")
    )

@app.route("/pixiv/ugoira")
def pixiv_ugoira():
    pid = request.args.get("pid","").strip()
    if not pid.isdigit():
        abort(400, "PID 必须为数字")
    zip_url, frames = fetch_ugoira_meta(pid)
    upstream = requests.get(
        zip_url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": f"https://www.pixiv.net/artworks/{pid}"
        }
    )
    upstream.raise_for_status()
    gif_bytes = make_gif_from_zip(upstream.content, frames)
    # 强制以 attachment 方式返回，确保下载 URL 拿到的是真 GIF
    headers = {"Content-Disposition": f'attachment; filename="{pid}.gif"'}
    return Response(gif_bytes, content_type="image/gif", headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))
