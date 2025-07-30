## how to run 
1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/pixiv-web.git
   cd pixiv-web
   ```

2. **Create and activate a Python virtual environment**

   ```bash
   python3 -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your Pixiv login cookie**

   * Log in to [https://www.pixiv.net](https://www.pixiv.net) in your browser.
   * Open Developer Tools → Application → Cookies → `pixiv.net`.
   * Copy the values for `PHPSESSID` and `device_token`.
   * Create a file named `.env` in the project root with:

     ```dotenv
     PIXIV_COOKIE=PHPSESSID=your_php_sessid; device_token=your_device_token
     ```

5. **Start the server**

   ```bash
   python app.py
   ```

6. **Access in your browser or on mobile**

   * Static image:

     ```
     http://<your-host>:5000/pixiv?pid=STATIC_PID&page=0
     ```
   * Animated Ugoira GIF:

     ```
     http://<your-host>:5000/pixiv?pid=UGOIRA_PID
     ```

   You will see the image (or animated GIF) inline, with a download button for the GIF.

## 如何运行

1. **克隆项目**

   ```bash
   git clone https://github.com/your-username/pixiv-web.git
   cd pixiv-web
   ```

2. **创建并激活虚拟环境**

   ```bash
   python3 -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

4. **配置 Pixiv 登录 Cookie**

   * 在浏览器登录 [https://www.pixiv.net](https://www.pixiv.net)
   * 打开开发者工具 → Application → Cookies → `pixiv.net`
   * 复制 `PHPSESSID` 和 `device_token` 的值
   * 在项目根目录新建 `.env`，写入：

     ```dotenv
     PIXIV_COOKIE=PHPSESSID=你的_PHPSESSID_值; device_token=你的_device_token_值
     ```

5. **启动服务**

   ```bash
   python app.py
   ```

6. **访问并下载**

   * **静态图片**：

     ```
     http://<服务器地址>:5000/pixiv?pid=静图PID&page=0
     ```
   * **动图（Ugoira）GIF**：

     ```
     http://<服务器地址>:5000/pixiv?pid=动图PID
     ```

   页面会内嵌展示静图或动图，并在动图下方提供“下载 GIF”按钮，长按或点击即可保存到本地。

