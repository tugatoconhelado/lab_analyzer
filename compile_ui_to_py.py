from pathlib import Path
from PyQt5 import uic

def compile_ui_files(base_dir: Path, output_dir: Path | None = None) -> int:
    ui_files = sorted(base_dir.rglob("*.ui"))
    if not ui_files:
        print(f"No .ui files found in: {base_dir}")
        return 0

    compiled = 0
    for ui_file in ui_files:
        if output_dir is None:
            py_file = ui_file.with_name(f"ui_{ui_file.stem}.py")
        else:
            rel = ui_file.relative_to(base_dir).with_suffix(".py")
            py_file = output_dir / rel
            py_file.parent.mkdir(parents=True, exist_ok=True)

        with ui_file.open("r", encoding="utf-8") as fin, py_file.open("w", encoding="utf-8") as fout:
            uic.compileUi(fin, fout)

        compiled += 1
        print(f"Compiled: {ui_file} -> {py_file}")

    return compiled


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    ui_dir = project_root / "resources" / "ui"

    if not ui_dir.exists():
        raise SystemExit(f"Directory not found: {ui_dir}")

    total = compile_ui_files(ui_dir)
    print(f"Done. Compiled {total} file(s).")