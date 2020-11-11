import os
import sys
import re
import regex
import urllib.request
import zipfile
import datetime

import docs_preview

from pathlib import Path
from translate.convert.po2html import converthtml
from translate.convert.csv2po import convertcsv
from janome.tokenizer import Tokenizer
from natsort import natsorted

################# 各種設定 ###############

# 日本語と英数字の間に半角スペースを自動で挿入するかどうか
#  0で無効、1でスペースを挿入、2でスペースを削除
SPACE_ADJUSTMENT = 1

# whxdata以下のファイルを翻訳するかどうか
EXPORT_WHXDATA = True

# Indexメニューに自動生成したトピックを追加するかどうか
ENABLE_EXTRA_INDEX = True

# IDEおよびマニュアルの二次ファイルを生成するかどうか
#  これらはオーバーライドデータと専用の辞書により、イベント名、DnDアクション名を日本語に置き換えたものです。
#  Github Pagesには影響せず、個別のアーカイブとして出力されます。
ENABLE_FULL_TRANSLATION = False

# GitHub Pagesをプレビュー版仕様にするかどうか
#  リポジトリ容量の肥大化を防ぐために検索機能を無効化（関連するjsファイルをdocsから削除）し、トップページをプレビュー版であることを示すものに変更します。
#  GitHub Pagesのみに影響し、リリースは影響を受けません。
GENERATE_AS_PREVIEW = True

input_dir = 'utf8/csv/' # ParaTranzのCSVディレクトリ
ide_path = ['utf8/english.csv', 'utf8/ide_english_dnd.csv'] # ParaTranzのIDE言語ファイル
glossary_path = 'utf8/manual_glossary.csv' # マニュアルの用語集
table_of_contents_path = 'utf8/manual_leftmenu.csv' # 左メニューの翻訳ファイル

doc_dir = 'docs'

template_html_dir = 'repo/tr_sources/source_html/' # GitPagesリポジトリのテンプレートHTML
template_pot_dir = 'repo/tr_sources/source_pot/' # GitPagesリポジトリのテンプレートPOT
template_csv_dir = 'repo/tr_sources/source_csv/' # GitPagesリポジトリのテンプレートCSV
template_db_dir = 'repo/tr_sources/source_db/' # GitPagesリポジトリのテンプレートDBファイル

output_dir = 'Converted/'
output_ex_dir = 'Converted_EX/'
output_preview_dir = 'Preview/'
output_manual_dirname = 'manual'
generated_dir = 'generated/'

dnd_dirname = 'Drag_And_Drop/Drag_And_Drop_Reference/'
gml_dirname = 'GameMaker_Language/GML_Reference/'

release_dir = 'Release/'
ide_base_name = [['japanese.csv', 'japanese_alt.csv'], ['ide_japanese_dnd.csv', 'ide_japanese_alt_dnd.csv']] # IDEの言語ファイル出力名
ide_overrides_path = [['override', 'override_extra'], ['ide_overrides.csv', 'ide_dnd_overrides.csv']] # IDEのオーバーライドcsv

dict_dnd_path = 'override_extra/dict/dict_dnd.dict' # マニュアルの置換辞書（DnDアクション名）
dict_misc_all_path = 'override_extra/dict/dict_misc.dict' # マニュアルの置換辞書（イベント名とその他）


po_replacer = [
['"Language: zh_CN\\n"', '"Language: ja_JP\\n"'],
['"Language-Team: LANGUAGE <LL@li.org>\\n"', '"Language-Team: GMS2 Japanese Translation Team <paratranz.cn/projects/1100>\\n"'],
['"Project-Id-Version: PACKAGE VERSION\\n"', '"Project-Id-Version: Gamemaker Studio 2 EN2JP Translation Project\\n"']
]

restore_format_key = [re.compile('^"location","(source|target)","(target|source)"\n'), '"location","source","target"\n']

csv_commentout_tr = [
['Click here to see this page in full context', 'ページをすべて表示するにはここをクリック']
]

compiled_raw_csv_file_patter = re.compile(r'^' + input_dir + '.*\.csv$')

comma_replacer = re.compile(r',(?=(?:[^"\r\n]*"[^"\r\n]*")*[^"\r\n]*$)', re.MULTILINE | re.DOTALL)


dict_dnd = []
dict_misc = []

search_results = []
search_keywords = []
topic_index = []
glossary = []

search_results_full = []
search_keywords_full = []
topic_index_full = []

index_exist_name = {}
index_data = {}
index_data_full = {}
index_exist_name_full = {}

translation_info = [0, 0, 0, 0] # 合計行数、合計翻訳数、追加された翻訳数、ワード数

##############################################################################################

def download_trans_zip_from_paratranz(project_id,
                                      secret,
                                      out_file_path,
                                      base_url="https://paratranz.cn"):
    """
    paratranzからzipをダウンロードする
    :param project_id:
    :param secret:
    :param base_url:
    :param out_file_path:
    :return:
    """

    request_url = "{}/api/projects/{}/artifacts/download".format(base_url, project_id)
    req = urllib.request.Request(request_url)
    req.add_header("Authorization", secret)

    my_file = open(out_file_path, "wb")

    try:
        my_file.write(urllib.request.urlopen(req).read())
    except IOError:
        print('Failed to download from paratranz')
        sys.exit(1)

    return out_file_path


def set_translation_count(old_lines, new_lines):
    global translation_info

    word_count = 0
    line_count = 0
    tr_count = [0, 0]

    old = comma_replacer.sub(r'\t', old_lines).splitlines(False)
    new = comma_replacer.sub(r'\t', new_lines).splitlines(False)
    pat_notags = re.compile(r'(<[^<]+>|(\{[^\}]+\}))')

    if len(old) == len(new):
        for idx in range(len(old)):
            s_old = old[idx].split('\t')
            s_new = new[idx].split('\t')

            if s_old[0] != s_new[0]: # キーが異なる＝ファイルがアップデートされたため翻訳数に加算しない
                word_count = 0
                tr_count[1] = 0
                break
            elif len(s_old) < 3 and len(s_new) >= 3:
                s_new[1] = pat_notags.sub('', s_new[1]) # タグはワード数としてカウントしない
                word_count += len(s_new[1].split())
                tr_count[1] += 1

    for line in new:
        line_count += 1
        s = line.split('\t')
        if len(s) >= 3:
            if s[2]:
                tr_count[0] += 1

    translation_info[0] = translation_info[0] + line_count # 合計行数
    translation_info[1] = translation_info[1] + tr_count[0] # 合計翻訳数

    if word_count > 0:
        translation_info[2] += tr_count[1] # ワード数
        translation_info[3] += word_count # 追加翻訳数
    return


