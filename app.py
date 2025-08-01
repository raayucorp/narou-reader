import re
import time
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, redirect, url_for

# --- Flaskアプリケーションの初期化 ---
app = Flask(__name__)

# --- グローバル設定 ---
BASE_URL = "https://ncode.syosetu.com/"
SEARCH_URL = "https://yomou.syosetu.com/search.php"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

# ==============================================================================
# --- HTMLテンプレート ---
# 3DSなどの低機能ブラウザ向けに、非常にシンプルなHTMLを定義します。
# ==============================================================================

# --- 共通のベーステンプレート ---
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}軽量なろうリーダー{% endblock %}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; line-height: 1.6; margin: 8px; }
        h1, h2, h3 { margin: 1em 0 0.5em 0; padding-bottom: 0.2em; border-bottom: 1px solid #ccc;}
        a { color: #007bff; text-decoration: none; }
        .container { max-width: 800px; margin: 0 auto; }
        .nav { margin: 1em 0; padding: 0.5em 0; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; }
        .nav a { margin-right: 1em; }
        .summary { background: #f4f4f4; padding: 0.8em; border-left: 4px solid #ccc; margin: 1em 0; font-size: 0.9em; }
        .pagination { margin: 1em 0; text-align: center; }
        .pagination a { margin: 0 0.5em; }
        .error { color: red; font-weight: bold; }
        ul, ol { padding-left: 20px; }
        li { margin-bottom: 0.5em; }
        .form-group { margin-bottom: 1em; }
        input[type="text"] { width: 70%; padding: 5px; }
        input[type="submit"] { padding: 5px 10px; }
        .chapter-title { background-color: #eee; padding: 0.3em 0.5em; font-weight: bold; margin-top: 1.5em; }
        .footer-note { font-size: 0.8em; color: #666; text-align: center; margin-top: 2em; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><a href="/">軽量なろうリーダー</a></h1>
        </header>
        <main>
            {% block content %}{% endblock %}
        </main>
        <footer>
            <hr>
            <p class="footer-note">
                このサイトは「小説家になろう」のコンテンツをスクレイピングし、軽量化して表示しています。<br>
                個人利用の範囲でご利用ください。
            </p>
        </footer>
    </div>
</body>
</html>
"""

# --- トップページ（検索フォーム） ---
INDEX_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}", """
    <h2>小説検索</h2>
    <form action="{{ url_for('search') }}" method="get">
        <div class="form-group">
            <input type="text" name="q" placeholder="作品名、作者名など" required>
            <input type="submit" value="検索">
        </div>
    </form>
"""
)

# --- 検索結果ページ ---
SEARCH_RESULTS_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block title %}{{ query }} の検索結果{% endblock %}", ""
).replace(
    "{% block content %}", """
    <h2>「{{ query }}」の検索結果 ({{ total }}件)</h2>
    
    {% if results %}
        <ol>
        {% for novel in results %}
            <li>
                <strong><a href="{{ url_for('table_of_contents', ncode=novel.ncode) }}">{{ novel.title }}</a></strong><br>
                作者: {{ novel.author }}<br>
                <div class="summary">{{ novel.summary }}</div>
            </li>
        {% endfor %}
        </ol>
    {% else %}
        <p>作品が見つかりませんでした。</p>
    {% endif %}

    <div class="pagination">
        {% if pagination.prev %}
            <a href="{{ url_for('search', q=query, page=pagination.prev) }}">< 前のページ</a>
        {% endif %}
        <span>- {{ current_page }} -</span>
        {% if pagination.next %}
            <a href="{{ url_for('search', q=query, page=pagination.next) }}">次のページ ></a>
        {% endif %}
    </div>
"""
)

# --- 目次ページ ---
TOC_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block title %}{{ novel.title }}{% endblock %}", ""
).replace(
    "{% block content %}", """
    <h2>{{ novel.title }}</h2>
    <p>作者: {{ novel.author }}</p>

    <h3>あらすじ</h3>
    <div class="summary">{{ novel.summary | safe }}</div>
    
    <h3>目次</h3>
    {% if novel.episodes %}
        <div>
        {% for item in novel.episodes %}
            {% if item.is_chapter %}
                <div class="chapter-title">{{ item.title }}</div>
            {% else %}
                <ul style="list-style-type: none; padding-left: 10px;">
                    <li><a href="{{ url_for('viewer', ncode=novel.ncode, chapter=item.chapter) }}">{{ item.title }}</a></li>
                </ul>
            {% endif %}
        {% endfor %}
        </div>
    {% else %}
        <p>目次が取得できませんでした。</p>
    {% endif %}

    <div class="pagination">
        {% if pagination.prev %}
            <a href="{{ url_for('table_of_contents', ncode=novel.ncode, p=pagination.prev) }}">< 前のページ</a>
        {% endif %}
        <span>- {{ current_page }} -</span>
        {% if pagination.next %}
            <a href="{{ url_for('table_of_contents', ncode=novel.ncode, p=pagination.next) }}">次のページ ></a>
        {% endif %}
    </div>
"""
)

# --- 本文表示ページ ---
VIEWER_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block title %}{{ novel.title }} - {{ novel.subtitle }}{% endblock %}", ""
).replace(
    "{% block content %}", """
    <h2><a href="{{ url_for('table_of_contents', ncode=ncode) }}">{{ novel.title }}</a></h2>
    <h3>{{ novel.subtitle }}</h3>

    <div class="nav">
        {% if nav.prev %}<a href="{{ nav.prev }}">＜ 前の話</a>{% endif %}
        <a href="{{ nav.toc }}">目次</a>
        {% if nav.next %}<a href="{{ nav.next }}">次の話 ＞</a>{% endif %}
    </div>

    <div id="novel_body">
        {% for line in novel.body %}
            <p>{{ line | safe }}</p>
        {% endfor %}
    </div>

    <div class="nav">
        {% if nav.prev %}<a href="{{ nav.prev }}">＜ 前の話</a>{% endif %}
        <a href="{{ nav.toc }}">目次</a>
        {% if nav.next %}<a href="{{ nav.next }}">次の話 ＞</a>{% endif %}
    </div>
"""
)

# --- エラーページ ---
ERROR_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block title %}エラー{% endblock %}", ""
).replace(
    "{% block content %}", """
    <h2>エラーが発生しました</h2>
    <p class="error">{{ message }}</p>
    <a href="/">トップに戻る</a>
"""
)

# ==============================================================================
# --- ヘルパー関数 ---
# ==============================================================================

def get_page_content(url, params=None):
    """指定されたURLのHTMLコンテンツを取得する"""
    try:
        time.sleep(1) # サーバー負荷軽減のため1秒待機
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def convert_ruby_tags(soup_tag):
    """ルビタグを(ふりがな)形式に変換する"""
    if not soup_tag:
        return ""
    for ruby in soup_tag.find_all('ruby'):
        rt = ruby.find('rt')
        if not rt:
            continue
        for rp in ruby.find_all('rp'):
            rp.decompose()
        rt_text = rt.get_text(strip=True)
        rt.decompose()
        rb_text = ruby.get_text(strip=True)
        ruby.replace_with(f'{rb_text}({rt_text})')
    # <br>タグを改行に変換
    for br in soup_tag.find_all('br'):
        br.replace_with('\n')
    return soup_tag.get_text(separator='\n').strip()
    
def get_ncode_from_url(url):
    """URLからNコードを抽出する"""
    match = re.search(r'/(n[a-zA-Z0-9]{5,})/?', url)
    return match.group(1) if match else None

# ==============================================================================
# --- スクレイピング関数 ---
# ==============================================================================

def scrape_search_page(query, page=1):
    """検索結果ページをスクレイピングする"""
    params = {'word': query, 'p': page}
    soup = get_page_content(SEARCH_URL, params)
    if not soup:
        return None

    results = []
    search_results = soup.find_all('div', class_='searchkekka_box')
    for item in search_results:
        title_tag = item.find('a', class_='tl')
        author_tag = item.find('a', href=re.compile(r'https://mypage.syosetu.com/\d+/'))
        summary_tag = item.find('div', class_='ex')
        
        if title_tag and title_tag.get('href'):
            ncode = get_ncode_from_url(title_tag['href'])
            if ncode:
                results.append({
                    'title': title_tag.get_text(strip=True),
                    'ncode': ncode,
                    'author': author_tag.get_text(strip=True) if author_tag else '作者不明',
                    'summary': summary_tag.get_text(strip=True) if summary_tag else 'あらすじなし'
                })

    # ページネーション
    pagination = {'prev': None, 'next': None}
    pager = soup.find('div', class_='pager')
    if pager:
        current_page = page
        next_page_tag = pager.find('a', string=re.compile(r'次へ'))
        if next_page_tag and 'href' in next_page_tag.attrs:
             pagination['next'] = current_page + 1
        
        if current_page > 1:
            pagination['prev'] = current_page - 1
            
    total_text = soup.find('span', style="font-size:150%; font-weight:bold;").find_next_sibling(string=True)
    total_count = re.search(r'(\d+)作品', total_text)
    total = total_count.group(1) if total_count else '多数'

    return {'results': results, 'pagination': pagination, 'total': total}

def scrape_toc_page(ncode, page_num=1):
    """作品の目次ページをスクレイピングする"""
    url = urljoin(BASE_URL, f"{ncode}/")
    soup = get_page_content(url, params={'p': page_num})
    if not soup:
        return None

    novel_info = {
        'title': soup.find('p', class_='novel_title').get_text(strip=True) if soup.find('p', class_='novel_title') else soup.find('h1', class_='p-novel__title').get_text(strip=True),
        'ncode': ncode,
        'author': soup.find('div', class_='novel_writername').get_text(strip=True).replace('作者：', '') if soup.find('div', class_='novel_writername') else soup.find('div', class_='p-novel__author').get_text(strip=True).replace('作者：', ''),
        'summary': convert_ruby_tags(soup.find('div', id='novel_ex')),
        'episodes': []
    }

    index_box = soup.find('div', class_='index_box')
    if not index_box:
       # 新しいレイアウトに対応
       index_box = soup.find('div', class_='p-eplist')

    if index_box:
      items = index_box.find_all(['div', 'dl'], class_=re.compile(r'(chapter_title|novel_sublist2|p-eplist__chapter-title|p-eplist__sublist)'))
      for item in items:
          if 'chapter' in ' '.join(item.get('class', [])):
              novel_info['episodes'].append({
                  'is_chapter': True,
                  'title': item.get_text(strip=True)
              })
          else:
              sublist_tag = item.find('a')
              if sublist_tag and sublist_tag.get('href'):
                  link = sublist_tag['href']
                  chapter = link.strip('/').split('/')[-1]
                  novel_info['episodes'].append({
                      'is_chapter': False,
                      'title': sublist_tag.get_text(strip=True),
                      'chapter': chapter
                  })

    # ページネーション
    pagination = {'prev': None, 'next': None}
    pager = soup.find('div', class_=re.compile(r'pager|novelview_pager-box'))
    if pager:
      next_page_tag = pager.find('a', string=re.compile(r'次へ'))
      if next_page_tag and next_page_tag.get('href'):
          pagination['next'] = page_num + 1
      if page_num > 1:
          pagination['prev'] = page_num - 1
          
    return novel_info, pagination

def scrape_viewer_page(ncode, chapter):
    """小説の本文ページをスクレイピングする"""
    url = urljoin(BASE_URL, f"{ncode}/{chapter}/")
    soup = get_page_content(url)
    if not soup:
        return None

    # 本文のルビを変換
    novel_honbun = soup.find('div', id='novel_honbun')
    if novel_honbun:
        for ruby in novel_honbun.find_all('ruby'):
            rt = ruby.find('rt')
            if not rt: continue
            for rp in ruby.find_all('rp'): rp.decompose()
            rt_text = rt.get_text(strip=True)
            rt.decompose()
            rb_text = ruby.get_text(strip=True)
            ruby.replace_with(f'{rb_text}({rt_text})')

    novel = {
        'title': soup.find('div', class_='contents1').find('a').get_text(strip=True) if soup.find('div', class_='contents1') else '作品タイトル不明',
        'subtitle': soup.find('p', class_='novel_subtitle').get_text(strip=True) if soup.find('p', class_='novel_subtitle') else 'サブタイトル不明',
        'body': [p.get_text('\n', strip=True) for p in novel_honbun.find_all('p')] if novel_honbun else ['本文が取得できませんでした。']
    }

    # ナビゲーション
    nav = {'prev': None, 'toc': url_for('table_of_contents', ncode=ncode), 'next': None}
    pager = soup.find('div', class_='novel_bn')
    if pager:
        prev_tag = pager.find('a', string=re.compile(r'前へ'))
        if prev_tag and prev_tag.get('href'):
            nav['prev'] = url_for('viewer', ncode=ncode, chapter=prev_tag['href'].strip('/').split('/')[-1])
        
        next_tag = pager.find('a', string=re.compile(r'次へ'))
        if next_tag and next_tag.get('href'):
            nav['next'] = url_for('viewer', ncode=ncode, chapter=next_tag['href'].strip('/').split('/')[-1])

    return novel, nav

# ==============================================================================
# --- Flask ルート定義 ---
# ==============================================================================

@app.route('/')
def index():
    """トップページ: 検索フォームを表示"""
    return render_template_string(INDEX_TEMPLATE)

@app.route('/search')
def search():
    """検索結果を表示"""
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)

    if not query:
        return redirect(url_for('index'))

    data = scrape_search_page(query, page)
    if data is None:
        return render_template_string(ERROR_TEMPLATE, message="検索結果の取得に失敗しました。時間をおいて再試行してください。")

    return render_template_string(
        SEARCH_RESULTS_TEMPLATE,
        query=query,
        results=data['results'],
        total=data['total'],
        pagination=data['pagination'],
        current_page=page
    )

@app.route('/novel/<ncode>')
def table_of_contents(ncode):
    """作品の目次を表示"""
    page_num = request.args.get('p', 1, type=int)
    novel_data, pagination_data = scrape_toc_page(ncode, page_num)

    if novel_data is None:
        return render_template_string(ERROR_TEMPLATE, message="目次ページの取得に失敗しました。Nコードが正しいか確認してください。")

    return render_template_string(
        TOC_TEMPLATE,
        novel=novel_data,
        pagination=pagination_data,
        current_page=page_num
    )

@app.route('/novel/<ncode>/<chapter>')
def viewer(ncode, chapter):
    """小説の本文を表示"""
    novel_data, nav_data = scrape_viewer_page(ncode, chapter)

    if novel_data is None:
        return render_template_string(ERROR_TEMPLATE, message="本文ページの取得に失敗しました。")

    return render_template_string(
        VIEWER_TEMPLATE,
        ncode=ncode,
        novel=novel_data,
        nav=nav_data
    )

# --- 実行 ---
if __name__ == '__main__':
    # 開発環境でテスト実行する場合
    # python app.py で起動
    app.run(host='0.0.0.0', port=8000, debug=True)
