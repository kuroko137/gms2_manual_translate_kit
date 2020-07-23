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
# 0で無効、1でスペースを挿入、2でスペースを削除
Space_Adjustment = 1

# DnDアクション名を自動翻訳（単純置換）するかどうか
# Github Pagesには変更を与えず、専用のアーカイブファイル（GMS2_Japanese_Alt-master.zip）にのみ出力されます
Generate_FullTranslation = True
dnd_dirname = 'source/_build/3_scripting/2_drag_and_drop_reference'
# ev_dirname = 'source/_build/2_interface/1_editors/events'

po_replacer_kw = ['"Language: zh_CN\\n"', 
'"Language-Team: LANGUAGE <LL@li.org>\\n"', 
'"Project-Id-Version: PACKAGE VERSION\\n"'
]
po_replacer_tr = ['"Language: ja_JP\\n"', 
'"Language-Team: GMS2 Japanese Translation Team <paratranz.cn/projects/1100>\\n"', 
'"Project-Id-Version: Gamemaker Studio 2 EN2JP Translation Project\\n"'
]

html_replacer_re_kw = [
' to show toolbars of the Web Online Help System:', re.compile('Click ([^>]+>)here([^>]+>) to show toolbars of the Web Online Help System: ([^>]+>)show toolbars</a>')
]
html_replacer_re_tr = [
r'\1こちら\2をクリックするとWebオンラインヘルプのツールバーを表示します: \3ツールバーを表示</a>'
]

template_html_dir = 'tr_sources/source_html/' # GitPagesリポジトリのテンプレートHTML
template_pot_dir = 'tr_sources/source_pot/' # GitPagesリポジトリのテンプレートPOT
template_csv_dir = 'tr_sources/source_csv/' # GitPagesリポジトリのテンプレートCSV

input_dir = 'utf8/csv/' # ParaTranz側の翻訳ファイル
ide_translation_path = 'utf8/english.csv' # ParaTranz側のIDE言語ファイル
output_dir = 'Converted/'
output_ex_dir = 'Converted_EX/'

restore_re_key = [re.compile('^"location","(source|target)","(target|source)"\n'), '"location","source","target"\n']

compiled_raw_csv_file_patter = re.compile(r'^' + input_dir + '.*\.csv$')


dict_dndname = []
dict_eventname = []


##########################################

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
    dl_failed = 0
    try:
        my_file.write(urllib.request.urlopen(req).read())
    except IOError:
        print('IOError')
        dl_failed = 1

    if dl_failed == 1:
        print('Failed to download from paratranz')
        sys.exit(1)

    return out_file_path


def set_tr_dict(paratranz_zip_path):

    if Generate_FullTranslation == False:
        return

    global dict_dndname
    global dict_eventname
    dict_output_dnd = []
    dict_output_ev = []

    # IDEの言語ファイルからDnD、イベント名の自動置き換え辞書を作成
    with zipfile.ZipFile(paratranz_zip_path) as zip_file:

        ide_output_dir = os.path.join(output_dir)
        ide_output_path = os.path.join(ide_output_dir, os.path.split(ide_translation_path)[1])

        if not os.path.exists(ide_output_dir):
            os.makedirs(ide_output_dir)

        with open(ide_output_path, 'wb') as f:
            f.write(zip_file.read(ide_translation_path))

        with open(ide_output_path, 'r', encoding='utf_8_sig', newline='\n') as f:
            ide_lines = f.readlines()

        for m in ide_lines:

            matched = ''

            if re.match(r'"?GMStd[^,\r\n]+_Name"?,', m):
                matched = 'dnd'
            elif re.match(r'"?Event_[^,]+"?,', m):
                matched = 'ev'

            if matched:
                m = m.rstrip('\n')
                m = m.replace('"', '')
                m = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', m)
                dict_var = re.split(r'\t', m)

                del dict_var[0]

                if len(dict_var) < 2:
                    continue
                if dict_var[0] == dict_var[1]:
                    continue

                if matched == 'dnd':
                    dict_dndname.append(dict_var)
                else:
                    dict_eventname.append(dict_var)

    # 辞書を長さ順でソート
    dict_dndname = sorted(dict_dndname, key=lambda x: len(x[0]), reverse=True)
    dict_eventname = sorted(dict_eventname, key=lambda x: len(x[0]), reverse=True)

    # 辞書を外部ファイルに書き出し
    for line in dict_dndname:
        dict_output_dnd.append('\t'.join(line))
    for line in dict_eventname:
        dict_output_ev.append('\t'.join(line))

    path_dict_dir = os.path.join(output_dir, 'dict')
    if not os.path.exists(path_dict_dir):
        os.makedirs(path_dict_dir)
    
    path_dnd_dict = os.path.join(path_dict_dir, 'dict_dndname.txt')
    with open(path_dnd_dict, 'w+', encoding='utf_8_sig') as f:
        lines = '\n'.join(dict_output_dnd)
        f.write(lines)

    path_ev_dict = os.path.join(path_dict_dir, 'dict_eventname.txt')
    with open(path_ev_dict, 'w+', encoding='utf_8_sig') as f:
        lines = '\n'.join(dict_output_ev)
        f.write(lines)


    return


