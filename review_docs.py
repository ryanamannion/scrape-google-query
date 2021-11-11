"""Use metadata file to open documents for review, and delete irrelevant docs.
"""
import sys
import json
import argparse
import subprocess
from pathlib import Path
from copy import deepcopy


def open_file(filepath):
    print(f"Opening: {filepath}")
    subprocess.run(f"xdg-open {filepath}", shell=True)


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data, save_path):
    with open(save_path, 'w') as f:
        json.dump(data, f)
    print(f"Data saved to: {save_path}")


def save_reviewed(data, save_path):
    with open(save_path, 'w') as f:
        for line in data:
            f.write(line+"\n")
    print(f"Data saved to: {save_path}")


def parse(input):
    if input.lower() in {'yes', 'y'}:
        return True
    elif input.lower() in {'no', 'n'}:
        return False
    elif input.lower() in {"mistake", "m"}:
        return "MKE"        # mistake
    elif input.lower() in {'note'}:
        return "NTE"
    elif input.lower() in {'q', 'quit'}:
        return "QIT"
    else:
        return "UNK"        # unknown


def main(data_dir):
    data_dir = Path(data_dir)
    reviewed_path = data_dir / "reviewed.txt"
    if not reviewed_path.exists():
        reviewed_path.touch()
    with reviewed_path.open('r') as f:
        reviewed = {line.strip() for line in f.readlines()}
    metadata_path = data_dir / "metadata.json"
    old_metadata_path = data_dir / "metadata_old.json"
    metadata = load_json(metadata_path)
    editable = deepcopy(metadata)
    last = {}
    try:
        for i, (file_name, doc) in enumerate(metadata.items()):
            print()
            print(f"{i+1}/{len(metadata)}")
            if file_name in reviewed:
                print(f"Skipping seen doc: {file_name}")
                continue
            file_path = data_dir/file_name
            open_file(file_path)
            relevant = "UNK"
            while relevant == "UNK":
                raw_input = input("Is this doc relevant? > ")
                relevant = parse(raw_input)
                if relevant is True:
                    # continue
                    print("Yes")
                elif relevant is False:
                    print("No")
                    # move to trash
                    trash_path = Path.home()/".local/share/Trash/files"/file_name
                    if file_path.exists():
                        # patch for error which caused files to be deleted but
                        # not from the metadata
                        file_path.rename(trash_path)
                    del editable[file_name]
                elif relevant == "NTE":
                    note = input("Enter note here > ")
                    this_doc = editable[file_name]
                    existing_notes = this_doc.get('notes', [])
                    existing_notes.append(note)
                    this_doc['notes'] = existing_notes
                    relevant = "UNK"        # re-prompt user
                elif relevant == "MKE":
                    print(f"MISTAKE: {last}")
                    relevant = "UNK"        # re-prompt user
                elif relevant == "QIT":
                    # save new metadata and exit, don't overwrite old metadata
                    metadata_path.rename(old_metadata_path)
                    save_json(editable, metadata_path)
                    save_reviewed(list(reviewed), reviewed_path)
                    sys.exit()
                elif relevant == "UNK":
                    # re-prompt user, unknown input
                    print("Please answer yes/no")
            last = doc
            reviewed.add(file_name)
        # if we run out of docs, save the progress!!!
        save_json(editable, metadata_path)
        save_reviewed(list(reviewed), reviewed_path)
    except Exception as exc:
        choice = parse(input("Exception raised. Save? "))
        if choice is True:
            save_json(editable, metadata_path)
            save_reviewed(list(reviewed), reviewed_path)
        raise exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data_path", type=Path, help="path to data to review")
    args = parser.parse_args()
    main(args.data_path)
