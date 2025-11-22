# Fix index.html by adding the missing script tags at the end

# Read the current file
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any existing closing body and html tags
content = content.rstrip()
if content.endswith('\u003c/html\u003e'):
    content = content[:-7].rstrip()
if content.endswith('\u003c/body\u003e'):
    content = content[:-7].rstrip()

# Add the script tags and closing tags
scripts = '''
\u003c!-- Scripts --\u003e
\u003cscript src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"\u003e\u003c/script\u003e
\u003cscript src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js"\u003e\u003c/script\u003e
\u003cscript src="app.js"\u003e\u003c/script\u003e
\u003cscript src="calendar.js"\u003e\u003c/script\u003e
\u003c/body\u003e

\u003c/html\u003e
'''

# Write the fixed content
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content + scripts)

print("Fixed index.html - added script tags")
