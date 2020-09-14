import os
import sys
import re
import regex
import urllib.request
import zipfile

from pathlib import Path
from translate.convert.po2html import converthtml
from translate.convert.csv2po import convertcsv

################# 各種設定 ###############

# 日本語と英数字の間に半角スペースを自動で挿入するかどうか
#  0で無効、1でスペースを挿入、2でスペースを削除
Space_Adjustment = 1

# whxdata以下のファイルを翻訳するかどうか
Export_whxdata = True

# IDEおよびマニュアルの二次ファイルを生成するかどうか
#  これらはオーバーライドデータと専用の辞書により、イベント名、DnDアクション名を日本語に置き換えたものです。
#  Github Pagesには影響せず、それぞれ別々のアーカイブ/csvとして出力されます。
Enable_fullTranslation = True
dnd_dirname = 'Drag_And_Drop/Drag_And_Drop_Reference/'

input_dir = 'utf8/csv/' # ParaTranzのCSVディレクトリ
ide_path = 'utf8/english.csv' # ParaTranzのIDE言語ファイル
glossary_path = 'utf8/manual_glossary.csv' # マニュアルの用語集
table_of_contents_path = 'utf8/manual_leftmenu.csv' # 左メニューの翻訳ファイル

template_html_dir = 'repo/tr_sources/source_html/' # GitPagesリポジトリのテンプレートHTML
template_pot_dir = 'repo/tr_sources/source_pot/' # GitPagesリポジトリのテンプレートPOT
template_csv_dir = 'repo/tr_sources/source_csv/' # GitPagesリポジトリのテンプレートCSV
template_db_dir = 'repo/tr_sources/source_db/' # GitPagesリポジトリのテンプレートDBファイル

output_dir = 'Converted/'
output_ex_dir = 'Converted_EX/'
output_manual_dirname = 'manual'

release_dir = 'Release/'
ide_base_name = 'japanese.csv' # IDEの言語ファイル出力名
ide_alt_name = 'japanese_alt.csv' # IDEの二次言語ファイル出力名
ide_overrides_path = 'override/ide_overrides.csv' # IDEのオーバーライドcsv
ide_overrides_alt_path = 'override_extra/ide_overrides.csv' # IDEのオーバーライドcsv

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


dict_dnd = []
dict_misc = []

search_results = []
search_keywords = []
topic_index = []
glossary = []

search_results_full = []
search_keywords_full = []
topic_index_full = []


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


