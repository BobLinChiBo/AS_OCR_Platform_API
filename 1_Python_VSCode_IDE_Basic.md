# 1. Beginner's Guide to Python, VS Code, and IDEs

This guide is intended for readers who are new to programming tools but have a general understanding of programming concepts. It introduces three foundational tools:

* **Python**, the programming environment used to run scripts
* **IDE**, an environment for writing and executing code
* **Visual Studio Code (VS Code)**, a modern and lightweight IDE well-suited for Python

---

## 1.1 Python Environment Overview

Python is widely used across many fields including web development, data science, automation, and more. When installed on your computer, Python includes the interpreter necessary to run `.py` script files.

In addition to the core interpreter, Python relies on packages—reusable sets of tools that extend what Python can do. These packages are managed through **pip**, Python's built-in package installer.

### Installing Python

1. Go to the official Python site: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download the installer for your system (Windows/macOS/Linux).
3. During installation, be sure to check the box labeled **"Add Python to PATH"**.
4. After installation, open a program called **Command Prompt** (on Windows) or **Terminal** (on macOS/Linux).

   * On Windows, search for "Command Prompt" in the Start Menu.
   * On macOS, open Spotlight (Cmd + Space) and type "Terminal".
5. Type the following command to check if Python was installed correctly:

   ```bash
   python --version
   ```

   You should see something like:

   ```
   Python 3.x.x
   ```

### What Is pip?

`pip` is a tool you use to install and manage extra features (called "packages") in Python. It comes with Python versions 3.4 and above, so you usually don't need to install it separately.

To check if pip is installed, type:

```bash
pip --version
```

To install a package, such as `requests`, use this command:

```bash
pip install requests
```

This tells your computer to download and install the `requests` package, which allows Python scripts to send and receive web requests.

---

## 1.2 What Is an IDE?

An **IDE (Integrated Development Environment)** is a software application that provides a complete environment to write, edit, and run code. An IDE typically includes:

* A code editor
* Highlighting for different parts of the code (syntax highlighting)
* Suggestions as you type (auto-completion)
* A place to run commands (often called a "terminal" or "console")
* Tools for checking errors and debugging

While it is possible to write Python code in a basic text editor and run it using Command Prompt or Terminal, using an IDE makes it easier and faster to work, especially for beginners.

Popular IDEs for Python include:

* **VS Code (Visual Studio Code)**: Lightweight and customizable
* PyCharm: Full-featured and popular with professionals
* Thonny: Designed for education and beginners

---

## 1.3 Using Visual Studio Code (VS Code) for Python

**Visual Studio Code** is a free and modern editor that works on Windows, macOS, and Linux. It is easy to use and works very well with Python.

### Installing VS Code

1. Download it from: [https://code.visualstudio.com/](https://code.visualstudio.com/)
2. Run the installer and follow the instructions.

### Opening a Project Folder

1. Start VS Code.
2. From the top menu, choose `File → Open Folder...`
3. Select the folder that contains your Python file (e.g., `sinica_apitest.py`) and any image files it uses.

### Opening and Editing a File

* On the left side of the window, you'll see your folder and its files.
* Click a file (like `sinica_apitest.py`) to open and edit it.

### Using the Built-in Terminal in VS Code

VS Code includes a tool to type commands, called the **integrated terminal**. This behaves just like Command Prompt or Terminal.

To open it:

* Press \`Ctrl + \`\` (the backtick key, usually above the Tab key)
* Or go to the top menu and click `Terminal → New Terminal`

This will open a panel at the bottom where you can type commands.

### Installing Python Packages with pip in VS Code

If your script needs extra packages (such as `requests`), type this into the terminal:

```bash
pip install requests
```

This installs the package so your script can use it.

### Running Your Python Script

To run a Python file (such as `sinica_apitest.py`), type:

```bash
python sinica_apitest.py
```

You will see messages appear in the terminal that show what the script is doing.

---

## 1.4 Frequently Asked Questions

| Question                              | Answer                                                                                                                                                            |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| What if Python is not found?          | Make sure you selected "Add Python to PATH" during installation. You may reinstall Python if needed.                                                              |
| What is a package?                    | A package is reusable code that extends Python's functionality. Packages are installed using `pip`.                                                               |
| Do I need an IDE to use Python?       | No. You can use any text editor and run Python in a command window. However, IDEs simplify and streamline development.                                            |
| What is a terminal or command window? | A program where you type and run commands, such as "python myfile.py". It's built into VS Code and also exists as Command Prompt on Windows or Terminal on macOS. |

---

You are now equipped with the essential tools to edit, run, and manage Python scripts. This knowledge will help you confidently use automation tools such as the Sinica OCR script.

