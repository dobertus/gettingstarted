import os
from tkinter import Tk, filedialog


def detect_eol(path, read_bytes=65536):
    try:
        with open(path, "rb") as f:
            content = f.read(read_bytes)
    except (PermissionError, OSError):
        return "error"
    if not content:
        return "empty"
    # szybkie wykrycie plików binarnych (nul byte)
    if b"\x00" in content:
        return "binary"
    if b"\r\n" in content:
        if b"\n" in content.replace(b"\r\n", b""):
            return "mixed"
        return "CRLF"
    elif b"\n" in content:
        return "LF"
    elif b"\r" in content:
        return "CR"
    else:
        return "unknown"


def pick_root():
    tk = Tk()
    tk.withdraw()
    path = filedialog.askdirectory(title="Wybierz katalog root")
    tk.destroy()
    return path


def main():
    root = pick_root()
    if not root:
        print("Nie wybrano katalogu. Kończę.")
        return
    crlf_files = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=True):
        for name in filenames:
            filepath = os.path.join(dirpath, name)
            try:
                eol = detect_eol(filepath)
            except Exception as exc:
                eol = f"error:{type(exc).__name__}"
            if eol == 'CRLF':
                crlf_files.append(filepath)
                print(f"{filepath} -> {eol}")

    crlf_files.sort()
    out_path = os.path.join(root, "crlf_files.csv")
    try:
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            for p in crlf_files:
                f.write(p + "\n")
        print(f"Zapisano {len(crlf_files)} wpisów do {out_path}")
    except OSError as e:
        print(f"Nie można zapisać pliku {out_path}: {e}")


if __name__ == "__main__":
    main()