def convert_from_zip(paratranz_zip_path):
    with zipfile.ZipFile(paratranz_zip_path) as zip_file:
        infos = zip_file.infolist() # 各メンバのオブジェクトをリストとして返す

        for info in infos:

            if compiled_raw_csv_file_patter.match(info.filename) is None:
                continue

            exoport_mode = ['']

            if Enable_fullTranslation: # イベント名、DnDアクション名の翻訳が有効となっている場合は再実行する
                if info.filename.find(dnd_dirname) != -1:
                    exoport_mode.append('dnd')
                else:
                    exoport_mode.append('ev')

            for mode in exoport_mode:

                base_path = info.filename.replace(input_dir, '')
                base_path = os.path.splitext(base_path)[0]

                if mode != '':
                    # イベント名、DnDアクション名が翻訳されたファイルは別のディレクトリに出力
                    dist_dir = os.path.join(output_ex_dir, output_manual_dirname)
                else:
                    dist_dir = os.path.join(output_dir, output_manual_dirname)

                # ParaTranzのバックアップ用CSVファイルを出力
                path_csv = os.path.join(dist_dir, 'csv', base_path) + '.csv'

                os.makedirs(os.path.split(path_csv)[0], exist_ok=True)
                with open(path_csv, 'wb') as f:
                    f.write(zip_file.read(info.filename))

                # 基本パスを復元
                try:
                    encoded_path = base_path.encode('cp437').decode('cp932')
                except UnicodeEncodeError:
                    encoded_path = base_path
                base_path = encoded_path

                base_path = base_path.replace('／', chr(47)) # 置き換えられたファイル名の'／'をパスとしての'/'に復元
                base_path = re.sub(r'GML_Reference/[A-Z]-[A-Z]/', r'GML_Reference/', base_path) # GMLリファレンスの細分化した一時ディレクトリをパスから取り除く

                path_source_csv = os.path.join(template_csv_dir, base_path) + '.csv'
                path_cnv_csv = os.path.join(dist_dir, 'csv_cnv', base_path) + '.csv'

                format_l = format_lines(mode)

                # 整形前のCSVファイルを出力
                with open(path_source_csv, 'r', encoding='utf_8_sig', newline='\n') as f:
                    source_lines = f.read()
                with open(path_csv, 'r', encoding='utf_8_sig', newline='\n') as f:
                    translated_lines = f.read()

                csv_lines = format_l.restore_csv_commentout(source_lines, translated_lines) # コメントアウトしたCSV行を復元

                with open(path_csv, 'w+', encoding='utf_8_sig', newline='\n') as f:
                    f.write(csv_lines)


                # 整形したCSVファイルを出力
                csv_lines = format_l._csv(csv_lines, base_path)

                os.makedirs(os.path.split(path_cnv_csv)[0], exist_ok=True)
                with open(path_cnv_csv, 'w+', encoding='utf_8_sig', newline='\n') as f_input:
                    f_input.write(csv_lines)


                # CSVファイルをPOファイルに変換
                path_po = os.path.join(dist_dir, 'po_cnv', base_path) + '.po'
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
                with open(path_po, 'r', encoding='utf_8_sig', newline='\n') as f_po:
                    po_lines = f_po.read()

                po_lines = format_l._po(po_lines)

                with open(path_po, 'w+', encoding='utf_8_sig', newline='\n') as f_po:
                    f_po.write(po_lines)
                

                # HTMLへの変換を開始
                path_output = os.path.join(dist_dir, 'docs', base_path) + '.htm'
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
                line = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', line)
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
        if translation.find(finder) == -1: # 翻訳が存在しない
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
    
    
        ## 一行ごとの処理 ##
        lines = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', lines)
        new_lines = []
    
        for line in lines.splitlines(False):
            separated = re.split(r'\t', line)
    
            SKIP = False
    
            if len(separated) < 3: # 翻訳がないため何もしない
                SKIP = True
            elif '{ANY_CODE}' in separated[2]: # コード行には何もしない
                SKIP = True
    
            if SKIP == False:
                tr = separated[2] # 翻訳行
        
                # 日本語/英数字、および<b>, <a href>タグの間に半角スペースを挿入・削除
                if Space_Adjustment == 1: # 半角スペースを挿入する場合
                    tr = insert_pat[0].sub(r'\1 \2\4\5', tr)
                    tr = insert_pat[1].sub(r'\1\3\4 \6', tr)
                    tr = insert_pat[2].sub(r'\1 \2\4\5', tr)
                    tr = insert_pat[3].sub(r'\1\3\4 \6', tr)
                    tr = insert_pat[4].sub(r'\1 \2\4\6', tr)
                    tr = insert_pat[5].sub(r'\1\4 \6\8', tr)
                    tr = insert_pat[6].sub(r'\1', tr)
                    tr = insert_pat[7].sub(r'\1', tr)
                    tr = insert_pat[8].sub(r'\\n', tr)
        
                elif Space_Adjustment == 2: # 半角スペースを削除する場合
                    tr = remove_pat[0].sub(r'\1\2\4\6', tr)
                    tr = remove_pat[1].sub(r'\1\4\6\8', tr)
        
                # 翻訳行をタグで分離
                notags = re.split(r'((?:<[^>]+>)|(?:\([a-zA-Z0-9 ]+\))|(?:（[a-zA-Z0-9 ]+）)|(?:\[[a-zA-Z0-9 ]+\]))', tr)
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
        
                separated[2] = ''.join(notags_cnv)
        
                # whxdata用の辞書にメタデータ等を代入
                append_list = []

                append_list = self.get_replaced_list(separated[1], separated[2], '"', '{SEARCH_RESULT} ', r'{SEARCH_RESULT} *', '')
                if append_list[0] != '':
                    if self.mode != '':
                        search_results_full.append(append_list)
                    else:
                        search_results.append(append_list)
                
                append_list = self.get_replaced_list(separated[1], separated[2], '"', '{INDEX_KEYWORD} ', r'{INDEX_KEYWORD} *', '')
                if append_list[0] != '':
                    if self.mode != '':
                        search_keywords_full.append(append_list)
                    else:
                        search_keywords.append(append_list)
                
                append_list = self.get_replaced_list(separated[1], separated[2], '"', '"<span data-open-text=""true"">', r'"<span data-open-text=""true"">([^<]+)</span>', r'\1')
                if append_list[0] != '':
                    if self.mode != '':
                        topic_index_full.append(append_list)
                    else:
                        topic_index.append(append_list)
                
                append_list = self.get_replaced_list(separated[1], separated[2], '"', '.head.title:')
                if append_list[0] != '':
                    if self.mode != '':
                        topic_index_full.append(append_list)
                    else:
                        topic_index.append(append_list)

            new_lines.append(','.join(separated))

        lines = '\n'.join(new_lines)
        

        # テンプレートを復元
        if restore_format_key[0] != '':
            lines = restore_format_key[0].sub( '', lines)
            lines = restore_format_key[1] + lines
    
        # キーを復元
        orig_key = 'YoYoStudioRoboHelp'
        if os.path.split(base_path)[0]:
            orig_key = orig_key + chr(47) + os.path.split(base_path)[0]
        orig_key = orig_key.replace(chr(47), chr(92) + chr(92))
        lines = re.sub(r'([^"\r\n]+\.html?\+[^:]+:[0-9]+\-[0-9]+)', orig_key + chr(92) + chr(92) + r'\1', lines)
    
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
        lines = re.sub(r'{CTR_N} ?', '', lines)
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
            line = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', line)
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

            new_lines.append(','.join(s) + ',,')

        new_lines.append('')
        return '\n'.join(new_lines)

    def generate_ide_dict(self, lines):
        result = []
        for d in lines.splitlines(False):
            d = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', d)
            dict_var = re.split(r'\t', d)
            result.append(dict_var)

        return result


    def _ide(self, paratranz_zip_path): # IDEの言語ファイルをバックアップし、さらに二次ファイルを生成

        with zipfile.ZipFile(paratranz_zip_path) as zip_file:

            ide_bak_path = os.path.join(output_dir, os.path.split(ide_path)[1])

            # ParaTranzの元ファイルをバックアップ
            os.makedirs(os.path.split(ide_bak_path)[0], exist_ok=True)
            with open(ide_bak_path, 'wb') as f:
                lines = zip_file.read(ide_path)
                orig_lines = lines.decode('utf-8-sig')
                f.write(lines)

        # GMS2本体の言語ファイルを生成
        os.makedirs(release_dir, exist_ok=True)
        ide_base_output_path = os.path.join(release_dir, ide_base_name)

        if os.path.exists(ide_overrides_path):
            with open(ide_overrides_path, 'r', encoding='utf_8_sig', newline='\n') as f:
                override_lines = f.read()
        else:
            override_lines = ''

        ide_lines = self.format_ide(orig_lines, self.generate_ide_dict(override_lines), False)

        with open(ide_base_output_path, 'w', encoding='utf_8_sig') as f:
            f.write(ide_lines)

        # 二次ファイルを生成
        if Enable_fullTranslation == False or not os.path.exists(ide_overrides_alt_path):
            return

        ide_alt_output_path = os.path.join(release_dir, ide_alt_name)

        with open(ide_overrides_alt_path, 'r', encoding='utf_8_sig', newline='\n') as f:
            override_lines = f.read()

        ide_lines = self.format_ide(orig_lines, self.generate_ide_dict(override_lines), True)

        with open(ide_alt_output_path, 'w', encoding='utf_8_sig') as f:
            f.write(ide_lines)

        return


    def _dict_template(self, paratranz_zip_path): # バックアップしたIDEの言語ファイルからDnD、イベント名の辞書テンプレートを生成        

        tmp_dnd = []
        tmp_event_all = []

        ide_output_path = os.path.join(output_dir, os.path.split(ide_path)[1])

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
                m = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', m)
                dict_var = re.split(r'\t', m)

                del dict_var[0]

                if len(dict_var) < 2: # 翻訳がない
                    continue
                if dict_var[0] == dict_var[1]: # 原文＝翻訳
                    continue

                dict_var.append(r'((?:^|(?:[^a-zA-Z\p{S}\-_:;\.\,\/\% ])) *)(' + re.escape(dict_var[0]) + r')( *(?:$|(?:[^a-zA-Z\p{S}\-_:;\.\,\/\% ])))')
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
                output_path = os.path.join(output_dir, os.path.split(source_path)[1])
                os.makedirs(os.path.split(output_path)[0], exist_ok=True)
                with open(output_path, 'wb') as f:
                    lines = zip_file.read(source_path)
                    f.write(lines)

        return


