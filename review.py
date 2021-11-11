"""Use metadata file to open documents for review, and delete irrelevant docs.
"""
import sys
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from copy import deepcopy

response_table = [
    ("Response", "Alternative(s)", "Description & Action"),
    ("yes", "y", "Document is relevant: set `reviewed` key to `True`"),
    ("no", "n", "Document is not relevant: remove from metadata and move file "
                "to trash"),
    ("reopen", "r", "Open the current document again."),
    ("mistake", "m", "You replied `y`/`n` when you meant the opposite: user is "
                     "prompted for which of the last 5 docs was a mistake. That"
                     " document is readded to the metadata as unreviewed, and "
                     "if the file is in the trash it is restored."),
    ("note, comment", "c", "Add a note to the current document"),
    ("quit", "q", "Save progress and quit")
    ]

TERM_SIZE = shutil.get_terminal_size((57, 98))      # for table formatting
print(TERM_SIZE)
TRASH_LOCATION = Path.home()/".local/share/Trash/files"       # joinpath idiom
DEFAULT_APP_OPENER = "xdg-open"


def format_table(table):
    output = ""
    lens = {0: [], 1: []}
    for cells in table:
        for num in [0, 1]:
            lens[num].append(len(cells[num]))
    longest = {num: max(lens[num]) for num in [0, 1]}
    for cells in table:
        third_col_start = None
        line = ""
        for i, cell in enumerate(cells):
            if i in [0, 1]:
                line += cell+(" " * (longest[i] - len(cell)))+(" "*4)
                third_col_start = len(line)   # will get set correctly when i==2
            else:
                words = cell.split(" ")
                third_col = ""
                for word in words:
                    if (len(line) + len(word) + 1) <= TERM_SIZE.columns:
                        line += " " + word
                    else:
                        output += line + "\n"
                        line = " " * third_col_start
        output += line + "\n"
        output += "-" * TERM_SIZE.columns + "\n"
    return output


def open_file(filepath):
    print(f"Opening: {filepath}")
    subprocess.run(f"{DEFAULT_APP_OPENER} {filepath}", shell=True)


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
    elif input.lower() in {'r', 'reopen'}:
        return "REO"
    elif input.lower() in {'note', 'comment', 'c'}:
        return "NTE"
    elif input.lower() in {'q', 'quit'}:
        return "QIT"
    else:
        return "UNK"        # unknown


def trash(file_path):
    trash_name = TRASH_LOCATION/file_path.name
    file_path.rename(trash_name)


def recover(file_name, dest):
    trash_name = TRASH_LOCATION/file_name
    dest_name = Path(dest)/file_name
    if trash_name.exists():
        trash_name.rename(dest_name)
    else:
        try:
            assert dest_name.exists()
        except AssertionError:
            raise FileNotFoundError(file_name)


def main(data_dir):
    data_dir = Path(data_dir)
    metadata_path = data_dir / "metadata.json"
    old_metadata_path = data_dir / "metadata_old.json"
    metadata = load_json(metadata_path)
    reviewed = {p for p, d in metadata.items() if d['reviewed'] is True}
    editable = deepcopy(metadata)
    last = []
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
                    editable[file_name]['reviewed'] = True
                elif relevant is False:
                    print("No")
                    # move to trash
                    if file_path.exists():
                        trash(file_path)
                    del editable[file_name]
                elif relevant == "NTE":
                    note = input("Enter note here > ")
                    this_doc = editable[file_name]
                    existing_notes = this_doc.get('notes', [])
                    existing_notes.append(note)
                    this_doc['notes'] = existing_notes
                    relevant = "UNK"        # re-prompt user
                elif relevant == "MKE":
                    print("Which document did you make a mistake on?")
                    for i, prev_doc in enumerate(last):
                        print(f"{i}: {prev_doc['save_fname']}")
                    idx = int(input("> "))
                    print(f"Re-adding doc {idx} as unreviewed. Returning to "
                          f"present document.")
                    last_doc = last[idx]
                    last_doc['reviewed'] = False
                    last_fname = last_doc['save_fname']
                    editable[last_fname] = last_doc
                    recover(last_fname, data_dir)
                    relevant = "UNK"        # re-prompt user
                elif relevant == "REO":
                    open_file(file_path)
                    relevant = "UNK"        # re-prompt user
                elif relevant == "QIT":
                    # save new metadata and exit, don't overwrite old metadata
                    metadata_path.rename(old_metadata_path)
                    save_json(editable, metadata_path)
                    sys.exit()
                elif relevant == "UNK":
                    # re-prompt user, unknown input
                    print("Please answer yes/no")
            if len(last) > 5:
                last.pop(0)
            last.append(doc)
            reviewed.add(file_name)
        # if we run out of docs, save the progress!!!
        save_json(editable, metadata_path)
    except Exception as exc:
        choice = parse(input("Exception raised. Save? "))
        if choice is True:
            save_json(editable, metadata_path)
        raise exc


if __name__ == "__main__":
    # hack-y way around optional arg still requiring positional arg
    if sys.argv[1] in ['--reponses', '-r']:
        print(format_table(response_table))
        sys.exit()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_path", type=Path, help="path to data to review")
    parser.add_argument("--responses", "-r", action="store_true",
                        help="display valid responses and exit")
    args = parser.parse_args()
    if args.responses:
        print(format_table(response_table))
        sys.exit()
    main(args.data_path)