def convert_from_zip(paratranz_zip_path):
    global translation_info

    # リポジトリでのパスを辞書に代入
    source_files_dict = {}
    for current, subfolders, subfiles in os.walk(template_csv_dir):
        for file in subfiles:
            path = os.path.join(current, file)
            path = path.replace(template_csv_dir, '')
            path = os.path.splitext(path)[0]
            source_files_dict[re.sub(r'[\\/]', '', path).lower()] = path

    # アーカイブ内のファイルを個別に処理
    with zipfile.ZipFile(paratranz_zip_path) as zip_file:
        infos = zip_file.infolist() # 各メンバのオブジェクトをリストとして返す

        for info in infos:

            if compiled_raw_csv_file_patter.match(info.filename) is None:
                continue

            exoport_mode = ['']

            if ENABLE_FULL_TRANSLATION: # イベント名、DnDアクション名の翻訳が有効となっている場合は再実行する
                if info.filename.find(dnd_dirname) != -1:
                    exoport_mode.append('dnd')
                else:
                    exoport_mode.append('ev')

            for mode in exoport_mode:

                base_path = info.filename.replace(input_dir, '')
                base_path = os.path.splitext(base_path)[0]

                if mode:
                    # イベント名、DnDアクション名が翻訳されたファイルは別のディレクトリに出力
                    dest_dir = os.path.join(output_ex_dir, output_manual_dirname)
                else:
                    dest_dir = os.path.join(output_dir, output_manual_dirname)

                path_csv = os.path.join(dest_dir, 'csv', base_path) + '.csv'
                zip_lines = zip_file.read(info.filename).decode('utf-8-sig')

                if mode == '':
                    csv_old_path = os.path.join(generated_dir, output_manual_dirname, 'csv', base_path) + '.csv'
                    old_lines = ''

                    if os.path.exists(csv_old_path):
                        with open(csv_old_path, 'r', encoding='utf_8_sig') as f:
                            old_lines = f.read()

                    set_translation_count(old_lines, zip_lines)

                # ParaTranzのバックアップ用CSVファイルを出力
                os.makedirs(os.path.split(path_csv)[0], exist_ok=True)
                with open(path_csv, 'w+', encoding='utf_8_sig') as f:
                    f.write(zip_lines)


                # 基本パスを復元
                try:
                    encoded_path = base_path.encode('cp437').decode('cp932')
                except UnicodeEncodeError:
                    encoded_path = base_path
                base_path = encoded_path
                base_path = base_path.replace('／', '/') # 置き換えられたファイル名の'／'をパスとしての'/'に復元
                
                base_path = re.sub(r'(GML_Reference)/[A-Z]-[A-Z]/', r'\1/', base_path, flags=re.IGNORECASE) # GMLリファレンスの細分化した一時ディレクトリをパスから取り除く

                try:
                    base_path = source_files_dict[re.sub(r'\/', '', base_path).lower()] # ParaTranzのパスからリポジトリでのパスを取得
                except:
                    print('SKIP! {0} : No csv template for {1} was found'.format((os.path.join(template_csv_dir, base_path) + '.csv'), path_csv))
                    continue

                path_source_csv = os.path.join(template_csv_dir, base_path) + '.csv'
                path_cnv_csv = os.path.join(dest_dir, 'cnv_csv', base_path) + '.csv'


                # 整形したCSVファイルを出力
                format_l = format_lines(mode)

                with open(path_source_csv, 'r', encoding='utf_8_sig') as f:
                    source_lines = f.read()

                csv_lines = format_l.restore_csv_commentout(source_lines, zip_lines) # コメントアウトしたCSV行を復元
                csv_lines = format_l._csv(csv_lines, base_path)

                if mode:
                    path_cnv_normal= os.path.join(output_dir, output_manual_dirname, 'cnv_csv', base_path) + '.csv'

                    with open(path_cnv_normal, 'r', encoding='utf_8_sig') as f:
                        lines_normal = f.read()

                        if lines_normal == csv_lines: # 自動翻訳前と内容が同じのためスキップ
                            continue

                os.makedirs(os.path.split(path_cnv_csv)[0], exist_ok=True)
                with open(path_cnv_csv, 'w+', encoding='utf_8_sig') as f_input:
                    f_input.write(csv_lines)


                # CSVファイルをPOファイルに変換
                path_po = os.path.join(dest_dir, 'cnv_po', base_path) + '.po'
                path_template_po = os.path.join(template_pot_dir, base_path) + '.pot'

                if not os.path.exists(path_template_po):
                    print('SKIP! {0} : No pot template for {1} was found'.format(path_template_po, path_po))
                    continue
                    
                os.makedirs(os.path.split(path_po)[0], exist_ok=True)

                f_input = open(path_cnv_csv, 'rb')
                f_output = open(path_po, 'wb+')
                f_template = open(path_template_po, 'rb')
                
                convertcsv(f_input, f_output, f_template, charset='utf_8_sig') # Translate-KitによるCSV > POの変換処理

                f_input.close()
                f_output.close()
                f_template.close()
                
                
                # POの整形
                with open(path_po, 'r', encoding='utf_8_sig') as f_po:
                    po_lines = f_po.read()

                po_lines = format_l._po(po_lines)

                with open(path_po, 'w+', encoding='utf_8_sig') as f_po:
                    f_po.write(po_lines)
                

                # HTMLへの変換を開始
                path_output = os.path.join(dest_dir, doc_dir, base_path) + '.htm'
                path_template_html = os.path.join(template_html_dir, base_path) + '.htm'
                
                if not os.path.exists(path_template_html):
                    print('SKIP! {0} : No html template for {1} was found'.format(path_template_html, path_po))
                    continue
                
                os.makedirs(os.path.split(path_output)[0], exist_ok=True)
                
                f_po = open(path_po, 'rb')
                f_output = open(path_output, 'wb+')
                f_template = open(path_template_html, 'rb')
                
                print('converting: {0} to .htm'.format(path_po))
                converthtml(f_po, f_output, f_template) # Translate-KitによるPO > HTMLの変換処理

                f_po.close()
                f_output.close()
                f_template.close()


                # HTMLの整形
                with open(path_output, 'r', encoding='utf_8_sig') as f_output:
                    html_lines = f_output.read()

                html_lines = format_l._html(html_lines)

                with open(path_output, 'w+', encoding='utf_8_sig') as f_output:
                    f_output.write(html_lines)

        return

##############################################################################################


