import json
import mimetypes
import os
import random
import re
import requests
import time
import glob

# %% [Setup]
TOKEN_FILE = "token_cache.json"
BOOK_CACHE_FILE = "book_cache.json"
QUEUE_INFO_FILE = "queue_info.json"
TOKEN_EXPIRES_IN = 86400
ALLOWED_MIME_TYPES = {
    'image/jpeg',      # JPG / JPEG
    'image/png',       # PNG
    'application/pdf', # PDF
    'application/x-zip-compressed'  # ZIP
}
FILENAME_PATTERN = re.compile(r'^[A-Za-z0-9_\-\.]+$')  # 僅允許英數、底線、減號、點

# ==============================
# NEW: Result file renaming config
# ==============================

# Template for output basenames (without extension)
# Available fields:
#   {original}  -> original uploaded filename without extension (if known)
#   {guid}      -> guid integer
#   {index}     -> 1-based index within the uploaded file's returned guid list (if known)
RESULT_NAME_TEMPLATE = "{original}_guid{guid}"

# Optional: JSON map guid -> desired basename (highest priority)
# Example rename_map.json:
# { "1147409": "MyBook_Page0012", "1143651": "MyBook_Page0013" }
RENAME_MAP_FILE = "rename_map.json"

# Optional: rename already-downloaded files in DOWNLOAD_DIR (without downloading again)
RENAME_EXISTING_DOWNLOADS = False
RENAME_DRY_RUN = False  # True: preview only; False: actually rename


_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}
_ILLEGAL_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]')


def sanitize_filename(name: str, replacement: str = "_", max_len: int = 150) -> str:
    """
    Safe on Windows/macOS/Linux. Keeps Unicode (e.g., Chinese) but removes illegal filesystem chars.
    """
    name = _ILLEGAL_CHARS_RE.sub(replacement, name)
    name = name.strip().rstrip(".")  # Windows hates trailing dots
    if not name:
        name = "untitled"

    base = os.path.splitext(name)[0].upper()
    if base in _WINDOWS_RESERVED:
        name = "_" + name

    if len(name) > max_len:
        root, ext = os.path.splitext(name)
        name = root[: max_len - len(ext)] + ext

    return name


def ensure_unique_path(path: str) -> str:
    """
    If path exists, append _1, _2, ... before extension.
    """
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    k = 1
    while True:
        candidate = f"{root}_{k}{ext}"
        if not os.path.exists(candidate):
            return candidate
        k += 1


def load_rename_map(path: str) -> dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # normalize keys to str
    return {str(k): str(v) for k, v in data.items()}


def render_result_basename(template: str, *, guid: int, original: str = None, index: int = None, rename_map: dict = None) -> str:
    """
    Priority:
      1) rename_map[str(guid)] if provided
      2) template rendered with fields
      3) fallback to guid only
    """
    if rename_map and str(guid) in rename_map and rename_map[str(guid)].strip():
        base = rename_map[str(guid)].strip()
    else:
        original = original or f"guid_{guid}"
        idx = 1 if index is None else int(index)
        try:
            base = template.format(original=original, guid=guid, index=idx)
        except Exception:
            base = f"{original}_{guid}"

    return sanitize_filename(base)


def find_existing_files_for_guid(download_dir: str, guid: int) -> list[str]:
    """
    Find downloaded files likely belonging to this GUID.
    Matches:
      - guid_<guid>.<ext>
      - *_<guid>.<ext>
      - *_guid<guid>.<ext>
    """
    patterns = [
        os.path.join(download_dir, f"guid_{guid}.*"),
        os.path.join(download_dir, f"*_{guid}.*"),
        os.path.join(download_dir, f"*guid{guid}.*"),
    ]
    out = []
    for p in patterns:
        out.extend(glob.glob(p))
    return sorted(set(out))


