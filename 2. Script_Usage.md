# 2. How to Use the Sinica OCR Script (`sinica_apitest.py`)

This document is a practical guide to using the Python script `sinica_apitest.py`, which demonstrates how to use base API functions of the Academia Sinica OCR platform.

It assumes you have Python installed and are familiar with using Visual Studio Code (VS Code) or an equivalent editor.

---

## 2.1 Purpose of the Script

The script can perform the following tasks:

1. Logs in to the Academia Sinica OCR web service
2. Creates a new "book" entry (or reuses an existing one)
3. Uploads image files to the OCR platform
4. Waits for the OCR processing to finish
5. Downloads the OCR result as text and JSON files

---

## 2.2 Preparing Your Environment

### Files You Need

* `sinica_apitest.py`: the main Python script
* Your image files (e.g. `page1.png`, `page2.jpg`)

Place all these files in the same folder.

### Required Python Package

This script uses the `requests` package to communicate with the website. You must install it first using the terminal (either in VScode or command promt):

```bash
pip install requests
```

---

## 2.3 Step-by-Step Instructions

### Step 1: Open the Script in VS Code

1. Open VS Code.
2. Go to `File → Open Folder...` and select the folder containing your script and images.
3. Click on `sinica_apitest.py` to open it.

### Step 2: Set Your Account and Book Info

At the top of the script, you will see some variables:

```python
ACCOUNT = "your_account"
PASSWORD = "your_password"
FILE_LIST = [
    "example.zip",
    "example.png",
    "example.pdf",
    "example.jpg"
]
BOOK_TITLE = "Book Title"
BOOK_AUTHOR = "Book Author"
BOOK_ID = None  # Use None to create a new book
```

Fill in your Academia Sinica OCR login credentials, the filenames of the images to upload, and book information. Acceptable file types are png, jpg, pdf, and zip. Acceptable file names are `[A-Za-z0-9_.-]+` (English letters, numbers, "_", ".", and "-")

* If you already have a book and want to reuse it, replace `BOOK_ID = None` with the actual book ID number. You can find book id in your URL when you browse yout book. For example https://ocr.ascdc.tw/bookDetail.php?id=7375 or https://ocr.ascdc.tw/pagelist.php?id=7375 has book id = 7375
* If you don't want to use a book but only want to download existing image OCR results, set `USE_BOOK = False` with `UPLOAD_FILE = False` and check [Directly Download OCR Results](#24-optional-directly-download-ocr-results) part in this ducument.

### Step 3: Run the Script

1. Open the terminal inside VS Code: `Terminal → New Terminal`
2. Run the script:

```bash
python sinica_apitest.py
```

The script will:

* Log you in
* Upload your files
* Wait for the OCR results to be ready
* Download the results to `.txt` and `.json` files in the same folder

---

## 2.4 Optional: Directly Download OCR Results 

If you already uploaded images and want to download OCR results of them, please set the following variable as:

```python
EXGUIDS = True
GUIDS = ["yourGUID1", "yourGUID2"]
```
* To get GUID, when you browse your OCRed pages, your URL should look like "https://ocr.ascdc.tw/reader.php?pid=1234567&book_id=1234&rid=1234567", the GUID is the number follows "pid="
* You can download multiple GUID at the same time.


---

## 2.5 Output Files

For each processed image, the script will generate:

* `yourGUID.txt`: plain text result
* `yourGUID.json`: structured result with position and formatting data

These files are saved in the same folder as the script.

---

## 2.6 Troubleshooting

| Issue                          | Solution                                                              |
| ------------------------------ | --------------------------------------------------------------------- |
| Login failed                   | Check your account and password are entered correctly.                |
| "No GUIDs to process"          | Ensure `UPLOAD_IMAGE = True` and `IMAGE_LIST` is not empty.           |
| Cannot find image file         | Make sure image filenames are correct and located in the same folder. |
| pip install fails or not found | Ensure Python and pip were installed properly and added to PATH.      |
| "something went wrong"                  | Set longer waiting time. If not solved, please reach out. 
---

