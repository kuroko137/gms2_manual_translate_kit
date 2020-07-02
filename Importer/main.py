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

input_dir = 'utf8/csv/' # ParaTranz側の翻訳ファイル
template_dir_html = 'source_html/' # GitPagesリポジトリのテンプレートHTML
template_dir_pot = 'source_pot/' # GitPagesリポジトリのテンプレートPOT
output_dir = 'Converted/'

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
'\\1こちら\\2をクリックするとWebオンラインヘルプシステムのツールバーを表示します: \\3ツールバーを表示</a>'
]

restore_re_key = [re.compile('^"location","(source|target)","(target|source)"\n'), '"location","source","target"\n']


compiled_raw_csv_file_patter = re.compile(r'^' + input_dir + '.*\.csv$')


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


def convert_csv_to_html_from_zip(paratranz_zip_path):

    with zipfile.ZipFile(paratranz_zip_path) as zip_file:
        infos = zip_file.infolist() # 各メンバのオブジェクトをリストとして返す

        for info in infos:
            if compiled_raw_csv_file_patter.match(info.filename) is None:
                continue

            base_path = info.filename.replace(input_dir, '')
            base_path = os.path.splitext(base_path)[0]


            # バックアップ用のcsvを生成
            path_csv = os.path.join(output_dir + 'csv', base_path) + '.csv'

            if not os.path.exists(os.path.split(path_csv)[0]):
                os.makedirs(os.path.split(path_csv)[0])

            with open(path_csv, 'wb') as f:
                f.write(zip_file.read(info.filename))


            # 一時フォルダに整形したCSVを生成

            with open(path_csv, 'r', encoding='utf-8', newline='\n') as f_input:
                # 日本語/英数字の間に半角スペースを挿入・削除
                csv_lines = f_input.read()

                insert_pat = [
                regex.compile(r'([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])((<[^>]+>)*)((\p{Ps})?)([a-zA-Z0-9™])'),
                regex.compile(r'(([a-zA-Z0-9™])(\p{Pe}?))((<[^>]+>)*)((\p{Ps})?)([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])'),
                re.compile(r'(、|。|！|？) '),
                re.compile(r' (、|。|！|？)'),
                re.compile(r'\\n ')
                ]

                remove_pat = [
                regex.compile(r'([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}]) ?((<[^>]+>)*) ?((\p{Ps})?)([a-zA-Z0-9™])'),
                regex.compile(r'(([a-zA-Z0-9™])(\p{Pe}?)) ?((<[^>]+>)*)((\p{Ps})?) ?([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])')
                ]

                if Space_Adjustment == 1:
                    csv_lines = insert_pat[0].sub(r'\1 \2\4\6', csv_lines)
                    csv_lines = insert_pat[1].sub(r'\1\4 \6\8', csv_lines)
                    csv_lines = insert_pat[2].sub(r'\1', csv_lines)
                    csv_lines = insert_pat[3].sub(r'\1', csv_lines)
                    csv_lines = insert_pat[4].sub(r'\\n', csv_lines)
                elif Space_Adjustment == 2:
                    csv_lines = remove_pat[0].sub(r'\1\2\4\6', csv_lines)
                    csv_lines = remove_pat[1].sub(r'\1\4\6\8', csv_lines)

                # ヘッダーを復元
                if restore_re_key[0] != '':
                    csv_lines = restore_re_key[0].sub( '', csv_lines)
                    csv_lines = restore_re_key[1] + csv_lines

            path_cnv_csv = os.path.join(output_dir + 'csv_cnv', base_path) + '.csv'

            if not os.path.exists(os.path.split(path_cnv_csv)[0]):
                os.makedirs(os.path.split(path_cnv_csv)[0])

            with open(path_cnv_csv, 'w+', encoding='utf-8', newline='\n') as f_input:
                f_input.write(csv_lines)


            # CSVファイルをPOファイルに変換

            path_cnv_po = os.path.join(output_dir + 'po', base_path) + '.po'
            path_template = os.path.join('repo/' + template_dir_pot, base_path) + '.pot'

            if not os.path.exists(path_template):
                print('SKIP CSV TEMPLATE = {0} '.format(path_template))
                continue
                
            if not os.path.exists(os.path.split(path_cnv_po)[0]):
                os.makedirs(os.path.split(path_cnv_po)[0])

            f_input = open(path_cnv_csv, 'rb')
            f_output = open(path_cnv_po, 'wb+')
            f_template = open(path_template, 'rb')
            
            convertcsv(f_input, f_output, f_template, charset='utf-8') # Translate-KitによるCSV > POの変換処理

            f_input.close()
            f_output.close()
            f_template.close()
            
            
            # POの整形

            with open(path_cnv_po, 'r', encoding='utf-8', newline='\n') as f_po:
                po_lines = f_po.read()

                count = 0

                for _keyword in po_replacer_kw:
                    # プロパティの情報を修正
                    if po_replacer_tr[count] != '' and _keyword in po_lines:
                        po_lines = po_lines.replace(_keyword, po_replacer_tr[count], 1)
                    count += 1

            with open(path_cnv_po, 'w+', encoding='utf-8', newline='\n') as f_po:                
                f_po.write(po_lines)
            

            # HTMLへの変換を開始

            path_output = os.path.join(output_dir + 'docs/', base_path) + '.html'
            path_template = os.path.join('repo/' + template_dir_html, base_path) + '.html'
            
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


            with open(path_output, 'r', encoding='utf-8') as f_output:

                html_lines = f_output.read()

                count = 0
                tr_count = 0

                # HTMLファイルの整形
                for _keyword in html_replacer_re_kw:
                    if count % 2 == 0:
                        if _keyword in html_lines:
                            html_lines = html_replacer_re_kw[count + 1].sub(html_replacer_re_tr[tr_count], html_lines)
                    else:
                        tr_count += 1
                    count += 1

            with open(path_output, 'w+', encoding='utf-8') as f_output:
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
