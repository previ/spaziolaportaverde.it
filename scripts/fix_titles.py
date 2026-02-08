#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).parents[1] / 'content'

title_re = re.compile(r'^(\s*title\s*[:=]\s*)(["\']?)(.*?)(["\']?)\s*$')

def fix_file(p: Path):
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    if not lines:
        return False
    # detect frontmatter delimiter
    if lines[0].strip() in ('---', '+++'):
        delim = lines[0].strip()
        # find end of frontmatter
        for i in range(1, len(lines)):
            if lines[i].strip() == delim:
                fm_end = i
                break
        else:
            return False
        changed = False
        for j in range(1, fm_end):
            m = title_re.match(lines[j])
            if m:
                prefix, q1, val, q2 = m.groups()
                new_val = val.replace('-', ' ')
                if new_val != val:
                    # keep original quoting style
                    lines[j] = f"{prefix}{q1}{new_val}{q2}"
                    changed = True
        if changed:
            p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            return True
    else:
        # no frontmatter delimiter — still try first 20 lines
        changed = False
        for j in range(0, min(20, len(lines))):
            m = title_re.match(lines[j])
            if m:
                prefix, q1, val, q2 = m.groups()
                new_val = val.replace('-', ' ')
                if new_val != val:
                    lines[j] = f"{prefix}{q1}{new_val}{q2}"
                    changed = True
        if changed:
            p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            return True
    return False

def main():
    updated = []
    for p in ROOT.rglob('*.md'):
        if fix_file(p):
            updated.append(str(p.relative_to(ROOT.parent)))
    if updated:
        print('Updated files:')
        for u in updated:
            print(u)
    else:
        print('No files updated')

if __name__ == '__main__':
    main()