class namedict(): # DnDアクション、イベント名の辞書

    def load_from_path(self, path): # ファイル内容をリストに変換して返す
        result = []

        if os.path.exists(path):
            with open(path, 'r', encoding='utf_8_sig', newline='\n') as f:
                lines = f.read().splitlines()

                # 書式 - 原文\t訳文\t原文（正規表現パターン有）\t訳文（正規表現パターン有）\t小/大文字の区別フラグ
                # 用例 - SOURCE    翻訳    ( ?)SOURCE() ?)    \1翻訳\2    i
                for line in lines:
                    dict_var = re.split(r'\t', line)

                    if len(dict_var) < 1:
                        continue
                    if dict_var[0] == dict_var[1]:
                        continue

                    re_flags = 0
                    if len(dict_var) >= 5 and 'i' in dict_var[4]:
                        re_flags = re.IGNORECASE # 大文字・小文字の区別を無効にする

                    if len(dict_var) >= 3: # 正規表現パターンが存在する場合はコンパイル
                        dict_var[2] = regex.compile(dict_var[2], flags=re_flags)
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

        for tr in tr_dict:

            re_flags = 0
            if len(tr) >= 5 and 'i' in tr[4]:
                re_flags = re.IGNORECASE # 大文字・小文字の区別を無効にする

            if len(tr) >= 2:

                if len(tr) >= 4:
                    re_m = tr[2].sub(tr[3], m) # パターンが存在する場合は正規表現置換
                else:
                    re_m = m.replace(tr[0], tr[1]) # 単純置換

                if '{CTR_N}' in re_m: # スペースつき対訳置換
                    re_m = regex.sub(r'{CTR_N} +' + tr[0], tr[1] + ' (' + tr[0] + ')', m, flags=re_flags)
                elif '{CTR_S}' in re_m: # スペースなし対訳置換
                    re_m = regex.sub(r'{CTR_S} +' + tr[0], ' ' + tr[1] + ' (' + tr[0] + ')', m, flags=re_flags)

                if m != re_m:
                    m = re_m
                    break

        return m