class format_lines():

    def __init__(self, mode):
        self.mode = mode

    def restore_csv_commentout(self, source, new): # Converterでコメントアウトされた行を復元

        source_lines = source.splitlines()
        new_lines = new.splitlines()

        for idx, line in enumerate(source_lines):
            if '#CSV_COMMENT_OUT#' in line:
                line = line.replace('#CSV_COMMENT_OUT#', '')
                line = comma_replacer.sub(r'\t', line)
                separated = re.split(r'\t', line)

                if len(separated) > 2:
                    for tr in csv_commentout_tr:
                        if tr[0] == separated[1].strip('"'):
                            separated[2] = '"' + tr[1] + '"'
                            break

                line = ','.join(separated)

                new_lines.insert(idx, line)

        return '\n'.join(new_lines)
    
    def get_replaced_list(self, source, translation, strip_chr, finder, pattern = '', replacer = ''): # 原文/訳文を整形してリストで返す
        result = []
        if not finder[0] in finder[1]: # 翻訳が存在しない
            return ['']

        # 改行を削除
        result.append(source.rstrip('\r\n'))
        result.append(translation.rstrip('\r\n'))

        # 前後の指定文字列を削除
        if strip_chr:
            result[0] = result[0].strip(strip_chr)
            result[1] = result[1].strip(strip_chr)

        # 正規表現置換
        if pattern:
            result[0] = re.sub(pattern, replacer, result[0])
            result[1] = re.sub(pattern, replacer, result[1])

        # 翻訳行のDnDアクション/イベント名を置換
        if self.mode == 'dnd':
            result[1] = namedict().replace_by_dict(result[1], dict_dnd)
        elif self.mode == 'ev':
            result[1] = namedict().replace_by_dict(result[1], dict_dnd)

        return result

    # ---------------------------------------------------------------------------------------

    def _csv(self, lines, base_path): # CSVの整形
    
        # 正規表現パターン定義
        insert_pat = [ # 半角スペースの挿入パターン
        regex.compile(r'([^ \p{Ps}\p{Pe}">])((<[^>]+>)*)(<b>|<strong>)((<[^>]+>)*)'),
        regex.compile(r'((<[^>]+>)*)(</b>|</strong>)((<[^>]+>)*)([^ \p{Ps}\p{Pe}"<])'),
        regex.compile(r'([^ \p{Ps}\p{Pe}">])((<[^>]+>)*)(<a href=[^>]+>)((<[^>]+>)*)'),
        regex.compile(r'((<[^>]+>)*)(</a>)((<[^>]+>)*)([^ \p{Ps}\p{Pe}"<])'),
        regex.compile(r'([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])((<[^>]+>)*)((\p{Ps})?)([a-zA-Z0-9™])'),
        regex.compile(r'(([a-zA-Z0-9™])(\p{Pe}?))((<[^>]+>)*)((\p{Ps})?)([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])'),
        re.compile(r'(、|。|！|？) '),
        re.compile(r' (、|。|！|？)'),
        re.compile(r'\\n ')
        ]
    
        remove_pat = [ # 半角スペースの削除パターン
        regex.compile(r'([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}]) ?((<[^>]+>)*) ?((\p{Ps})?)([a-zA-Z0-9™])'),
        regex.compile(r'(([a-zA-Z0-9™])(\p{Pe}?)) ?((<[^>]+>)*)((\p{Ps})?) ?([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])')
        ]
    
        base_path = base_path.replace('\\', '\\\\')

    
        ############# 一行ごとの処理 #############
        lines = comma_replacer.sub(r'\t', lines)
        new_lines = []
    
        for line in lines.splitlines(False):
            separated = re.split(r'\t', line)
    
            SKIP = False
    
            if len(separated) < 3: # 翻訳がないため何もしない
                SKIP = True
            elif '{ANY_CODE}' in separated[2]: # コード行には何もしない
                SKIP = True

            if SKIP == False:
                source = separated[1] # 原文
                translation = separated[2] # 翻訳
        
                # 日本語/英数字、および<b>, <a href>タグの間に半角スペースを挿入・削除
                if SPACE_ADJUSTMENT == 1: # 半角スペースを挿入する場合
                    translation = insert_pat[0].sub(r'\1 \2\4\5', translation)
                    translation = insert_pat[1].sub(r'\1\3\4 \6', translation)
                    translation = insert_pat[2].sub(r'\1 \2\4\5', translation)
                    translation = insert_pat[3].sub(r'\1\3\4 \6', translation)
                    translation = insert_pat[4].sub(r'\1 \2\4\6', translation)
                    translation = insert_pat[5].sub(r'\1\4 \6\8', translation)
                    translation = insert_pat[6].sub(r'\1', translation)
                    translation = insert_pat[7].sub(r'\1', translation)
                    translation = insert_pat[8].sub(r'\\n', translation)
        
                elif SPACE_ADJUSTMENT == 2: # 半角スペースを削除する場合
                    translation = remove_pat[0].sub(r'\1\2\4\6', translation)
                    translation = remove_pat[1].sub(r'\1\4\6\8', translation)
        
                # 翻訳行をタグで分離
                notags = re.split(r'((?:<[^>]+>)|(?:\([a-zA-Z0-9 ]+\))|(?:（[a-zA-Z0-9 ]+）)|(?:\[[a-zA-Z0-9 ]+\]))', translation)
                notags_cnv = []
        
                for m in notags:
        
                    if m == None:
                        continue
                    elif m.startswith('<') or m.startswith(r'\(') or m.startswith('（') or m.startswith(r'\['): # タグは置換しない
                        notags_cnv.append(m)
                        continue
        
                    # アクション/イベント名を辞書から置換
                    if self.mode == 'dnd':
                        m = namedict().replace_by_dict(m, dict_dnd)
                    elif self.mode == 'ev':
                        m = namedict().replace_by_dict(m, dict_misc)
        
                    notags_cnv.append(m)
        
                translation = ''.join(notags_cnv)
                
                # whxdata用の辞書にメタデータ等を追加
                append_list = self.get_replaced_list(source, translation, '"', ['{SEARCH_RESULT}', translation], r'{SEARCH_RESULT} *', '')
                if append_list[0] != '':
                    search_results_full.append(append_list) if self.mode != '' else search_results.append(append_list)
                
                append_list = self.get_replaced_list(source, translation, '"', ['{INDEX_KEYWORD}', translation], r'{INDEX_KEYWORD} *', '')
                if append_list[0] != '':
                    search_keywords_full.append(append_list) if self.mode != '' else search_keywords.append(append_list)
                
                append_list = self.get_replaced_list(source, translation, '"', ['<span data-open-text', translation], r'.*<span data-open-text *= *"+true"+ *>([^<]+)</span>.*', r'\1')
                if append_list[0] != '':
                    topic_index_full.append(append_list) if self.mode != '' else topic_index.append(append_list)
                
                append_list = self.get_replaced_list(source, translation, '"', ['.head.title:', separated[0]])
                if append_list[0] != '':
                    topic_index_full.append(append_list) if self.mode != '' else topic_index.append(append_list)
                    search_keywords_full.append(append_list) if self.mode != '' else search_keywords.append(append_list)

                # Index用の辞書にデータを追加
                global index_exist_name
                global index_data
                global index_exist_name_full
                global index_data_full
                filename = base_path.replace('\\\\', '/') + '.htm'

                patterns = [ # 特定のタグから始まる行を分割
                re.compile(r'(^[ "]*<strong>)([^<\,\./\\"]{2,})(</strong>)'), 
                re.compile(r'(^[ "]*<span data-open-text *= *"+true"+>)([^<\,\./\\"]{2,})(</span>)'),
                re.compile(r'(^[ "]*<tt>)([^<\,\./\\"]{2,})(</tt>)')
                ]
                SPLITTER = '{_SPLIT}'

                replaced_source = source
                replaced_translation = translation
                for pat in patterns:
                    replaced_source = pat.sub(r'\1' + SPLITTER + r'\2\3', replaced_source)
                    replaced_translation = pat.sub(r'\1' + SPLITTER + r'\2\3', replaced_translation)

                s_source = re.split(r'(' + SPLITTER + r'[^<]+)', replaced_source)
                s_translation = re.split(r'(' + SPLITTER + r'[^<]+)', replaced_translation)

                if len(s_source) == 3 and len(s_translation) == 3:
                    s = s_source[1][len(SPLITTER):]
                    s = s.strip(' ')

                    # 除外パターン
                    if re.match(r'^[0-9 -\/:-@\[-\`\{-\~\!\?]+$', s): # 数字記号半角スペースのみは除外
                        continue
                    elif re.match(r'^.*&[a-zA-Z]+.*', s): # タグの記号込みは除外
                        continue

                    tr = s_translation[1][len(SPLITTER):] + '\u200b' # RoboHelpの予約語（constructor, toStringなど）と同名の場合は動作しなくなるため、ゼロ幅スペースを付加して被らないようにする

                    # 既存のトピックと重複していなければ辞書に追加
                    if self.mode != '':
                        if not s.upper() in index_exist_name_full:
                            index_exist_name_full[s.upper()] = True
                            index_data_full[tr] = filename
                    else:
                        if not s.upper() in index_exist_name:
                            index_exist_name[s.upper()] = True
                            index_data[tr] = filename


                separated[1] = source
                separated[2] = translation

            new_lines.append(','.join(separated))

        lines = '\n'.join(new_lines)
        ######################################


        # テンプレートを復元
        if restore_format_key[0] != '':
            lines = restore_format_key[0].sub( '', lines)
            lines = restore_format_key[1] + lines
    
        # キーを復元
        orig_key = 'YoYoStudioRoboHelp'
        if os.path.split(base_path)[0]:
            orig_key = orig_key + '/' + os.path.split(base_path)[0]
        orig_key = orig_key.replace('/', '\\\\')
        lines = re.sub(r'([^"\r\n]+\.html?\+[^:]+:[0-9]+\-[0-9]+)', orig_key + '\\\\' + r'\1', lines)
    
        # ダウンロード後にコメント列が削除されてしまうため空の列を挿入
        lines = re.sub(r'([\r\n]+)', r',""\1', lines)
    
        return lines
    

    def _po(self, lines): # POの整形
    
        for rp in po_replacer:
            # プロパティの情報を置き換え
            if rp[0] in lines and rp[1] != '':
                lines = lines.replace(rp[0], rp[1], 1)
    
        return lines
    

    def _html(self, lines): # HTMLの整形
    
        # コードの識別子を削除
        lines = re.sub(r'{ANY_CODE} ?', '', lines)
    
        # 画像テキストの識別子を削除
        lines = re.sub(r'{IMG_TXT} ?', '', lines)
    
        # 対訳識別子を削除
        lines = re.sub(r'{CTR_S}', '', lines)
    
        # 抽出した検索結果テキストを削除
        lines = re.sub(r'<p>[^<]*{SEARCH_RESULT}[^<]*</p>', '', lines)
    
        # 抽出したキーワードテキストを削除
        lines = re.sub(r'<p>[^<]*{INDEX_KEYWORD}[^<]*</p>', '', lines)
    
        # URLのドットを復元
        lines = re.sub(r'{\-dot\-}', r'.', lines)
    
        # Converterでキー化した用語集の用語を復元
        for keyword in glossary:
            if keyword[0] in lines:
                lines = lines.replace(keyword[0], keyword[4])
    
        # ノーブレークスペースを復元
        separated = re.split('(({nbsp_x[0-9]+})+)', lines)
        pre_nbsp = False
        new_lines = ''
    
        for m in separated:
    
            if pre_nbsp:
                pre_nbsp = False
                continue
            elif 'nbsp_x' in m:
                cnt = int(re.sub(r"\D", "", m))
                m = ''
    
                while cnt > 0:
                    m += '\u00a0'
                    cnt -= 1
                pre_nbsp = True
    
            new_lines += m
        
        return new_lines

##############################################################################################



