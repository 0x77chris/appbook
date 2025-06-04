import re

def parse_metadata(filepath):
    metadata = {
        "name": filepath.stem,
        "description": "No description",
        "version": "0.1",
        "category": "Utility",
        "icon": "🚟"
    }
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"):
                match = re.match(r"#\s*(\w+):\s*(.+)", line)
                if match:
                    key, value = match.groups()
                    metadata[key.lower()] = value.strip()
            else:
                break
    metadata["path"] = str(filepath)
    return metadata
