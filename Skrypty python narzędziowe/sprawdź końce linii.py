import os
import sys
import argparse
import tempfile
from tkinter import Tk, filedialog


def parse_args():
    parser = argparse.ArgumentParser(description="Wyszukaj pliki wg typu EOL i opcjonalnie konwertuj do LF")
    parser.add_argument("-t", "--types", default="CRLF",
                        help=("Comma-separated EOL types to target. Allowed: binary,mixed,LF,CR,unknown,CRLF "
                              "(default: CRLF)"))
    parser.add_argument("--force-binary", action="store_true",
                        help="Allow converting files detected as binary (contains NUL) — risky")
    parser.add_argument("-o", "--output", default=None,
                        help="Output CSV filename relative to selected root (default auto-generated)")
    return parser.parse_args()


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


def convert_to_lf(path, backup=True, allow_binary=False):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, PermissionError):
        return False
    # opcjonalne pomijanie plików binarnych
    if b"\x00" in data and not allow_binary:
        return False
    # zamień CRLF i samodzielne CR na LF
    new = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
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
    args = parse_args()

    # parse and validate requested EOL types
    allowed = {"binary", "mixed", "lf", "cr", "unknown", "crlf"}
    requested = [s.strip() for s in args.types.split(",") if s.strip()]
    if not requested:
        print("Brak typów EOL do przetworzenia. Kończę.")
        return
    for s in requested:
        if s.lower() not in allowed:
            print(f"Nieprawidłowy typ '{s}'. Dozwolone: {', '.join(sorted(allowed))}")
            return

    norm_map = {"binary": "binary", "mixed": "mixed", "lf": "LF", "cr": "CR", "unknown": "unknown", "crlf": "CRLF"}
    requested_set = set(norm_map[s.lower()] for s in requested)

    root = pick_root()
    if not root:
        print("Nie wybrano katalogu. Kończę.")
        return

    matched_files = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=True):
        for name in filenames:
            filepath = os.path.join(dirpath, name)
            # pomiń pliki kopii zapasowych .bak
            if name.lower().endswith(".bak"):
                continue
            try:
                eol = detect_eol(filepath)
            except Exception as exc:
                eol = f"error:{type(exc).__name__}"
            if eol in requested_set:
                matched_files.append(filepath)
                print(f"{filepath} -> {eol}")
                # handle binary specially unless forced
                if eol == "binary" and not args.force_binary:
                    print("  binary file detected; conversion skipped (use --force-binary to allow)")
                    continue
                try:
                    converted = convert_to_lf(filepath, backup=True, allow_binary=args.force_binary)
                except Exception as exc:
                    converted = False
                    print(f"  conversion error: {exc}")
                if converted:
                    print(f"  converted to LF (backup: {filepath}.bak)")
                else:
                    print(f"  conversion skipped/failed")

    matched_files.sort()
    # determine output filename
    if args.output:
        out_name = args.output
    else:
        out_name = "_".join(sorted(s.lower() for s in requested_set)) + "_files.csv"
    out_path = os.path.join(root, out_name)
    try:
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            for p in matched_files:
                f.write(p + "\n")
        print(f"Zapisano {len(matched_files)} wpisów do {out_path}")
    except OSError as e:
        print(f"Nie można zapisać pliku {out_path}: {e}")


if __name__ == "__main__":
    main()