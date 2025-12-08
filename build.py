import os
import markdown
import yaml
from jinja2 import Template

# مسیرها
ARTICLES_DIR = 'articles'
BUILD_DIR = 'builds'
PARTIALS_DIR = 'partials'

# بارگذاری header و footer
with open(os.path.join(PARTIALS_DIR, 'header.html'), 'r', encoding='utf-8') as f:
    header_html = f.read()

with open(os.path.join(PARTIALS_DIR, 'footer.html'), 'r', encoding='utf-8') as f:
    footer_html = f.read()

# خواندن تمام مقالات Markdown
articles = []
for filename in os.listdir(ARTICLES_DIR):
    if filename.endswith('.md'):
        path = os.path.join(ARTICLES_DIR, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            # جدا کردن Front Matter
            if content.startswith('---'):
                parts = content.split('---', 2)
                meta = yaml.safe_load(parts[1])
                md_content = parts[2].strip()
                html_content = markdown.markdown(md_content)
                meta['html_content'] = html_content
                meta['filename'] = filename.replace('.md', '.html')
                articles.append(meta)

# مرتب سازی مقالات بر اساس تاریخ
articles.sort(key=lambda x: x['date'], reverse=True)

# تابع تولید صفحه HTML مقاله
def generate_article_page(article, related_articles):
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{{{{ title }}}}</title>
<link rel="stylesheet" href="../../assets/css/style.css">
</head>
<body>
{header_html}
<main>
<nav class="breadcrumb">
<a href="../../index.html">Home</a> › 
<a href="../../brands/{{{{ brand|lower }}}}/index.html">{{{{ brand }}}}</a> › 
<a href="../../brands/{{{{ brand|lower }}}}/{{{{ series|lower }}}}/index.html">{{{{ series }}}}</a> › 
{{{{ title }}}}
</nav>

<h1>{{{{ title }}}}</h1>
<div>
{{{{ html_content|safe }}}}
</div>

<section>
<h2>Related Articles</h2>
<ul>
{% for ra in related_articles %}
<li><a href="../../articles/{{{{ ra.filename }}}}">{{{{ ra.title }}}}</a></li>
{% endfor %}
</ul>
</section>
</main>
{footer_html}
</body>
</html>
"""
    t = Template(template)
    return t.render(title=article['title'],
                    brand=article['brand'],
                    series=article['series'],
                    html_content=article['html_content'],
                    related_articles=related_articles)

# پاکسازی پوشه builds و ایجاد زیرپوشه‌ها
os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'articles'), exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'brands'), exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'topics'), exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'countries'), exist_ok=True)

# تولید صفحات مقاله
for article in articles:
    # Related Articles بر اساس topic و brand و country
    related = [a for a in articles if a != article and 
               (a['brand']==article['brand'] or 
                a['topic']==article['topic'] or 
                a['country']==article['country'])]
    html = generate_article_page(article, related[:5])
    with open(os.path.join(BUILD_DIR, 'articles', article['filename']), 'w', encoding='utf-8') as f:
        f.write(html)

print("✅ All articles HTML generated successfully!")