class generate_file():

    def format_ide(self, lines, override_dict, is_alt):
        new_lines = ['Name,English,Translation,Restrictions,Comment']

        for line in lines.splitlines(False):
            line = comma_replacer.sub(r'\t', line)
            line = re.sub(r'"(["]+)', r'\1', line)
            line = line.replace('"""', '""')

            s = re.split(r'\t', line)

            if len(s) > 2:
                for d in override_dict:
                    if s[0] == d[0]:
                        s[1] = d[1]
                        s[2] = d[2]
                        break

                if is_alt == False:
                    if s[0].startswith('Event_') or (s[0].startswith('GMStd') and s[0].endswith('_Name')):
                        s[2] = s[1]
            else:
                s.append(s[1])

            new_lines.append(','.join(s) + ',' * (5 - len(s)))

        new_lines.append('')
        return '\n'.join(new_lines)

    def generate_ide_dict(self, lines):
        result = []
        for d in lines.splitlines(False):
            d = comma_replacer.sub(r'\t', d)
            dict_var = re.split(r'\t', d)
            result.append(dict_var)

        return result


    def _ide(self, paratranz_zip_path): # IDEの言語ファイルをバックアップし、さらに二次ファイルを生成

        for idx, file in enumerate(ide_path):

            with zipfile.ZipFile(paratranz_zip_path) as zip_file:
                try:
                    zip_lines = zip_file.read(file).decode('utf-8-sig')
                except:
                    continue

                ide_old_path = os.path.join(generated_dir, os.path.split(file)[1])
                ide_bak_path = os.path.join(output_dir, os.path.split(file)[1])

                # ParaTranzの元ファイルをバックアップ
                old_lines = ''
                if os.path.exists(ide_old_path):
                    with open(ide_old_path, 'r', encoding='utf_8_sig') as f:
                        old_lines = f.read()
                set_translation_count(old_lines, zip_lines)

                os.makedirs(os.path.split(ide_bak_path)[0], exist_ok=True)
                with open(ide_bak_path, 'w', encoding='utf_8_sig') as f:
                    f.write(zip_lines)

            # GMS2本体の言語ファイルを生成
            os.makedirs(release_dir, exist_ok=True)

            overrides_path = os.path.join(ide_overrides_path[0][0], ide_overrides_path[1][idx])

            if os.path.exists(overrides_path):
                with open(overrides_path, 'r', encoding='utf_8_sig') as f:
                    override_lines = f.read()
            else:
                override_lines = ''

            ide_lines = self.format_ide(zip_lines, self.generate_ide_dict(override_lines), False)
            ide_base_output_path = os.path.join(release_dir, ide_base_name[idx][0])

            with open(ide_base_output_path, 'w', encoding='utf_8_sig', newline='\r\n') as f:
                f.write(ide_lines)

            overrides_alt_path = os.path.join(ide_overrides_path[0][1], ide_overrides_path[1][idx])

            # 二次ファイルを生成
            if ENABLE_FULL_TRANSLATION == False or not os.path.exists(overrides_alt_path):
                return

            with open(overrides_alt_path, 'r', encoding='utf_8_sig') as f:
                override_lines = f.read()

            ide_lines = self.format_ide(zip_lines, self.generate_ide_dict(override_lines), True)
            ide_alt_output_path = os.path.join(release_dir, ide_base_name[idx][1])

            with open(ide_alt_output_path, 'w', encoding='utf_8_sig', newline='\r\n') as f:
                f.write(ide_lines)

        return


    def _dict_template(self, paratranz_zip_path): # バックアップしたIDEの言語ファイルからDnD、イベント名の辞書テンプレートを生成        

        tmp_dnd = []
        tmp_event_all = []

        ide_output_path = os.path.join(output_dir, os.path.split(ide_path[0])[1])

        if not os.path.exists(ide_output_path):
            return

        with open(ide_output_path, 'r', encoding='utf_8_sig', newline='\n') as f:
            ide_lines = f.read()

        for m in ide_lines.splitlines(False):

            matched = ''

            if re.match(r'"?GMStd[^,\r\n]+_Name"?,', m):
                matched = 'dnd'
            elif re.match(r'"?Event_[^,]+"?,', m):
                matched = 'ev'

            if matched:
                m = m.replace('"', '')
                m = comma_replacer.sub(r'\t', m)
                dict_var = re.split(r'\t', m)

                del dict_var[0]

                if len(dict_var) < 2: # 翻訳がない
                    continue
                if dict_var[0] == dict_var[1]: # 原文＝翻訳
                    continue

                # dict_var.append(r'((?:^|(?:[^a-zA-Z\p{S}\-_:;\.\,\/\% ])) *)(' + re.escape(dict_var[0]) + r')( *(?:$|(?:[^a-zA-Z\p{S}\-_:;\.\,\/\% ])))')
                dict_var.append(r'(\b)(' + re.escape(dict_var[0]) + r')(\b)')
                dict_var.append(r'\1' + dict_var[1] + r'\3')
                dict_var.append(r'i')

                if matched == 'dnd':
                    tmp_dnd.append(dict_var)
                else:
                    tmp_event_all.append(dict_var)

        # 長さ順でソート
        tmp_dnd = sorted(tmp_dnd, key=lambda x: len(x[0]), reverse=True)
        tmp_event_all = sorted(tmp_event_all, key=lambda x: len(x[0]), reverse=True)

        # 辞書テンプレートを外部ファイルに書き出し
        dict_dir = os.path.join(output_dir, 'dict_template')
        os.makedirs(dict_dir, exist_ok=True)

        output_dnd = ['\t'.join(line) for line in tmp_dnd]
        output_dnd = list(dict.fromkeys(output_dnd)) # 重複行を削除
        if len(output_dnd) > 0:
            path_dnd = os.path.join(dict_dir, 'dict_dnd.dict')
            with open(path_dnd, 'w+', encoding='utf_8_sig') as f:
                f.write('\n'.join(output_dnd))

        output_ev = ['\t'.join(line) for line in tmp_event_all]
        output_ev = list(dict.fromkeys(output_ev)) # 重複行を削除
        if len(output_ev) > 0:
            path_ev = os.path.join(dict_dir, 'dict_misc.dict')
            with open(path_ev, 'w+', encoding='utf_8_sig') as f:
                f.write('\n'.join(output_ev))

        return


    def _sub(self, paratranz_zip_path): # その他のファイルをバックアップ

        with zipfile.ZipFile(paratranz_zip_path) as zip_file:

            paths = [glossary_path, table_of_contents_path]

            # ParaTranzの元ファイルをバックアップ

            for source_path in paths:
                zip_lines = zip_file.read(source_path).decode('utf-8-sig')

                old_path = os.path.join(generated_dir, os.path.split(source_path)[1])
                old_lines = ''
                if os.path.exists(old_path):
                    with open(old_path, 'r', encoding='utf_8_sig') as f:
                        old_lines = f.read()
                set_translation_count(old_lines, zip_lines)

                output_path = os.path.join(output_dir, os.path.split(source_path)[1])
                os.makedirs(os.path.split(output_path)[0], exist_ok=True)
                with open(output_path, 'w', encoding='utf_8_sig') as f:
                    lines = zip_lines
                    f.write(lines)

        return


class namedict(): # DnDアクション、イベント名の辞書

    def load_from_path(self, path): # ファイル内容をリストに変換して返す
        result = []

        if os.path.exists(path):
            with open(path, 'r', encoding='utf_8_sig') as f:
                lines = f.read().splitlines(False)

                # 書式 - 原文\t訳文\t原文（正規表現パターン有）\t訳文（正規表現パターン有）\t小/大文字の区別フラグ
                # 用例 - SOURCE    翻訳    ( ?)SOURCE() ?)    \1翻訳\2    i
                for idx, line in enumerate(lines):
                    dict_var = re.split(r'\t', line)

                    if len(dict_var) < 1:
                        continue
                    if dict_var[0] == dict_var[1]:
                        continue

                    re_flags = 0
                    if len(dict_var) >= 5 and 'i' in dict_var[4]:
                        re_flags = re.IGNORECASE # 大文字・小文字の区別を無効にする

                    if len(dict_var) >= 3: # 正規表現パターンが存在する場合はコンパイル
                        try:
                            dict_var[2] = regex.compile(dict_var[2], flags=re_flags)
                        except:
                            print('ERROR! {0} {1}: "{2}" failed to compile. The regular expression pattern is incorrect.'.format(path, idx, dict_var[2]))
                            continue
                    result.append(dict_var)
        else:
            return False

        result = sorted(result, key=lambda x: len(x[0]), reverse=True) # 原文の長さで降順ソート

        return result

    def create_vars(self): # ファイルからグローバルリストに代入
        global dict_dnd
        global dict_misc

        dict_dnd = namedict().load_from_path(dict_dnd_path)
        dict_misc = namedict().load_from_path(dict_misc_all_path)

        if dict_dnd == False or dict_misc == False:
            print('No dictionary files were found.')
            return False

        return True

    def replace_by_dict(self, m, tr_dict): # グローバルリストから置換

        if not tr_dict:
            return m

        for tr in tr_dict:

            re_flags = 0
            if len(tr) >= 5 and 'i' in tr[4]:
                re_flags = re.IGNORECASE # 大文字・小文字の区別を無効にする

            if len(tr) >= 2:

                m = m.replace('\u00a0', ' ')

                if len(tr) >= 4:
                    re_m = tr[2].sub(tr[3], m) # パターンが存在する場合は正規表現置換
                else:
                    re_m = m.replace(tr[0], tr[1]) # 単純置換

                if '{CTR_S}' in re_m: # 対訳置換
                    re_m = regex.sub(r'{CTR_S} *' + tr[0], ' ' + tr[1] + ' (' + tr[0] + ')', m, flags=re_flags)

                if m != re_m:
                    m = re_m
                    break

        return m