class ASCDCOCRClient:
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.no_auth_headers = self._make_headers(auth=False)
        self.token = self.load_or_login()
        self.session.headers.update(self._make_headers(auth=True))

    def _make_headers(self, auth=True):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://ocr.ascdc.tw/",
            "Origin": "https://ocr.ascdc.tw",
        }
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def wait_random(self, min_sec=0.5, max_sec=1.5, label=""):
        delay = random.uniform(min_sec, max_sec)
        print(f"Waiting {delay:.2f}s {label}...")
        time.sleep(delay)

    def safe_json(self, response, context=""):
        try:
            return response.json()
        except Exception as e:
            print(f"[{context}] JSON parse error. Status {response.status_code}")
            try:
                print(response.content.decode("utf-8"))
            except:
                print(response.content)
            raise e

    def debug_response(self, response):
        print("Response Debug Info")
        print("=" * 40)
        print(f"Status Code: {response.status_code}")
        print(f"Headers:\n{json.dumps(dict(response.headers), indent=2)}")
        print(f"Content Length: {len(response.content)} bytes")
        try:
            print(response.content.decode("utf-8")[:1000])
        except UnicodeDecodeError:
            print(response.content[:100])
        print("=" * 40)

    def load_or_login(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if time.time() < data.get("expires_at", 0):
                    print("Using cached token.")
                    return data["token"]
        return self.login()

    def login(self):
        url = "https://ocr.ascdc.tw/web_api/auth.php"
        payload = {"account": self.account, "password": self.password}
        response = self.session.post(url, data=payload, headers=self.no_auth_headers)
        data = self.safe_json(response, "Login")
        if data.get("status") == 200:
            token = data["access_token"]
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump({"token": token, "expires_at": int(time.time()) + TOKEN_EXPIRES_IN}, f)
            print("Login successful.")
            return token
        raise Exception(f"Login failed: {data.get('message')}")

    def create_book(self, title, author, is_public=0, orientation=2):
        url = "https://ocr.ascdc.tw/web_api/create_book.php"
        payload = {
            "token": self.token,
            "title": title,
            "author": author,
            "public": is_public,
            "orientation": orientation
        }
        response = self.session.post(url, data=payload, headers=self.no_auth_headers)
        return self.safe_json(response, "Create Book")

    def get_result(self, guid):
        url = "https://ocr.ascdc.tw/web_api/query.php"
        response = self.session.post(url, data={"guid": int(guid)})
        data = self.safe_json(response, "Get Result")
        if data.get("status") == 200:
            return data["result"]
        raise Exception(f"Result error: {data.get('message')}")

    def get_image(self, guid):
        url = "https://ocr.ascdc.tw/web_api/get_image.php"
        response = self.session.post(url, data={"guid": int(guid)})
        data = self.safe_json(response, "Get Image")
        if data.get("status") == 200:
            return data["result"]
        raise Exception(f"Result error:\n{json.dumps(data, indent=2, ensure_ascii=False)}")


    def upload_file(self, file_name, bookid, block_order="TBRL"):
        url = "https://ocr.ascdc.tw/web_api/upload.php"

        base_name = os.path.basename(file_name)
        # Check if file name is allowed
        if not FILENAME_PATTERN.match(base_name):
            raise ValueError(f"❌ Illegal file name: {base_name}. Only A-Z, a-z, 0-9, '_', '-', and '.' are allowed.")

        mime_type, _ = mimetypes.guess_type(base_name)
        # Check if MIME type is allowed
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"❌ Unsupported MIME type: {mime_type}. Allowed types are: {', '.join(ALLOWED_MIME_TYPES)}")

        with open(file_name, 'rb') as f:
            files = {'page': (os.path.basename(file_name), f, mime_type)}
            data = {
                'token': self.token,
                'bookid': bookid,
                'block_order': str(block_order).upper()
            }
            response = self.session.post(url, data=data, files=files, headers=self.no_auth_headers)
        return self.safe_json(response, "Upload")

    def poll_ocr_queue(self, queue_id):
        url = "https://ocr.ascdc.tw/web_api/queue.php"
        while True:
            response = self.session.post(url, data={"queue_id": queue_id})
            data = self.safe_json(response, "Queue")
            if data.get("status") == 103:
                print("OCR processing...")
                time.sleep(60)
            elif data.get("status") == 200:
                return data["guids"]
            else:
                raise Exception(f"OCR queue failed: {data.get('message')}")


