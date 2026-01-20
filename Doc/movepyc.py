import os
import shutil

SOURCE_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ROOT = os.path.join(SOURCE_ROOT, "compiled")   # change if needed


def move_pyc_files():
    for root, _, files in os.walk(SOURCE_ROOT):
        # Skip output folder to avoid looping on itself
        if OUTPUT_ROOT in os.path.abspath(root):
            continue

        for f in files:
            if f.endswith(".pyc"):
                src_file = os.path.join(root, f)

                # relative folder path from project root
                rel_path = os.path.relpath(root, SOURCE_ROOT)
                dest_dir = os.path.join(OUTPUT_ROOT, rel_path)

                os.makedirs(dest_dir, exist_ok=True)

                dest_file = os.path.join(dest_dir, f)

                print(f"Moving {src_file} -> {dest_file}")
                shutil.move(src_file, dest_file)

    print("Done moving .pyc files.")


if __name__ == "__main__":
    move_pyc_files()
