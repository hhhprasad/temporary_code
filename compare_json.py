#!/usr/bin/env python3

"""
this program will compare both json file values unordered , ordering does not matter here
python compare_json_iterative.py C:/t1/f1.json C:/t1/f2.json --html-report C:/t1/report.html

"""


import json
import argparse
import sys
import html
from colorama import init, Fore, Style

init(autoreset=True)

def is_valid_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"{Fore.RED}Invalid JSON in {file_path}: {e}"
    except FileNotFoundError:
        return None, f"{Fore.RED}File not found: {file_path}"
    except Exception as e:
        return None, f"{Fore.RED}Error reading {file_path}: {e}"

def normalize(data):
    if isinstance(data, dict):
        stack = [(data, {})]
        result = {}

        while stack:
            current, normalized = stack.pop()
            for key in sorted(current):
                value = current[key]
                if isinstance(value, dict):
                    new_dict = {}
                    normalized[key] = new_dict
                    stack.append((value, new_dict))
                elif isinstance(value, list):
                    norm_list = sorted([normalize(v) for v in value], key=lambda x: json.dumps(x, sort_keys=True))
                    normalized[key] = norm_list
                else:
                    normalized[key] = value
        return normalized

    elif isinstance(data, list):
        return sorted([normalize(v) for v in data], key=lambda x: json.dumps(x, sort_keys=True))

    return data

def compare_json(json1, json2):
    stack = [(json1, json2, "")]
    differences = []

    while stack:
        val1, val2, path = stack.pop()

        if type(val1) != type(val2):
            differences.append(("type", path, f"Type mismatch: {type(val1).__name__} vs {type(val2).__name__}"))
            continue

        if isinstance(val1, dict):
            keys = set(val1) | set(val2)
            for key in keys:
                new_path = f"{path}.{key}" if path else key
                if key not in val1:
                    differences.append(("missing_key", new_path, "Missing in first JSON"))
                elif key not in val2:
                    differences.append(("missing_key", new_path, "Missing in second JSON"))
                else:
                    stack.append((val1[key], val2[key], new_path))

        elif isinstance(val1, list):
            norm1 = normalize(val1)
            norm2 = normalize(val2)
            if norm1 != norm2:
                differences.append(("list", path, f"List mismatch:\n  First: {norm1}\n  Second: {norm2}"))

        else:
            if val1 != val2:
                differences.append(("value", path, f"{val1} vs {val2}"))

    return differences

def print_terminal_diffs(differences):
    if differences:
        print(Fore.YELLOW + Style.BRIGHT + "\nDifferences found:\n")
        for diff_type, path, message in differences:
            color = {
                "missing_key": Fore.RED,
                "type": Fore.YELLOW,
                "value": Fore.MAGENTA,
                "list": Fore.CYAN
            }.get(diff_type, Fore.WHITE)
            print(f"{color}- {path}: {message}")
    else:
        print(Fore.GREEN + "✅ JSONs are equivalent (ignoring order).")

def generate_html_report(differences, output_path):
    html_parts = [
        "<html><head><style>",
        "body { font-family: Arial; padding: 20px; }",
        "details.diff { margin: 10px 0; padding: 10px; border-left: 5px solid #999; background: #f9f9f9; }",
        ".diff.missing_key { border-color: red; }",
        ".diff.type { border-color: orange; }",
        ".diff.value { border-color: purple; }",
        ".diff.list { border-color: teal; }",
        ".message { white-space: pre-wrap; font-family: monospace; }",
        "</style><title>JSON Diff Report</title></head><body>",
        "<h1>JSON Diff Report</h1>"
    ]

    if not differences:
        html_parts.append("<p style='color:green;'>✅ JSONs are equivalent (ignoring order).</p>")
    else:
        for diff_type, path, message in differences:
            message_html = html.escape(message)
            if diff_type in {"list", "value"}:
                message_html = message_html.replace("First:", "<br><strong>First:</strong><br>")
                message_html = message_html.replace("Second:", "<br><strong>Second:</strong><br>")
                message_html = message_html.replace(" vs ", "<br><strong>vs</strong><br>")

            html_parts.append(f"<details class='diff {diff_type}' open>")
            html_parts.append(f"<summary>{html.escape(path)} ({diff_type})</summary>")
            html_parts.append(f"<div class='message'>{message_html}</div>")
            html_parts.append("</details>")

    html_parts.append("</body></html>")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_parts))

    print(Fore.BLUE + f"\n📄 HTML report written to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Compare two JSON files (order-insensitive).")
    parser.add_argument("file1", help="Path to first JSON file")
    parser.add_argument("file2", help="Path to second JSON file")
    parser.add_argument("--html-report", help="Optional output path for HTML report")
    args = parser.parse_args()

    data1, err1 = is_valid_json_file(args.file1)
    data2, err2 = is_valid_json_file(args.file2)

    if err1 or err2:
        if err1: print(err1)
        if err2: print(err2)
        sys.exit(1)

    differences = compare_json(data1, data2)
    print_terminal_diffs(differences)

    if args.html_report:
        generate_html_report(differences, args.html_report)

    sys.exit(1 if differences else 0)

if __name__ == "__main__":
    main()
