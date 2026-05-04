import re
with open('core/templates/core/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'<span class=\"tab-icon\">.*?</span>', '', content)
with open('core/templates/core/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
