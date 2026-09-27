import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('scratch/paper_v2/generated_stats.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix double backslash before % in our added macros (\\% -> \%)
content_fixed = content.replace('\\\\%', '\\%')
bad_count = content_fixed.count('\\\\%')
print(f'Remaining bad \\\\% count: {bad_count}')

# Add \endinput at end if missing
if '\\endinput' not in content_fixed:
    content_fixed = content_fixed.rstrip() + '\n\\endinput\n'
    print('Added \\endinput at end')
else:
    print('\\endinput already present')

with open('scratch/paper_v2/generated_stats.tex', 'w', encoding='utf-8') as f:
    f.write(content_fixed)
print('Fixed and saved')
print(f'Total lines: {len(content_fixed.splitlines())}')
