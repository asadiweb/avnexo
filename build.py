import os
import markdown
import yaml
from jinja2 import Template
from collections import defaultdict

# مسیرها
ARTICLES_DIR = 'articles'
BUILD_DIR = 'builds'
PARTIALS_DIR = 'partials'

# بارگذاری header و footer
with open(os.path.join(PARTIALS_DIR, 'header.html'), 'r', encoding='utf-8') as f:
    header_html = f.read()
with open(os.path.join(PARTIALS_DIR, 'footer.html'), 'r', encoding='utf-8') as f:
    footer_html = f.read()

# خواندن مقالات
articles = []
for filename in os.listdir(ARTICLES_DIR):
    if filename.endswith('.md'):
        path = os.path.join(ARTICLES_DIR, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
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

# ساختار هاب‌ها
brands_hub = defaultdict(list)
series_hub = defaultdict(lambda: defaultdict(list))
topics_hub = defaultdict(list)
countries_hub = defaultdict(list)

for a in articles:
    brands_hub[a['brand']].append(a)
    series_hub[a['brand']][a['series']].append(a)
    topics_hub[a['topic']].append(a)
    countries_hub[a['country']].append(a)

# توابع تولید HTML
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
                    related_articles=related_articles[:5])

def generate_hub_page(title, articles_list, output_path):
    html_articles = '\n'.join([f'<li><a href="../../articles/{a["filename"]}">{a["title"]}</a></li>' for a in articles_list])
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<link rel="stylesheet" href="../../assets/css/style.css">
</head>
<body>
{header_html}
<main>
<h1>{title}</h1>
<ul>
{html_articles}
</ul>
</main>
{footer_html}
</body>
</html>"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def generate_home_page(latest_articles):
    html_articles = '\n'.join([f'<li><a href="articles/{a["filename"]}">{a["title"]}</a> - {a["date"]}</li>' for a in latest_articles[:10]])
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AvNexo - Expert Smartphone Guides</title>
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
{header_html}
<main>
<h1>AvNexo</h1>
<section>
<h2>Latest Articles</h2>
<ul>
{html_articles}
</ul>
</section>
</main>
{footer_html}
</body>
</html>"""
    with open(os.path.join(BUILD_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

# پاکسازی پوشه builds و ساخت زیرپوشه‌ها
os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'articles'), exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'brands'), exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'topics'), exist_ok=True)
os.makedirs(os.path.join(BUILD_DIR, 'countries'), exist_ok=True)

# تولید صفحات مقاله
for article in articles:
    related = [a for a in articles if a != article and 
               (a['brand']==article['brand'] or 
                a['topic']==article['topic'] or 
                a['country']==article['country'])]
    html = generate_article_page(article, related)
    with open(os.path.join(BUILD_DIR, 'articles', article['filename']), 'w', encoding='utf-8') as f:
        f.write(html)

# تولید هاب برند و سری
for brand, brand_articles in brands_hub.items():
    os.makedirs(os.path.join(BUILD_DIR, 'brands', brand.lower()), exist_ok=True)
    generate_hub_page(f'{brand} Hub', brand_articles,
                      os.path.join(BUILD_DIR, 'brands', brand.lower(), 'index.html'))
    for series, series_articles in series_hub[brand].items():
        os.makedirs(os.path.join(BUILD_DIR, 'brands', brand.lower(), series.lower()), exist_ok=True)
        generate_hub_page(f'{brand} {series} Hub', series_articles,
                          os.path.join(BUILD_DIR, 'brands', brand.lower(), series.lower(), 'index.html'))

# تولید هاب موضوع
for topic, topic_articles in topics_hub.items():
    folder = os.path.join(BUILD_DIR, 'topics', topic.lower().replace(' & ','-').replace(' ','-'))
    os.makedirs(folder, exist_ok=True)
    generate_hub_page(f'{topic} Hub', topic_articles,
                      os.path.join(folder, 'index.html'))

# تولید هاب کشور
for country, country_articles in countries_hub.items():
    folder = os.path.join(BUILD_DIR, 'countries', country.lower())
    os.makedirs(folder, exist_ok=True)
    generate_hub_page(f'{country} Hub', country_articles,
                      os.path.join(folder, 'index.html'))

# تولید هوم پیج
generate_home_page(articles)

print("✅ All HTML pages generated successfully!")
