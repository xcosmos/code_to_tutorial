

import yaml
import re
def extract_yaml_block(text: str, label: str = "yaml") -> list:
    """
    Extract and parse a YAML block from an LLM response, automatically
    quoting any `name:` lines whose value contains a colon.
    """
    try:
        # 1. Pull out the inner ```yaml``` block
        block = text.strip().split(f"```{label}")[1].split("```")[0].strip()
        
        # 2. Pre-process line-by-line to quote name values with colons
        fixed_lines = []
        for line in block.splitlines():
            m = re.match(r'^(\s*-\s*name:\s*)(.+)$', line)
            if m:
                key, val = m.groups()
                # If the value has a colon and isn't already quoted, wrap it
                if ":" in val and not (val.strip().startswith('"') and val.strip().endswith('"')):
                    # escape any existing quotes inside
                    val_escaped = val.replace('"', '\\"')
                    fixed_lines.append(f'{key}"{val_escaped}"')
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        fixed_block = "\n".join(fixed_lines)

        # 3. Parse with PyYAML
        return yaml.safe_load(fixed_block)

    except (IndexError, yaml.YAMLError) as e:
        raise ValueError(f"Failed to extract or parse YAML block: {e}")
    
    
    

if __name__ == "__main__":
    sample_yaml = """```yaml
- name: Something
  description: |
    This is like ...
```"""

    print(extract_yaml_block(sample_yaml))