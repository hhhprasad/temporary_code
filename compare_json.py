#!/usr/bin/env python3

import json
import argparse
import sys
import html
from colorama import init, Fore, Style

# Initialize colorama
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

def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(value[k]) for k in sorted(value)}
    elif isinstance(value, list):
        return sorted([normalize(v) for v in value], key=lambda x: json.dumps(x, sort_keys=True))
    return value

def compare_json(json1, json2, path=""):
    differences = []

    if type(json1) != type(json2):
        differences.append(("type", path, f"Type mismatch: {type(json1).__name__} vs {type(json2).__name__}"))
        return differences

    if isinstance(json1, dict):
        keys = set(json1) | set(json2)
        for key in keys:
            new_path = f"{path}.{key}" if path else key
            if key not in json1:
                differences.append(("missing_key", new_path, "Missing in first JSON"))
            elif key not in json2:
                differences.append(("missing_key", new_path, "Missing in second JSON"))
            else:
                differences += compare_json(json1[key], json2[key], new_path)

    elif isinstance(json1, list):
        norm1 = normalize(json1)
        norm2 = normalize(json2)
        if norm1 != norm2:
            differences.append(("list", path, f"List mismatch:\n  First: {norm1}\n  Second: {norm2}"))
    else:
        if json1 != json2:
            differences.append(("value", path, f"{json1} vs {json2}"))

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
        "body { font-family: sans-serif; padding: 1em; }",
        ".diff { margin-bottom: 1em; border: 1px solid #ddd; border-radius: 5px; }",
        "summary { font-weight: bold; padding: 0.4em; cursor: pointer; }",
        ".missing_key summary { background: #ffe6e6; }",
        ".type summary { background: #fff5cc; }",
        ".value summary { background: #f0e6ff; }",
        ".list summary { background: #e6f7ff; }",
        ".message { padding: 0.5em 1em; white-space: pre-wrap; }",
        "</style><title>JSON Diff Report</title></head><body>",
        "<h1>JSON Diff Report</h1>"
    ]

    if not differences:
        html_parts.append("<p style='color:green;'>✅ JSONs are equivalent (ignoring order).</p>")
    else:
        for diff_type, path, message in differences:
            message_html = html.escape(message)

            # Add line breaks for 'list' and 'value'
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
    parser.add_argument("file1", help="Path to the first JSON file")
    parser.add_argument("file2", help="Path to the second JSON file")
    parser.add_argument("--html-report", help="Optional path to save HTML report")

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
