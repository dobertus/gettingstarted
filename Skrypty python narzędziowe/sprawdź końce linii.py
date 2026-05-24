import os
import tempfile
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


def convert_to_lf(path, backup=True):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, PermissionError):
        return False
    # pomijamy pliki binarne
    if b"\x00" in data:
        return False
    new = data.replace(b"\r\n", b"\n")
    if new == data:
        return False
    if backup:
        try:
            with open(path + ".bak", "wb") as b:
                b.write(data)
        except Exception:
            pass
    dirpath = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "wb") as tf:
            tf.write(new)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
    return True


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
                try:
                    converted = convert_to_lf(filepath, backup=True)
                except Exception as exc:
                    converted = False
                    print(f"  conversion error: {exc}")
                if converted:
                    print(f"  converted to LF (backup: {filepath}.bak)")
                else:
                    print(f"  conversion skipped/failed")

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