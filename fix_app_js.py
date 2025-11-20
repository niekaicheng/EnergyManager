# Fix app.js by removing duplicate code
import os

file_path = 'web/app.js'

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Original file has {len(lines)} lines")

# Keep only the first 893 lines (up to line 893, index 892)
# Line 893 is the closing brace of importData function
cleaned_lines = lines[:893]

print(f"Keeping first 893 lines")

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(cleaned_lines)

print(f"Fixed! New file has {len(cleaned_lines)} lines")
print("Removed all duplicate functions")