def read_glossary(paratranz_zip_path): # 用語集のファイル内容をリストに代入
    global glossary

    lines = ''
    with zipfile.ZipFile(paratranz_zip_path) as zip_file:
        lines = zip_file.read(glossary_path).decode('utf-8-sig')

    lines = comma_replacer.sub(r'\t', lines)
    lines = re.sub(r'_(Name|Desc)\t', r'\t\1\t', lines)
    l_lines = lines.splitlines(False)

    l_line = [''] * 5

    for m in l_lines:

        separated = re.split(r'\t', m)

        if len(separated) <= 2: # 項目が不足している場合はスキップ
            continue
        elif len(separated) <= 3: # 翻訳がない場合は原文＝訳文にする
            source = separated[2]
            translation = separated[2]
        else:
            source = separated[2]
            translation = separated[3]

        if separated[1] == 'Name':
            l_line[0] = 'TITLE_KEY::' + separated[0]
            l_line[1] = source.strip('"')
            l_line[2] = translation.strip('"')
        else:
            l_line[3] = source.strip('"')
            l_line[4] = translation.strip('"')
            glossary.append(l_line)
            l_line = [''] * 5

    return

def extract_exist_topics(): # 既存のトピック名を辞書に代入
    global index_exist_name
    global index_exist_name_full

    lines = ''

    index_path = os.path.join(template_db_dir, 'whxdata', './idata1.new.js')

    with open(index_path, 'r', encoding='utf_8_sig') as f:
        lines = f.read()

    data = ''
    for line in lines.splitlines(False):
        if line.startswith('var index =  {'):
            data = line
            break

    data_s = re.split(r'({"name":"[^"]+)("[^\[]+)("topics":\[[^\]]+\],)("keys":\[\]},?)', data)

    # key_tree
    for entry in data_s:
        name_key = '{"name":"'

        if entry.startswith(name_key):
            topic_key = entry[len(name_key):].upper()
            index_exist_name[topic_key] = True
            index_exist_name_full[topic_key] = True

        elif entry.startswith('"topics":['):

            topics = re.split(r'(' + name_key + r'[^"]+)("[^}]+)', entry)
            for topic in topics:

                if topic.startswith(name_key):
                    topic_key = topic[len(name_key):].upper()
                    index_exist_name[topic_key] = True
                    index_exist_name_full[topic_key] = True
    return


