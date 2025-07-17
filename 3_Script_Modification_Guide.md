# 3. Customizing the Main Execution Block of the Sinica OCR Script

This guide explains how to adapt the `sinica_apitest_refactored.py` script to fit your OCR workflows by covering:

1. How to modify OCR parameters (via `Book` and `File` classes)
2. How to adjust control flags and logic flow
3. How to upload all valid files in a folder dynamically

---

## 3.1 Changing OCR Parameters (Basic, Core Usage)

The script gives you full control of OCR behavior through the `Book` and `File` classes.

### A. `Book` Class – Book Metadata

You can customize how the uploaded files are grouped as a "book" in the system.

```python
book = Book(
    client,
    title="Book Title",
    author="Your Name",
    is_public=0,
    orientation=2,
    bookid=None
)
```

| Argument      | Type       | Description                                  |
| ------------- | ---------- | -------------------------------------------- |
| `title`       | string     | Book title                                   |
| `author`      | string     | Book author                                  |
| `is_public`   | int        | `0` = private, `1` = public                  |
| `orientation` | int        | `0` = horizontal, `1` = vertical, `2` = auto |
| `bookid`      | int / None | Use this to reuse a created book             |

When `bookid` is set, `title` and `author` are only used for internal caching.

### B. `File` Class – OCR Upload Parameters

You can specify detailed OCR settings for each file:

```python
file = File(
    client,
    book.bookid,
    file_name="example.png",
    block_order='TBLR',
    language=5,
    orientation=0,
    correction=1,
    pages_per_img=1,
    remove_margin=2,
    has_mark=True,
    has_alphabet=True,
    remove_anno=False,
    is_inverted=False
)
```

| Parameter       | Type | Description                                     |
| --------------- | ---- | ----------------------------------------------- |
| `block_order`   | str  | `'TBRL'`, `'TBLR'`, `'RLTB'`, `'LRTB'`  (Reading order T:Top; B:Bottom; R:Right; L:Left)        |
| `language`      | int  | `1` = Chinese, `5` = Old Japanese               |
| `orientation`   | int  | `0` = horizontal, `1` = vertical, `2` = auto    |
| `correction`    | int  | `-1` = no correction, `0–4` for history, Taoism, Buddhism, medicine, modern dictionary |
| `pages_per_img` | int  | `1` or `2` pages per image                      |
| `remove_margin` | int  | `-1`, `1` (black), `2` (white)                  |
| `has_mark`      | bool | Whether punctuation is present                  |
| `has_alphabet`  | bool | Horizontal Latin letters present                |
| `remove_anno`   | bool | Remove annotation symbols                       |
| `is_inverted`   | bool | Image is white-on-black                         |

---

## 2. Adjusting Execution Flags and Script Flow

At the top of the script are global flags and parameters that control what actions are taken.

```python
UPLOAD_FILE = True
USE_BOOK = True
BOOK_TITLE = "Book X"
BOOK_AUTHOR = "Author Y"
BOOK_ID = None
EXGUIDS = False
GUIDS = ["1039633"]
```

### Common Use Cases

| Goal                  | Settings                                                    |
| --------------------- | ----------------------------------------------------------- |
| Use existing book     | Set `BOOK_ID = 1234`, set `BOOK_TITLE` and `BOOK_AUTHOR` correspondingly. The API can't fetch title and author.               |
| Create new book       | Leave `BOOK_ID = None`, define `BOOK_TITLE` and `BOOK_AUTHOR`            |
| Skip books entirely   | Set `USE_BOOK = False` (only if you don't want to upload files.)    |
| Download existing results | Set `EXGUIDS = True`, define `GUIDS` |

* If you want to upload files, then you must use a book (either create one or use existing one). 
* Download existing results is separate from other workflow. Whether you use a book or not, upload a file or not, you can still download existing results as long as you have correpoding GUIDs. 

### Execution Block (Simplified Overview)

```python
client = ASCDCOCRClient(ACCOUNT, PASSWORD)

if USE_BOOK:
    book = Book(client, title=BOOK_TITLE, author=BOOK_AUTHOR, bookid=BOOK_ID)

guids = []

if UPLOAD_FILE:
    for name in FILE_LIST:
        file = File(client, book.bookid, name)
        file.upload()
        guids.extend(file.wait_for_ocr())

if EXGUIDS:
    guids.extend([GUID(client, guid) for guid in GUIDS])

for guid in guids:
    guid.save_to_file()
```

---

## 3. Uploading All Files in a Folder

To avoid hardcoding file names, you can automatically gather all valid files from a folder.

Replace this block:

```python
FILE_LIST = [
    "example.jpg", "example.pdf"
]
```

With:

```python
UPLOAD_FOLDER = "./uploads" # your folder's path
FILE_LIST = [
    os.path.join(UPLOAD_FOLDER, f)
    for f in os.listdir(UPLOAD_FOLDER)
    if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and
       mimetypes.guess_type(f)[0] in ALLOWED_MIME_TYPES and
       FILENAME_PATTERN.match(f)
]
```

Only files matching:

* `.jpg`, `.png`, `.pdf`, `.zip`
* File name pattern `[A-Za-z0-9_.-]+`

are included.