def read_glossary(paratranz_zip_path): # 用語集のファイル内容をリストに代入
    global glossary

    lines = ''
    with zipfile.ZipFile(paratranz_zip_path) as zip_file:
        lines = zip_file.read(glossary_path).decode('utf-8-sig')

    lines = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', lines)
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


class whx(): # whxdataディレクトリ以下にあるファイルの処理
    def __init__(self):
        self.db_base_dir = os.path.join(template_db_dir, 'whxdata')
        self.db_dist_dir = os.path.join(output_dir, output_manual_dirname, 'docs', 'whxdata')
        self.db_dist_ex_dir = os.path.join(output_ex_dir, output_manual_dirname, 'docs', 'whxdata')
        os.makedirs(self.db_dist_dir, exist_ok=True)
        os.makedirs(self.db_dist_ex_dir, exist_ok=True)

    def translate_from_file(self, source_path, dist_path, separate_pat, keys, *tr_dict): # ファイルを翻訳して出力

        with open(source_path, 'r', encoding='utf_8_sig') as f:
            lines = f.read()
        separated = re.split(separate_pat, lines)
        new_lines = []

        if len(keys) != len(tr_dict):
            return

        for m in separated:

            for idx, key in enumerate(keys):

                if m.startswith(key):
                    m = m.replace(key, '')

                    if tr_dict[idx].get(m):
                        m = tr_dict[idx].get(m)
                    m = key + m 

            new_lines.append(m)

        with open(dist_path, 'w', encoding='utf_8_sig') as f:
            f.write(''.join(new_lines))
        print('The db file file "{0}" has been successfully translated.'.format(dist_path))

    
    def translate_glossary(self):
        # 用語集を翻訳
        separate_pat = r'({[^}]+)("name":"[^"]+)(",)("value":"[^"]+)("},*)'
        keys = ['"name":"', '"value":"']
        whx_filename = 'gdata1.new.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dist_path = os.path.join(self.db_dist_dir, whx_filename)

        self.translate_from_file(source_path, dist_path, separate_pat, keys, {x[1]:x[2] for x in glossary}, {x[3]:x[4] for x in glossary})

    def translate_search_result(self):
        # 検索結果を翻訳
        separate_pat = r'([^\}]+{\\)("title\\":\\"[^"]+)(\\",\\)("summary\\":\\"[^"]+)(\\"[^\}]+\})'
        keys = ['"title\\":\\"', '"summary\\":\\"']
        whx_filename = 'search_topics.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dist_path = os.path.join(self.db_dist_dir, whx_filename)

        self.translate_from_file(source_path, dist_path, separate_pat, keys, {x[0]:x[1] for x in search_keywords}, {x[0]:x[1] for x in search_results})
        
        if Enable_fullTranslation:
            dist_path = os.path.join(self.db_dist_ex_dir, whx_filename)
            self.translate_from_file(source_path, dist_path, separate_pat, keys, {x[0]:x[1] for x in search_keywords_full}, {x[0]:x[1] for x in search_results_full})

    def translate_index(self):
        # 索引を翻訳
        separate_pat = r'([^{]+{)("name":"[^"]+)'
        keys = ['"name":"']
        whx_filename = 'idata1.new.js'
        source_path = os.path.join(self.db_base_dir, whx_filename)
        dist_path = os.path.join(self.db_dist_dir, whx_filename)
        topic_index.extend(search_keywords) # 検索結果のキーワードも含める
        self.translate_from_file(source_path, dist_path, separate_pat, keys, {x[0]:x[1] for x in topic_index})
        
        if Enable_fullTranslation:
            dist_path = os.path.join(self.db_dist_ex_dir, whx_filename)
            topic_index_full.extend(search_keywords_full) # 検索結果のキーワードも含める
            self.translate_from_file(source_path, dist_path, separate_pat, keys, {x[0]:x[1] for x in topic_index_full})

    def translate_table_of_contents(self, out_file_path):
        with zipfile.ZipFile(out_file_path) as zip_file:
            lines = zip_file.read(table_of_contents_path).decode('utf-8-sig')

        # csvファイルから変換用の辞書を作成
        lines = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', lines)

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

            f_distpath = os.path.join(self.db_dist_dir, file)
            with open(f_distpath, "w", encoding="utf_8_sig", newline="\n") as f:
                f.write(''.join(lines))
            f_distpath = os.path.join(self.db_dist_ex_dir, file)
            with open(f_distpath, "w", encoding="utf_8_sig", newline="\n") as f:
                f.write(''.join(lines_full_tr))