class whx(): # whxdataディレクトリ以下にあるファイルの処理
    def __init__(self):
        self.db_base_dir = os.path.join(template_db_dir, 'whxdata')
        self.db_dest_dir = os.path.join(output_dir, output_manual_dirname, doc_dir, 'whxdata')
        self.db_dest_ex_dir = os.path.join(output_ex_dir, output_manual_dirname, doc_dir, 'whxdata')
        os.makedirs(self.db_dest_dir, exist_ok=True)
        if ENABLE_FULL_TRANSLATION:
            os.makedirs(self.db_dest_ex_dir, exist_ok=True)

        self.isJp = regex.compile(r'([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])')
        self.isEn = regex.compile(r'^[A-Za-z0-9\!-\/:-@\[-\^\{-\~_ ©]+$')
        self.isSymbol = regex.compile(r'^[\!-\*\.\,\/:-@\[-\^\{-\~\p{InCJKSymbolsAndPunctuation}]+$')
        self.isSymbolEx = regex.compile(r'^[\+\-_]+$')
        self.isHiragana = regex.compile(r'^[\p{Hiragana}]+$')

        self.search_dict = {}
        self.search_fulltr_dict = {}
        self.js_dict = {}
        self.t = Tokenizer()

    def translate_from_file(self, source_path, dest_path, separate_pat, keys, *tr_dict): # ファイルを翻訳して出力

        with open(source_path, 'r', encoding='utf_8_sig') as f:
            lines = f.read()
        separated = re.split(separate_pat, lines)
        new_lines = []

        if len(keys) != len(tr_dict):
            return

        tr_dict = list(tr_dict)

        no_punctuations = re.compile(r'([ \,\.\\])')
        for idx in range(len(tr_dict)):
            tr_dict[idx] = {no_punctuations.sub('', x) : tr_dict[idx].get(x) for x in tr_dict[idx]}

        for m in separated:

            for idx, key in enumerate(keys):

                if m.startswith(key):
                    m = m.replace(key, '')
                    m_dictkey = no_punctuations.sub('', m)

                    if tr_dict[idx].get(m_dictkey):
                        m = tr_dict[idx].get(m_dictkey)
                    m = key + m 

            new_lines.append(m)

        with open(dest_path, 'w', encoding='utf_8_sig') as f:
            f.write(''.join(new_lines))
        print('The db file file "{0}" has been successfully translated.'.format(dest_path))


    def merge_indexdata(self, dest_path, data):
        data_line = ''

        for key in data:
            data_line += ',{"name":"' + key + '","type":"key","topics":[{"name":"' + key + '","type":"topic","url":"' + data.get(key) + '"}],"keys":[]}'


        with open(dest_path, 'r', encoding='utf_8_sig') as f:
            lines = f.read()

        new_lines = []

        for line in lines.splitlines(False):
            if line.startswith('var index =  {'):
                end_part = re.split(r'(,"keys":\[\]})(\]};$)', line)
                if len(end_part) > 2:
                    end_part[1] = end_part[1] + data_line
                line = ''.join(end_part)
            new_lines.append(line)

        with open(dest_path, 'w', encoding='utf_8_sig') as f:
            f.write('\n'.join(new_lines))

    
    def translate_glossary(self):
        # 用語集を翻訳
        separate_pat = r'({[^}]+)("name":"[^"]+)(",)("value":"[^"]+)("},*)'
        keys = ['"name":"', '"value":"']
        whx_filename = 'gdata1.new.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dest_path = os.path.join(self.db_dest_dir, whx_filename)

        self.translate_from_file(source_path, dest_path, separate_pat, keys, {x[1]:x[2] for x in glossary}, {x[3]:x[4] for x in glossary})

    def translate_search_result(self):
        # 検索結果を翻訳
        separate_pat = r'([^\}]+{\\)("title\\":\\"[^"]+)(\\",\\)("summary\\":\\"[^"]+)(\\"[^\}]+\})'
        keys = ['"title\\":\\"', '"summary\\":\\"']
        whx_filename = 'search_topics.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dest_path = os.path.join(self.db_dest_dir, whx_filename)

        self.translate_from_file(source_path, dest_path, separate_pat, keys, {x[0]:x[1] for x in search_keywords}, {x[0]:x[1] for x in search_results})
        
        if ENABLE_FULL_TRANSLATION:
            dest_path = os.path.join(self.db_dest_ex_dir, whx_filename)
            self.translate_from_file(source_path, dest_path, separate_pat, keys, {x[0]:x[1] for x in search_keywords_full}, {x[0]:x[1] for x in search_results_full})

    def translate_index(self):
        # 索引を翻訳
        separate_pat = r'([^{]+{)("name":"[^"]+)'
        keys = ['"name":"']
        whx_filename = 'idata1.new.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dest_path = os.path.join(self.db_dest_dir, whx_filename)

        topic_index.extend(search_keywords) # 検索結果のキーワードも含める
        self.translate_from_file(source_path, dest_path, separate_pat, keys, {x[0]:x[1] for x in topic_index})
        if ENABLE_EXTRA_INDEX:
            self.merge_indexdata(dest_path, index_data)
        
        if ENABLE_FULL_TRANSLATION:
            dest_path = os.path.join(self.db_dest_ex_dir, whx_filename)
            topic_index_full.extend(search_keywords_full) # 検索結果のキーワードも含める
            self.translate_from_file(source_path, dest_path, separate_pat, keys, {x[0]:x[1] for x in topic_index_full})
            if ENABLE_EXTRA_INDEX:
                self.merge_indexdata(dest_path, index_data_full)


    def translate_table_of_contents(self, out_file_path):
        # 左メニューを翻訳
        with zipfile.ZipFile(out_file_path) as zip_file:
            lines = zip_file.read(table_of_contents_path).decode('utf-8-sig')

        # csvファイルから変換用の辞書を作成
        lines = comma_replacer.sub(r'\t', lines)

        names = {}
        names_with_idx = []
        for line in lines.splitlines(False):
            separated = re.split(r'\t', line)
            separated = [s.strip('"') for s in separated]

            if len(separated) < 3: # 翻訳がないためスキップ
                continue

            loc_idx = re.sub(r'.*:([0-9]+).*', r'\1', separated[0])
            if loc_idx != separated[0]:
                names_with_idx.append([loc_idx, separated[1], separated[2]])
            else:
                names[separated[1]] = separated[2]

        # jsファイルを辞書で置換
        file_paths = [file for file in os.listdir(self.db_base_dir) if os.path.isfile(os.path.join(self.db_base_dir, file)) and re.search(r'toc[0-9]*\.new\.js', file)]

        for idx, file in enumerate(file_paths):
            f_path = os.path.join(self.db_base_dir, file)
            with open(f_path, "r", encoding="utf_8_sig", newline="\n") as f:
                separated = re.split(r'("name":"[^"]+)', f.read())

            loc_idx = re.sub(r'.*toc([0-9]+)\.new\.js', r'\1', f_path)

            key_name = '"name":"'
            lines = []
            lines_full_tr = []

            n_dict = namedict()

            for m in separated:
                m_full = m

                if m.startswith(key_name):
                    table_name = m.replace(key_name, '')

                    for n in names_with_idx:
                        if loc_idx == n[0] and n[1] == table_name:
                            table_name = n[2]
                            break
                    else:
                        if names.get(table_name):
                            table_name = names.get(table_name)

                    m = key_name + table_name

                    table_name_full = n_dict.replace_by_dict(table_name, dict_dnd)
                    table_name_full = n_dict.replace_by_dict(table_name_full, dict_misc)
                    m_full = key_name + table_name_full

                lines.append(m)
                lines_full_tr.append(m_full)

            f_destpath = os.path.join(self.db_dest_dir, file)
            with open(f_destpath, "w", encoding="utf_8_sig", newline="\n") as f:
                f.write(''.join(lines))

            if ENABLE_FULL_TRANSLATION:
                f_destpath = os.path.join(self.db_dest_ex_dir, file)
                with open(f_destpath, "w", encoding="utf_8_sig", newline="\n") as f:
                    f.write(''.join(lines_full_tr))


    def separate_by_janome(self, lines):
        p_noun = ['名詞,']
        p_ignore = ['名詞,代名詞'] # 無視する品詞
        p_ignore_single = ['形容詞', '助詞,連体化'] #単体NG（直前・直後が名詞ならOK）
        p_ignore_single_hiragana = ['名詞,非自立', '名詞,代名詞', '名詞,副詞可能', '名詞,形容動詞語幹', '名詞,接尾', '名詞,副詞可能', '名詞,動詞非自立的'] #ひらがなの場合は単体NG
        p_strip = ['名詞,非自立', '助詞,連体化', '形容詞,非自立'] # 前後を取る
        p_allowed = ['名詞', '記号,空白', '記号,連体化', '助詞,連体化', '形容詞'] # 許可する品詞
        p_separate = ['助詞,連体化', '記号', '形容詞'] # 区切りとなる品詞

        result = []

        lines = re.sub(r'^ *{[^\}]+\}.*', r'', lines, flags=re.MULTILINE) # htmlの外で使われるテキストは除外
        lines = re.sub(r'\{[^\}]+\}', r'', lines) # ダミータグは除外
        lines = re.sub(r'<img alt=[^>]+>', r'', lines) # IMG_TXTは除外

        # 見出し（タグ区切りのテキスト）を辞書に追加
        for line in lines.splitlines(False):
            patterns = [
            re.compile(r'(^[ "]*<strong>)([^<\,\./\\"]{2,})(</strong>).*'), 
            re.compile(r'(^[ "]*<tt>)([^<\,\./\\"]{2,})(</tt>).*'),
            re.compile(r'(^.*<span data-open-text="+true"+>)([^<\,\./\\"]{2,})(</span>).*')
            ]

            for pat in patterns: # 特定のタグから始まる行を分割
                output = pat.sub(r'\2', line)
                if output and output != line and self.isJp.match(output):
                    result.append(output.strip(' "'))
                    break

        lines = re.sub(r'<[^>]+>', r'', lines) # タグを削除
        lines = lines.replace('\u200b', ' ') # ノーブレークスペースは半角スペースに
        lines = re.sub('  *', ' ', lines)

        # 形態素解析による行ごとのキーワード抽出
        for line in lines.splitlines(False):
            surfaces = []
            parts = []

            line += '。' # 末尾に区切り文字を残す

            tokens = [[token.surface, token.part_of_speech] for token in self.t.tokenize(line)]

            for idx, token in enumerate(tokens):

                if self.isSymbol.match(token[0]):
                    token[1] = '記号,その他,*,*'
                elif self.isSymbolEx.match(token[0]):
                    token[1] = '記号,連体化,*,*'

                if all(not token[1].startswith(pat) for pat in p_allowed) or any(token[1].startswith(pat) for pat in p_ignore):
                    SKIP = False

                    # パターン精査
                    while len(parts) > 0 and any(parts[-1].startswith(pat) for pat in p_strip):
                        parts.pop(-1)
                        surfaces.pop(-1)

                    while len(parts) > 0 and any(parts[0].startswith(pat) for pat in p_strip):
                        parts.pop(0)
                        surfaces.pop(0)

                    output = ''.join(surfaces)
                    output = output.rstrip('-')
                    output = output.strip(' "')

                    if len(parts) == 1 and any(parts[0].startswith(pat) for pat in p_ignore_single):
                        SKIP = True

                    if len(parts) == 1 and self.isHiragana.match(output) and any(parts[0].startswith(pat) for pat in p_ignore_single_hiragana):
                        SKIP = True

                    if len(output) <= 1:
                        SKIP = True

                    # キーワードの辞書への追加
                    if SKIP == False:
                        # 全文を追加
                        result.append(output)

                        # 区切り文字で分解し、それぞれのパーツを追加
                        s_output = []
                        for i in range(len(parts)):
                            if any(parts[i].startswith(pat) for pat in p_separate):

                                s = ''.join(s_output).strip(' "')
                                if s:
                                    result.append(s)
                                s_output = []
                            else:
                                s_output.append(surfaces[i])
                                s = surfaces[i].strip(' "')
                                if s and not self.isHiragana.match(surfaces[i]) and any(parts[i].startswith(pat) for pat in p_noun):
                                    result.append(s) # 名詞を単体で抽出
                        else:
                            if len(s_output) > 1: # ループの余りを追加
                                s = ''.join(s_output)
                                if s:
                                    result.append(''.join(s_output))

                        # スペースで分割
                        for s in output.split():
                            if s and not s in result:

                                if s != ''.join(self.separate_by_janome(s)):
                                    result.append('{_SPLIT_BY_SPACE}' + s) # '～の'などで終わっているキーワードは入力候補に出ないようにする
                                else:
                                    result.append(s)

                    surfaces = []
                    parts = []
                    continue

                surfaces.append(token[0])
                parts.append(token[1])

        return result

    def extract_search_keyword(self, lines):

        result = []
        title = ''

        new_lines = []

        # 翻訳のみ抽出＆ページタイトルを辞書に追加

        lines = re.sub(r'^"location","source","target"(,"")?[\r\n]+', '', lines)

        for line in lines.splitlines(False):
            line = comma_replacer.sub(r'\t', line)
            s = re.split(r'\t', line)

            if len(s) >= 3:
                tr = s[2].strip(' "')
                new_lines.append(tr)

                if 'head.title' in s[0] and not self.isEn.match(tr):
                    title = tr
        else:
            if len(new_lines) == 0: # 翻訳がないためスキップ
                return None

        lines = '\n'.join(new_lines)


        ####################################################################

        # janomeによるキーワード抽出
        result.append(self.separate_by_janome(title))
        if title and not title in result[0]:
            result[0].insert(0, title)

        result.append(self.separate_by_janome(lines))

        result[0] = sorted(set(result[0]), key=result[0].index) # title
        result[1] = sorted(set(result[1]), key=result[1].index) # body

        return result


    def mapping_js_by_topics(self): # {js名 : htmファイル名} の対応辞書を作成
        whx_path = os.path.join(self.db_base_dir, 'search_topics.js')

        result = {}

        with open(whx_path, "r", encoding="utf_8_sig") as f:
            lines = f.read()

        for m in re.finditer(r'[^\}]+\\"([0-9]+)\\":\{[^\}]+"relUrl\\":\\"([^"]+)\\",\\"[^\}]+\}', lines, re.MULTILINE):
            path = m.group(2).replace('.htm', '')
            self.js_dict[m.group(1)] = path

        return result


    def write_text_js(self, dic, data, files, dest_dir_path): # text/jsファイル群に書き込み
        source_dir_path = os.path.join(self.db_base_dir, 'text')
        os.makedirs(dest_dir_path, exist_ok=True)

        for current, subfolders, subfiles in os.walk(source_dir_path):
            for file in subfiles:
                source_path = os.path.join(current, file)
                dest_path = dest_dir_path + source_path.replace(source_dir_path, '')

                with open(source_path, "r", encoding="utf_8_sig") as f:
                    lines = f.read()

                separated = re.split(r'([,\]]*"[0-9]":\[)', lines)
                cat_pos = [-1, -1]

                for idx, s in enumerate(separated):
                    if s.startswith('"0":['):
                        cat_pos[0] = idx + 1 # タイトル
                    elif s.startswith('],"3":['):
                        cat_pos[1] = idx + 1 # 本文
                        break
                else:
                    continue


                js_name = os.path.splitext(os.path.split(file)[1])[0]
                f_path = self.js_dict.get(js_name)

                for idx, file in enumerate(files):
                    if file == f_path:

                        for cat, pos in enumerate(cat_pos):
                            if len(data[cat][idx]) > 0:
                                text = separated[pos].split('","')
                                text[-1] = text[-1].rstrip('"')

                                # 日本語テキストを挿入する開始位置を算出
                                text_for_len = '{_SEPARATOR}'.join(text)
                                text_for_len = re.sub(r'^(?:((\\n)|[" ])*{_SEPARATOR})+(.*)', r'\3', text_for_len) # 本文が始まる前の改行コードは計測されないため削除
                                text_for_len = text_for_len.replace('\\\\', ' ') # 二重エスケープは一字
                                text_for_len = text_for_len.replace('\\', '') # エスケープ文字は計測されないため削除
                                text_for_len = text_for_len.replace('{_SEPARATOR}', ' ')
                                text_for_len = text_for_len.lstrip('"')

                                current_pos = len(text_for_len) + 1 # 日本語テキストを挿入する開始位置

                                # 辞書からデータを取り出し
                                for d in data[cat][idx]:
                                    d = d.replace('\\', '')

                                    no_automap = False
                                    if '{_SPLIT_BY_SPACE}' in d: # 入力候補から除外するキーワード
                                        d = d.replace(r'{_SPLIT_BY_SPACE}', r'')
                                        no_automap = True

                                    d_body = d.replace(r'"', r'\"')

                                    if d_body[0] == '\\':
                                        continue
                                    if self.isEn.match(d_body):
                                        continue

                                    self.append_search_db(dic, d_body, d_body[0], str(len(d)), js_name, str(current_pos), str(cat), no_automap) # キーワードと関連情報をDB辞書にコピー
                                    text.append(d_body)

                                    if ' ' in d: # スペース抜きのキーワードを生成（'x 位置'→'x位置'など）
                                        d_ns = re.sub(r'(([^A-Za-z0-9\!-\/:-@\[-`\{-~ ©]) +| +([^A-Za-z0-9\!-\/:-@\[-`\{-~ ©]))', r'\2\3', d)
                                        d_ns_body = d_ns.replace(r'"', r'\"')
                                        # ハイライトを有効にするため、位置情報はスペース入りのキーワードと同一にする
                                        self.append_search_db(dic, d_ns_body, d_body[0], str(len(d)), js_name, str(current_pos), str(cat), no_automap)
                                        text.append(d_ns_body)
                                        current_pos += (1 + len(d_ns))

                                    current_pos += (1 + len(d))

                                separated[pos] = '","'.join(text) + '"'
                        break
                else:
                    continue

                output = ''.join(separated)

                with open(dest_path, 'w+', encoding='utf_8_sig') as f:
                    f.write(output)


    def append_search_db(self, dic, keyword, initial, length, js, pos, cat, no_automap=False):
        # {'keyword' : {'initial' : str, 'length' : 0-9+, 'js' : 1:2:3:4:5:6:7, 'pos' : js:pos:cat,js:pos:cat'}} # text/jsからの参照位置

        keyword = keyword.lower()
        initial = initial.lower()
        if no_automap:
            text_js = '"-1"'
        else:
            text_js = '"' + js +'"'
        pos_js = '"' + js +'"'

        if dic.get(keyword): # 既存のキーワードにjsとposを追加
            dic[keyword]['js'] += ',' + text_js
            dic[keyword]['pos'] += ',' + ':'.join([pos_js, pos, cat])
        else:
            dic[keyword] = {'initial' : initial, 'length' : length, 'js' : text_js, 'pos' : ':'.join([pos_js, pos, cat])}
        return


    def write_search_automap(self, dic, dir_path):
        whx_filename = 'search_auto_map_0.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dest_path = os.path.join(dir_path, whx_filename)

        edges = ['rh._.exports({', '})']

        with open(source_path, "r", encoding="utf_8_sig") as f:
            lines = f.read()
        lines = lines[len(edges[0]):-(len(edges[1]))]
        lines = re.sub(r'(\],|{)("[^"]+":)', r'\1{_SPLIT}\2', lines)

        separated = [m.rstrip(',)}') for m in lines.split(r'{_SPLIT}')]
        initials = [s[1] for s in separated]

        idxs = re.findall(r'\["[^\]]+",([0-9]+)', lines)
        current_idx = 1 + int(natsorted(idxs)[-1])

        for d in dic:
            idx = -1

            js_name = dic[d].get('js')

            if ' ' in d or '-1' in js_name:
                continue
            
            NOTFOUND = False
            try:
                idx = initials.index(dic[d].get('initial'))
            except:
                NOTFOUND = True
                separated.append('')
                initials.append(dic[d].get('initial')) # 存在しなければ親エントリ（イニシャル）を作成

            s = separated[idx][6:-2].split('],[')
            # "keyword",index,1,0,index,[js_files]'
            s.append('"{0}",{1},1,0,{1},[{2}]'.format(d.lower(), current_idx, js_name))
            current_idx += 1

            if NOTFOUND:
                separated[idx] = '"{0}":[[{1}]]'.format(initials[idx], ''.join(s))
            else:
                separated[idx] = '"{0}":[[{1}]]'.format(initials[idx], '],['.join(s))

        lines = edges[0] + ','.join(separated) + edges[1]
        with open(dest_path, 'w', encoding='utf_8_sig') as f:
            f.write(lines)

        return


    def write_search_db(self, dic, dir_path):
        whx_filename = 'search_db.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dest_path = os.path.join(dir_path, whx_filename)

        with open(source_path, "r", encoding="utf_8_sig") as f:
            lines = f.read()

        lines = re.sub(r'("_index":[0-9]+\}\],?)', r'\1{_SPLIT}', lines)
        separated = [m for m in lines.split(r'{_SPLIT}')]

        idxs = re.findall(r'"_index":([0-9]+)', lines)
        current_idx = 1 + int(natsorted(idxs)[-1]) # indexの開始位置を取得
        
        edges = [separated.pop(0), separated.pop(-1)]
        separated[-1] += ','

        for d in dic:
            body_pos = []
            title_pos = []
            for p in dic[d].get('pos').split(','):
                p_data = p.split(':')

                var = '{0}:{{"position":[[{1},{2}]]}}'.format(p_data[0], p_data[1], dic[d].get('length'))

                if p_data[2] == "0":
                    title_pos.append(var)
                else:
                    body_pos.append(var)

            entry = '["{0}",{{"0":{{{1}}},"1":{{}},"2":{{}},"3":{{{2}}},"4":{{}},"5":{{}},"6":{{}},"7":{{}},"8":{{}},"_index":{3}}}],'.format(d, ','.join(title_pos), ','.join(body_pos), current_idx)
            separated.append(entry)
            current_idx += 1

        # RoboHelpのソート順に合わせる
        separated = [m.replace(r'\"', r'"{_C_QUOTE}') for m in separated] # 半角スペース（および'!'）が入るとズレるためダミー文字に変換
        separated = [m.replace(r' ', r'"{_A_SPACE}') for m in separated] # 半角スペース（および'!'）が入るとズレるためダミー文字に変換
        separated = [m.replace(r'!', r'"{_B_EXCL}') for m in separated]
        separated.sort()
        separated = [m.replace(r'"{_C_QUOTE}', r'\"') for m in separated]
        separated = [m.replace(r'"{_A_SPACE}', r' ') for m in separated]
        separated = [m.replace(r'"{_B_EXCL}', r'!') for m in separated]

        separated[-1] = separated[-1].rstrip(',')
        separated.insert(0, edges[0])
        separated.append(edges[-1])

        lines = ''.join(separated)

        with open(dest_path, 'w', encoding='utf_8_sig') as f:
            f.write(lines)

        return

    def write_search_files(self):
        doc_dir = os.path.join(output_dir, output_manual_dirname, 'cnv_csv')
        ex_dir = os.path.join(output_ex_dir, output_manual_dirname,  'cnv_csv')
        js_body = [[''], ['']]
        js_title = [[''], ['']]
        files = [[''], ['']]

        for current, subfolders, subfiles in os.walk(doc_dir):
            for file in subfiles:

                f_path = os.path.join(current, file)

                real_path = f_path.replace(doc_dir, '')
                real_path = real_path[1:]
                real_path = real_path.replace('\\', '/')
                real_path = real_path.replace('／', '/') # 置き換えられたファイル名の'／'をパスとしての'/'に復元
                real_path = re.sub(r'GML_Reference/[A-Z]-[A-Z]/', r'GML_Reference/', real_path) # GMLリファレンスの細分化した一時ディレクトリをパスから取り除く
                real_path = real_path.replace('.csv', '')

                f_ex_path = os.path.join(current.replace(doc_dir, ex_dir), file)

                with open(f_path, "r", encoding="utf_8_sig") as f:
                    lines = f.read()

                keywords = self.extract_search_keyword(lines)

                if keywords == None: # 翻訳がない
                    continue

                title = [k for k in keywords[0]]
                entry = [k for k in keywords[1]]
                js_title[0].append(title)
                js_body[0].append(entry)
                files[0].append(real_path)

                if ENABLE_FULL_TRANSLATION:
                    js_title[1].append(title)
                    js_body[1].append(entry)
                    files[1].append(real_path)

                    if os.path.exists(f_ex_path):
                        with open(f_ex_path, "r", encoding="utf_8_sig") as f:
                            lines_ex = f.read()

                        if lines_ex and lines_ex != lines:
                            keywords = self.extract_search_keyword(lines_ex)

                            js_title[1][-1] = [k for k in keywords[0]]
                            js_body[1][-1] = [k for k in keywords[1]]
        del js_body[1][0]
        del js_title[1][0]
        del files[1][0]

        del js_body[0][0]
        del js_title[0][0]
        del files[0][0]

        self.mapping_js_by_topics()
        
        self.write_text_js(self.search_dict, [js_title[0], js_body[0]], files[0], os.path.join(self.db_dest_dir, 'text'))
        if ENABLE_FULL_TRANSLATION:
            self.write_text_js(self.search_fulltr_dict, [js_title[1], js_body[1]], files[1], os.path.join(self.db_dest_ex_dir, 'text'))

        self.write_search_automap(self.search_dict, self.db_dest_dir)
        self.write_search_db(self.search_dict, self.db_dest_dir)
        if ENABLE_FULL_TRANSLATION:
            self.write_search_automap(self.search_fulltr_dict, self.db_dest_ex_dir)
            self.write_search_db(self.search_fulltr_dict, self.db_dest_ex_dir)

        return