def restore_csv_commentout(source_lines, new_lines):

    cnt = 0
    for line in source_lines:
        cnt += 1
        if '#CSV_COMMENT_OUT#' in line:
            restored_line = re.sub(r'#CSV_COMMENT_OUT#"?([^"]+)"?([^\r\n]+)', r'\1\2', line)
            new_lines.insert(cnt, restored_line)
    lines = '\n'.join(new_lines)

    return lines

def format_csv(lines, base_path, mode):

    # 正規表現パターン定義
    insert_pat = [ # 半角スペースの挿入パターン
    regex.compile(r'([^ \p{Ps}\p{Pe}">])((<[^>]+>)*)(<b>)((<[^>]+>)*)'),
    regex.compile(r'((<[^>]+>)*)(</b>)((<[^>]+>)*)([^ \p{Ps}\p{Pe}"<])'),
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


    # 一行ごとの処理
    lines = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\t', lines)
    new_lines = ''
    l_split = lines.splitlines(True)

    for line in l_split:
        s = re.split(r'\t', line)

        if len(s) < 3: # 翻訳がないため処理をしない
            line = ','.join(s)
            new_lines += line
            continue

        # 日本語/英数字、および<b>, <a href>タグの間に半角スペースを挿入・削除
        if Space_Adjustment == 1: # 半角スペースを挿入する場合
            s[2] = insert_pat[0].sub(r'\1 \2\4\5', s[2])
            s[2] = insert_pat[1].sub(r'\1\3\4 \6', s[2])
            s[2] = insert_pat[2].sub(r'\1 \2\4\5', s[2])
            s[2] = insert_pat[3].sub(r'\1\3\4 \6', s[2])
            s[2] = insert_pat[4].sub(r'\1 \2\4\6', s[2])
            s[2] = insert_pat[5].sub(r'\1\4 \6\8', s[2])
            s[2] = insert_pat[6].sub(r'\1', s[2])
            s[2] = insert_pat[7].sub(r'\1', s[2])
            s[2] = insert_pat[8].sub(r'\\n', s[2])

        elif Space_Adjustment == 2: # 半角スペースを削除する場合
            s[2] = remove_pat[0].sub(r'\1\2\4\6', s[2])
            s[2] = remove_pat[1].sub(r'\1\4\6\8', s[2])


        # アクション/イベント名を自動置き換え
        if mode == 'dnd':
            for tr in dict_dndname:

                if tr[0] in s[2] and len(tr) >= 2:

                    if '{CTR_N}' in s[2]: # スペースつき対訳置換
                        s[2] = re.sub(r'{CTR_N} +' + tr[0], tr[1] + ' (' + tr[0] + ')', s[2])
                    elif '{CTR_S}' in s[2]: # スペースなし対訳置換
                        s[2] = re.sub(r'{CTR_S} +' + tr[0], ' ' + tr[1] + ' (' + tr[0] + ')', s[2])
                    else:
                        s[2] = s[2].replace(tr[0], tr[1])
                    break

        line = ','.join(s)
        new_lines += line
    lines = new_lines


    # コメント列を復元（エントリ破損防止）
    lines = re.sub(r'([\r\n]+)', r',""\1', lines)

    # テンプレートを復元
    if restore_re_key[0] != '':
        lines = restore_re_key[0].sub( '', lines)
        lines = restore_re_key[1] + lines

    # キーを復元
    orig_key = 'YoYoStudioHelp'
    if os.path.split(base_path)[0]:
        orig_key = orig_key + chr(47) + os.path.split(base_path)[0]
    orig_key = orig_key.replace(chr(47), chr(92) + chr(92))
    lines = re.sub(r'([^"\r\n]+\.html\+[^:]+:[0-9]+\-[0-9]+)', '"' + orig_key + chr(92) + chr(92) + r'\1"', lines)

    return lines

def format_po(lines):

    idx = 0

    for _keyword in po_replacer_kw:
        # プロパティの情報を修正
        if po_replacer_tr[idx] != '' and _keyword in lines:
            lines = lines.replace(_keyword, po_replacer_tr[idx], 1)
        idx += 1

    return lines

def format_html(lines):

    idx = 0
    tr_idx = 0

    # TranslateKitで抽出できないテキストを翻訳
    for _keyword in html_replacer_re_kw:
        if idx % 2 == 0:
            if _keyword in lines:
                lines = html_replacer_re_kw[idx + 1].sub(html_replacer_re_tr[tr_idx], lines)
        else:
            tr_idx += 1
        idx += 1

    # コードの識別子を削除
    lines = re.sub(r'{ANY_CODE} ?', '', lines)

    # 画像テキストの識別子を削除
    lines = re.sub(r'{IMG_TXT} ?', '', lines)

    # 対訳識別子を削除
    lines = re.sub(r'{CTR_N} ?', '', lines)
    lines = re.sub(r'{CTR_S}', '', lines)

    # URLのドットを復元
    lines = re.sub(r'{\-dot\-}', r'.', lines)

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


def convert_csv_to_html_from_zip(paratranz_zip_path):

    with zipfile.ZipFile(paratranz_zip_path) as zip_file:
        infos = zip_file.infolist() # 各メンバのオブジェクトをリストとして返す

        for info in infos:

            if compiled_raw_csv_file_patter.match(info.filename) is None:
                continue


            exoport_mode = ['']

            if Generate_FullTranslation:
                if info.filename.find(dnd_dirname) > 0:
                    exoport_mode.append('dnd')

                # if ev_dirname.match(info.filename):
                #    mode.append('ev')


            for mode in exoport_mode:

                base_path = info.filename.replace(input_dir, '')
                base_path = os.path.splitext(base_path)[0]

                if mode != '':
                    dist_dir = output_ex_dir
                else:
                    dist_dir = output_dir

                # ParaTranzのバックアップ用csvを生成
                path_csv = os.path.join(dist_dir + 'csv', base_path) + '.csv'

                if not os.path.exists(os.path.split(path_csv)[0]):
                    os.makedirs(os.path.split(path_csv)[0])

                with open(path_csv, 'wb') as f:
                    f.write(zip_file.read(info.filename))

                # base_path = base_path.encode('cp437').decode('cp932')
                base_path = base_path.replace('／', chr(47)) # 置き換えられたファイル名の'／'をパスとしての'/'に復元

                path_csv_csv = os.path.join(dist_dir + 'csv_cnv', base_path) + '.csv'
                path_source_csv = os.path.join('repo/' + template_csv_dir, base_path) + '.csv'


                # コメントアウトしたCSV行を復元
                with open(path_source_csv, 'r', encoding='utf_8_sig', newline='\n') as f_source:
                    source_lines = f_source.read().splitlines()

                with open(path_csv, 'r', encoding='utf_8_sig', newline='\n') as f_input:
                    new_lines = f_input.read().splitlines()

                csv_lines = restore_csv_commentout(source_lines, new_lines)

                with open(path_csv, 'w+', encoding='utf_8_sig', newline='\n') as f_input:
                    f_input.write(csv_lines)


                # 整形したCSVを生成
                with open(path_csv, 'r', encoding='utf_8_sig', newline='\n') as f_input:
                    csv_lines = format_csv(f_input.read(), base_path, mode)

                if not os.path.exists(os.path.split(path_csv_csv)[0]):
                    os.makedirs(os.path.split(path_csv_csv)[0])

                with open(path_csv_csv, 'w+', encoding='utf_8_sig', newline='\n') as f_input:
                    f_input.write(csv_lines)


                # CSVファイルをPOファイルに変換
                path_cnv_po = os.path.join(dist_dir + 'po_cnv', base_path) + '.po'
                path_template = os.path.join('repo/' + template_pot_dir, base_path) + '.pot'

                if not os.path.exists(path_template):
                    print('SKIP CSV TEMPLATE = {0} '.format(path_template))
                    continue
                    
                if not os.path.exists(os.path.split(path_cnv_po)[0]):
                    os.makedirs(os.path.split(path_cnv_po)[0])

                f_input = open(path_csv_csv, 'rb')
                f_output = open(path_cnv_po, 'wb+')
                f_template = open(path_template, 'rb')
                
                convertcsv(f_input, f_output, f_template, charset='utf_8_sig') # Translate-KitによるCSV > POの変換処理

                f_input.close()
                f_output.close()
                f_template.close()
                
                
                # POの整形
                with open(path_cnv_po, 'r', encoding='utf_8_sig', newline='\n') as f_po:
                    po_lines = format_po(f_po.read())
                with open(path_cnv_po, 'w+', encoding='utf_8_sig', newline='\n') as f_po:
                    f_po.write(po_lines)
                

                # HTMLへの変換を開始
                path_output = os.path.join(dist_dir + 'docs/', base_path) + '.html'
                path_template = os.path.join('repo/' + template_html_dir, base_path) + '.html'
                
                if not os.path.exists(path_template):
                    print('SKIP HTML TEMPLATE = {0} '.format(path_template))
                    continue
                
                if not os.path.exists(os.path.split(path_output)[0]):
                    os.makedirs(os.path.split(path_output)[0])
                
                f_po = open(path_cnv_po, 'rb')
                f_output = open(path_output, 'wb+')
                f_template = open(path_template, 'rb')
                
                print('converting: {0} to .html'.format(path_cnv_po))
                converthtml(f_po, f_output, f_template) # Translate-KitによるPO > HTMLの変換処理

                f_po.close()
                f_output.close()
                f_template.close()


                # HTMLの整形
                with open(path_output, 'r', encoding='utf_8_sig') as f_output:
                    html_lines = format_html(f_output.read())
                with open(path_output, 'w+', encoding='utf_8_sig') as f_output:
                    f_output.write(html_lines)

    return



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

    # 辞書データを取得
    set_tr_dict(out_file_path)
    # csvをhtmlに変換
    convert_csv_to_html_from_zip(out_file_path)

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
