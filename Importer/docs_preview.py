import os
import sys
import re


def format_pages(input_dir, output_dir, repository_url):

    if repository_url == None:
        return

    target_files = [
    ['index.htm', re.compile(r'(<div class="title">[\r\n]+[\t ]+)[^\r\n]+'), r'\1GameMaker Studio 2 マニュアル Preview'], 
    ['index.htm', re.compile(r'<title>[^\r\n]+</title>'), 
    r'<title>GameMaker Studio 2 マニュアル - Preview</title>'], 
    ['Content.htm', re.compile(r'(Zeus_Banner.png ?"[^\r\n]+[\r\n]+)( *<\!--<div class="body-scroll" [^>]+>-->[\r\n]+)?( *<p>[  ]*</p>[\r\n]+)([^\r\n]+[\r\n]+[^\r\n]+<!-- GitHub_Pages_Preview -->[\r\n]+)?'), 
    r'\1\2\3  <p><u><b>注意:</b> こちらは翻訳の結果をテストするための<b>プレビュー版</b>です。そのため<b>検索機能が利用不可</b>となっています。<br>'
    r'検索機能を利用するには、以下のリンク先からリリース版を入手してください。</u></p>\n  <p><a href="https://github.com/' + repository_url + r'">'
    r'Gamemaker Studio 2 日本語化プロジェクト</a></p><hr><!-- GitHub_Pages_Preview -->\n']
    ]

    if not os.path.exists(input_dir):
        return

    for target in target_files:

        source_path = os.path.join(input_dir, target[0])
        with open(source_path, 'r', encoding='utf_8_sig') as f:
            lines = f.read()

        lines = target[1].sub(target[2], lines)

        dest_path = os.path.join(output_dir, target[0])
        os.makedirs(os.path.split(dest_path)[0], exist_ok=True)

        with open(dest_path, 'w+', encoding='utf_8_sig') as f:
            f.write(lines)

    return