##############################################################################################


def check_for_changes():

    # IDEの変更確認
    ide_old_path = os.path.join(generated_dir, os.path.split(ide_path[0])[1])
    ide_bak_path = os.path.join(output_dir, os.path.split(ide_path[0])[1])

    if not os.path.exists(ide_old_path):
        return True
    else:
        with open(ide_old_path, 'rb') as f:
            ide_old_lines = f.read()

        with open(ide_bak_path, 'rb') as f:
            ide_bak_lines = f.read()

        if ide_old_lines != ide_bak_lines:
            return True

    # マニュアルの変更確認
    converted_dir = os.path.join(output_dir, output_manual_dirname, doc_dir)
    
    source_dict = {}
    dest_dict = {}

    for current, subfolders, subfiles in os.walk(doc_dir):
        for file in subfiles:

            f_path = os.path.join(current, file)

            if not f_path.endswith('.htm') and not f_path.endswith('.js'):
                continue

            with open(f_path, "r", encoding="utf_8_sig") as f:
                lines = f.read()
                source_dict[f_path] = lines
    
    for current, subfolders, subfiles in os.walk(converted_dir):
        for file in subfiles:

            f_path = os.path.join(current, file)

            if not f_path.endswith('.htm') and not f_path.endswith('.js'):
                continue

            with open(f_path, "r", encoding="utf_8_sig") as f:
                lines = f.read()
            f_path = re.sub(os.path.join(output_dir, output_manual_dirname) + r'.' + doc_dir, doc_dir, f_path)
            dest_dict[f_path] = lines

    for k in source_dict:
        if dest_dict.get(k) != None and source_dict.get(k) != None:

            if source_dict.get(k) != dest_dict.get(k):
                return True

    return False

