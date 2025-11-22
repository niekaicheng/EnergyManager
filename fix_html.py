#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Remove the unused edit-goal-modal from index.html"""

with open('web/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove the edit-goal-modal section
start_marker = '<!-- Edit Goal Modal -->'
end_marker = '</div>\n    </div>\n\n\n    <div id="import-data-modal"'

start_pos = content.find(start_marker)
end_pos = content.find(end_marker)

if start_pos != -1 and end_pos != -1:
    # Remove the section
    new_content = content[:start_pos] + '    <div id="import-data-modal"' + content[end_pos + len(end_marker):]
    
    with open('web/index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully removed edit-goal-modal")
else:
    print("Could not find markers")
    print(f"start_pos: {start_pos}, end_pos: {end_pos}")