##############################################################################################

def check_for_changes():
    doc_dir = 'docs'
    converted_dir = os.path.join(output_dir, output_manual_dirname, doc_dir)

    file_pat = ''
    
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
            f_path = re.sub(os.path.join(output_dir, output_manual_dirname) + r'.docs', 'docs', f_path)
            dest_dict[f_path] = lines

    for k in source_dict:
        if dest_dict.get(k) != None and source_dict.get(k) != None:

            if source_dict.get(k) != dest_dict.get(k):
                with open('_COMMIT_RUN', "w") as f:
                    f.write('COMMIT_RUN')
                break
    else:
        return False

    return True

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

    # 辞書データを登録
    global Enable_fullTranslation

    if namedict().create_vars() == False: # 辞書ファイルを読み込みリストを生成
        Enable_fullTranslation = False # 失敗した場合はイベント名、DnDアクション名を翻訳しない

    # 用語集を読み込み
    read_glossary(out_file_path)

    # csvをhtmlに変換
    convert_from_zip(out_file_path)

    # whxdata以下にあるファイルを日本語化
    whxdata = whx()
    whxdata.translate_glossary()
    whxdata.translate_search_result()
    whxdata.translate_index()
    whxdata.translate_table_of_contents(out_file_path)

    # 出力ファイルに変更があるかどうかチェック
    if check_for_changes() == False:
        print("NO CHANGES FOUND.")
    else:
        print("complete")


def main(paratranz_secret):
    # 一時フォルダ用意
    os.makedirs("tmp", exist_ok=True)

    p_code = os.environ.get("PARATRANZ_CODE")
    
    sub(index_name="gms2",
        paratranz_project_code=p_code,
        paratranz_secret=paratranz_secret)


if __name__ == '__main__':
    main(paratranz_secret=os.environ.get("PARATRANZ_SECRET"))