class Book:
    def __init__(self, client, title=None, author=None, is_public=0, orientation=2, bookid=None):
        self.client = client
        if bookid is not None:
            self.bookid = int(bookid)
            self.title = title
            self.author = author
            self.public = is_public
            self.orientation = orientation
            self.key = f"{title}::{author}" if title and author else None
            print(f"📕 Using existing book ID: {self.bookid}")
            if self.key:
                cache = self._load_cache()
                if self.key not in cache:
                    cache[self.key] = self.bookid
                    self._save_cache(cache)
                    print(f"📝 Cached manually provided book ID for: {self.key}")
        else:
            if not title or not author:
                raise ValueError("Title and author must be provided if bookid is not specified.")
            self.title = title
            self.author = author
            self.key = f"{title}::{author}"
            self.bookid = int(self._get_or_create_book(is_public, orientation))

    def _load_cache(self):
        if os.path.exists(BOOK_CACHE_FILE):
            with open(BOOK_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_cache(self, cache):
        with open(BOOK_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)

    def _get_or_create_book(self, is_public, orientation):
        cache = self._load_cache()
        if self.key in cache:
            print(f"Book exists: {self.title}")
            return cache[self.key]

        data = self.client.create_book(self.title, self.author, is_public, orientation)
        if data.get("status") == 200:
            cache[self.key] = data["bookid"]
            print(f"Book created: {self.title} (ID: {data['bookid']})")
            self._save_cache(cache)
            return data["bookid"]
        raise Exception(f"Book creation failed: {data.get('message')}")


class File:
    def __init__(self, client, bookid, file_name, block_order='TBRL', language=1, orientation=2, correction=-1,
                 pages_per_img=1, remove_margin=-1, has_mark=False, has_alphabet=False, remove_anno=False, is_inverted=False):
        self.client = client
        self.bookid = int(bookid)
        self.file_name = file_name
        self.queue_id = None
        self.guids = []
        self.block_order = block_order.upper()
        self.language = int(language)
        self.orientation = int(orientation)
        self.correction = int(correction)
        self.pages_per_img = int(pages_per_img)
        self.remove_margin = int(remove_margin)
        self.has_mark = bool(has_mark)
        self.has_alphabet = bool(has_alphabet)
        self.remove_anno = bool(remove_anno)
        self.is_inverted = bool(is_inverted)

    def upload(self):
        # now respects self.block_order (default remains TBRL)
        data = self.client.upload_file(self.file_name, self.bookid, block_order=self.block_order)
        if data.get("status") == 200:
            self.queue_id = data["queue_id"]
            print(f"File uploaded successfully. Queue ID: {self.queue_id}")
            return self.queue_id
        raise Exception(f"Upload failed: {data.get('message')}")

    def wait_for_ocr(self):
        guids_data = self.client.poll_ocr_queue(self.queue_id)
        # Pass the original filename + index to GUID objects
        base_name = os.path.splitext(os.path.basename(self.file_name))[0]
        self.guids = [GUID(self.client, guid["guid"], base_name, index=i+1) for i, guid in enumerate(guids_data)]
        print(f"OCR completed. GUIDs: {[g.guid for g in self.guids]}")
        return self.guids


class GUID:
    def __init__(self, client, guid, original_filename=None, index=None):
        self.client = client
        self.guid = int(guid)
        self.original_filename = original_filename
        self.index = index  # 1-based position within a file (if known)

    def _basename(self, rename_map=None, template=RESULT_NAME_TEMPLATE):
        return render_result_basename(
            template,
            guid=self.guid,
            original=self.original_filename,
            index=self.index,
            rename_map=rename_map
        )

    def save_results(self, rename_map=None):
        result = self.client.get_result(self.guid)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        base = self._basename(rename_map=rename_map)

        txt_filename = ensure_unique_path(os.path.join(DOWNLOAD_DIR, f"{base}.txt"))
        json_filename = ensure_unique_path(os.path.join(DOWNLOAD_DIR, f"{base}.json"))

        with open(txt_filename, 'w', encoding='utf-8') as f:
            for line in result:
                f.write(line["text"] + "\n")
        print(f"Saved text: {txt_filename}")

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON: {json_filename}")

    def save_image(self, rename_map=None):
        result = self.client.get_image(self.guid)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        base = self._basename(rename_map=rename_map)
        image_filename = ensure_unique_path(os.path.join(DOWNLOAD_DIR, f"{base}.jpg"))

        with open(image_filename, 'wb') as f:
            f.write(result)
        print(f"Saved image: {image_filename}")

    # NEW: rename already-downloaded files in downloads/
    def rename_existing_downloads(self, rename_map=None, dry_run=False):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        base = self._basename(rename_map=rename_map)
        candidates = find_existing_files_for_guid(DOWNLOAD_DIR, self.guid)

        if not candidates:
            print(f"[rename] No existing files found for GUID {self.guid} in {DOWNLOAD_DIR}")
            return []

        renamed = []
        for src in candidates:
            ext = os.path.splitext(src)[1].lower()
            dst = ensure_unique_path(os.path.join(DOWNLOAD_DIR, f"{base}{ext}"))

            if os.path.abspath(src) == os.path.abspath(dst):
                continue

            if dry_run:
                print(f"[dry-run] {src} -> {dst}")
            else:
                os.rename(src, dst)
                print(f"[renamed] {src} -> {dst}")

            renamed.append((src, dst))

        return renamed


# %% [0] Account and Workflow Settings
# You need to modify these variables to match your account and password
ACCOUNT = ""
PASSWORD = ""

# Modify below if you want to upload an file (You must specify a book ID or create a new book to upload an file)
# Please put your files in the same directory as this script (your working directory)
UPLOAD_FILE = True
#FILE_LIST = [
#    "a.png"
#]

UPLOAD_FOLDER = "./uploads" # your folder's path
FILE_LIST = [
    os.path.join(UPLOAD_FOLDER, f)
    for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and
        mimetypes.guess_type(f)[0] in ALLOWED_MIME_TYPES and
        FILENAME_PATTERN.match(f)
    ]

BOOK_TITLE = "Vertical_Test"
BOOK_AUTHOR = "Vertical_Test"
USE_BOOK = True # Set to True to create a new book or to use an existing book ID, False to skip book
BOOK_ID = None # Set to None to create a new book, or specify an existing book ID. To get BOOK_ID, you can browse your created book and check the URL

DOWNLOAD_RESULTS = True  # Set to True to download OCR results
#DOWNLOAD_IMAGES = False  # Set to True to download OCR images
DOWNLOAD_DIR = "downloads"

# Modify below if you want to directly download OCR results that already on the platform.
# In order to get GUIDs, you can browse your uploaded files and check the URLs
# This step is seperate from uploading files or create a book. You can directly download OCR results without knowing the BOOK_ID or uploading an file.
EXGUIDS = False # Set to True to download results of your existing GUIDs
# Option 1: Use a range for consecutive GUIDs
GUID_START = 1162900
GUID_END = 1162921  # inclusive
GUIDS = [str(i) for i in range(GUID_START, GUID_END + 1)]

# Option 2: Or manually list specific GUIDs
#GUIDS = [
#     "1147409",
#     "1143651"
# ]


# ======================================# Main execution flow
# %% [1] Login to OCR service
client = ASCDCOCRClient(ACCOUNT, PASSWORD)

# Load rename map once (optional)
rename_map = load_rename_map(RENAME_MAP_FILE)

# %% [2] Create or reuse book metadata
if USE_BOOK:
    book = Book(client, title=BOOK_TITLE, author=BOOK_AUTHOR, bookid=BOOK_ID)
    client.wait_random(label="after book")

# %% [3] Upload new files and check existing GUIDs
guids = []
uploaded_files = []
if UPLOAD_FILE and len(FILE_LIST) > 0:
    for path in FILE_LIST:
        name = os.path.basename(path)
        file = File(client, book.bookid, path)
        file.upload()
        uploaded_files.append(file)
        client.wait_random(label=f"uploaded: {name}")
    for file in uploaded_files:
        guids.extend(file.wait_for_ocr())

if EXGUIDS and len(GUIDS) > 0:
    guids.extend([GUID(client, guid) for guid in GUIDS])

# Optional: rename already-downloaded result files (without downloading again)
if RENAME_EXISTING_DOWNLOADS and len(guids) > 0:
    for guid in guids:
        guid.rename_existing_downloads(rename_map=rename_map, dry_run=RENAME_DRY_RUN)

# %% [4] Download OCR results
if UPLOAD_FILE:
    client.wait_random(min_sec=10, max_sec=10, label=f"to make sure uploaded files are ready")   # if there are many GUIDs, wait longer to ensure all results are ready

if DOWNLOAD_RESULTS:
    if len(guids) == 0:
        print("No GUIDs to process. Please check your file uploads or GUIDs.")
    else:
        if len(guids) > 4 and UPLOAD_FILE:
            client.wait_random(min_sec=30, max_sec=30, label=f"to make sure all GUIDs are ready")   # if there are many GUIDs, wait longer to ensure all results are ready
        for guid in guids:
            print()
            client.wait_random(min_sec=1, max_sec=2, label=f"before GUID {guid.guid}")
            guid.save_results(rename_map=rename_map)


# %% [5] Download images
# if DOWNLOAD_IMAGES:
#     if len(guids) == 0:
#         print("No GUIDs to process. Please check your file uploads or GUIDs.")
#     else:
#         if len(guids) > 4 and UPLOAD_FILE:
#             client.wait_random(min_sec=30, max_sec=30, label=f"to make sure all GUIDs are ready")   # if there are many GUIDs, wait longer to ensure all results are ready
#         for guid in guids:
#             client.wait_random(min_sec=1, max_sec=2, label=f"before GUID {guid.guid}")
#             guid.save_image(rename_map=rename_map)