def write_update_stats(file_path):
    lines = []
    header = 'time\tlines\ttranslations\tpercentage\tadded_translations\tadded_percentage\tadded_words'

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            lines = f.read().splitlines(False)[1:]

    total_line = translation_info[0]
    total_translation = translation_info[1]
    total_percentage = '{:.3f}'.format((translation_info[1] / translation_info[0]) * 100)
    current_percentage = '{:.3f}'.format((translation_info[2] / translation_info[0]) * 100)
    curent_line = '{:,}'.format(translation_info[2])
    current_word = '{:,}'.format(translation_info[3])

    dt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    current_time = dt.strftime('%Y/%m/%d %H:%M:%S')

    if translation_info[2] > 0:
        line = '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}'.format(current_time, total_line, total_translation, total_percentage, curent_line, current_percentage, current_word)
    else:
        line = '{0}\t{1}\t{2}\t{3}'.format(current_time, total_line, total_translation, total_percentage)

    lines.insert(0, line)
    lines.insert(0, header)

    with open(file_path, "w+") as f:
        f.write('\n'.join(lines))

    return

##############################################################################################


def sub(index_name,
        paratranz_project_code,
        paratranz_secret):
    out_file_path = "tmp/paratranz_%s.zip" % paratranz_project_code

    print("index_name=%s,code=%s" % (index_name, paratranz_project_code))

    if not os.path.exists(out_file_path):
        # paratranzからzipファイルのダウンロード
        out_file_path = download_trans_zip_from_paratranz(project_id=paratranz_project_code,
                                                          secret=paratranz_secret,
                                                          out_file_path=out_file_path)
        print("download data")

    # IDEの言語ファイルをバックアップ + 二次ファイルを生成
    generate_file()._ide(out_file_path)
    # テンプレート辞書を生成
    generate_file()._dict_template(out_file_path)
    # その他の直下にあるファイルをバックアップ
    generate_file()._sub(out_file_path)

    # DnD/イベント名の辞書データを登録
    global ENABLE_FULL_TRANSLATION

    if namedict().create_vars() == False: # 辞書ファイルを読み込みリストを生成
        ENABLE_FULL_TRANSLATION = False # 失敗した場合はイベント名、DnDアクション名を翻訳しない

    # 用語集を読み込み
    read_glossary(out_file_path)

    # 既存のトピック名を辞書に代入
    extract_exist_topics()

    # csvをhtmlに変換
    convert_from_zip(out_file_path)

    # whxdata以下にあるファイルを日本語化
    if EXPORT_WHXDATA:
        whxdata = whx()
        whxdata.translate_glossary()
        whxdata.translate_search_result()
        whxdata.translate_index()
        whxdata.translate_table_of_contents(out_file_path)
        whxdata.write_search_files()

    # 出力ファイルに変更があるかどうかチェック
    if check_for_changes() == False:
        print("NO CHANGES FOUND.")
        return

    # プレビュー版に変更
    if GENERATE_AS_PREVIEW:
        docs_preview.format_pages(os.path.join(output_dir, output_manual_dirname, doc_dir), output_preview_dir, os.environ.get("REPOSITORY_NAME"))

    print("complete")
    commit_file = '_COMMIT_RUN'
    with open(commit_file, "w+") as f:
        f.write(commit_file)

    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    write_update_stats(os.path.join(logs_dir, 'update_stats.csv'))

    return


def main(paratranz_secret):
    # 一時フォルダ用意
    os.makedirs("tmp", exist_ok=True)

    p_code = os.environ.get("PARATRANZ_CODE")
    
    sub(index_name="gms2",
        paratranz_project_code=p_code,
        paratranz_secret=paratranz_secret)


if __name__ == '__main__':
    main(paratranz_secret=os.environ.get("PARATRANZ_SECRET"))
