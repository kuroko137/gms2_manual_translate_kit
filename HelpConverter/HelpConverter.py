from tkinter import *
import tkinter.filedialog, tkinter.messagebox
import os
import shutil
import zipfile
import urllib.parse
import regex as re
import Levenshtein
import time
from pathlib import Path
from natsort import natsorted
from translate.convert.html2po import converthtml
from translate.convert.po2csv import convertcsv
from translate.tools.pretranslate import pretranslate_file

title = 'HelpConverter for GMS2 - 2.10'

# DnDアクション、Event名のラベルに対訳表示用のタグを追加するかどうか
COUNTER_TRANSLATION = True

# 構造の簡易化がオンの場合、GMLリファレンスの出力ディレクトリを[A-B]のようにアルファベットで細分化するかどうか
GML_SEPARATE = True

archive_name = 'GMS2-Robohelp.zip' # アーカイブ名＝キー名

ignore_files_path = './ignore_files.ini' # 翻訳対象としないファイル
user_settings_path = './user_settings.ini' # オプションの設定履歴

dir_name_output = 'output'
dir_name_paratranz = 'paratranz'
dir_name_tr_paratranz = 'paratranz_with_tr'
dir_name_up_paratranz = 'paratranz_updated'
dir_name_repository = 'repository'

dir_name_po = 'po'
dir_name_csv = 'csv'
dir_name_docs = 'docs'
dir_name_override = 'override'
dir_name_override_ex = 'override_extra'
dir_name_source_html = 'tr_sources/source_html'
dir_name_source_db = 'tr_sources/source_db'
dir_name_source_pot = 'tr_sources/source_pot'
dir_name_source_csv = 'tr_sources/source_csv'

dnd_dirname = ['Drag_And_Drop/', 'Drag_And_Drop_Reference/']
gml_dirname = ['GameMaker_Language/', 'GML_Reference/']


csv_source_remove_key = [re.compile(r'("location","source","target"[^\r\n]*[\r\n]+)')]

csv_source_commentout = [
re.compile(r'([^\r\n]+Click here to see this page in full context[^\r\n]*)'),
re.compile(r'([^\r\n]+Copyright YoYo Games Ltd. 2020 All Rights Reserved[^\r\n]*)')
]

db_exclude_files = ['search_db.js', 'search_auto_model_0.js', 'search_auto_map_0.js', 'search_topics.js', 'text[/\\][0-9]+.js']

comma_replacer = re.compile(r',(?=(?:[^"\r\n]*"[^"\r\n]*")*[^"\r\n]*$)', re.MULTILINE | re.DOTALL)
isJp = re.compile(r'([\p{Hiragana}\p{Katakana}\p{Han}\p{InCJKSymbolsAndPunctuation}\p{InHalfwidthAndFullwidthForms}])')


##############################################################################################

class user_settings: # オプションの設定履歴
    def __init__(self):
        self.defaults = [['import_path', '...'], ['export_path', '...'], ['gms_version', '0'], ['simplified', 'True'], 
        ['add_url', 'False'], ['en_url', 'https://manual.yoyogames.com/'], ['jp_url', ''], ['url_type', 'True']]
        self.current = []

    def create_txt(self): # テキストがなければ作成
        if os.path.isfile(user_settings_path):
            return

        lines = [line[0] + ':=' + line[1] for idx, line in enumerate(self.defaults)]
        with open(user_settings_path, "w+") as f:
            f.write('\n'.join(lines))

    def generate_list(self): # テキストからリストを生成
        with open(user_settings_path, "r") as f:
            lines = f.read()

        for line in lines.splitlines(False):
            separated = re.split(':=', line)
            self.current.append([separated[0], separated[1]])

    def read_by_key(self, key): # リストの値を読み取り

        for data in self.current:
            if data[0] == key:
                return data[1]

        return ''

    def write_txt(self, *val): # 現在の設定をテキストファイルに書き込み

        if len(val) != len(self.current):
            return

        with open(user_settings_path, "r") as f:
            lines = f.read()

        new_lines = []
        for line in lines.splitlines(False):
            separated = re.split(':=', line)

            for idx in range(len(val)):

                if separated[0] == self.current[idx][0]:
                    separated[1] = val[idx]
                    break
            new_lines.append(':='.join(map(str, separated)))

        with open(user_settings_path, "w") as f:
            f.write('\n'.join(new_lines))

##############################################################################################


class App(tkinter.Frame): # GUIの設定

    def __init__(self, root):
        super().__init__(root, height=720, width=700)
        root.title(title)

        self.lastused = user_settings()
        self.lastused.create_txt()
        self.lastused.generate_list()

        self.w_import_path = StringVar(value=self.lastused.read_by_key('import_path'))
        self.w_export_path = StringVar(value=self.lastused.read_by_key('export_path'))
        self.w_old_path = StringVar(value='')
        self.w_gms_version = IntVar(value=self.lastused.read_by_key('gms_version'))
        self.w_simple_structure = BooleanVar(value=self.lastused.read_by_key('simplified'))
        self.w_url_is_add = BooleanVar(value=self.lastused.read_by_key('add_url'))
        self.w_url_en = StringVar(value=self.lastused.read_by_key('en_url'))
        self.w_url_jp = StringVar(value=self.lastused.read_by_key('jp_url'))
        self.w_url_type = BooleanVar(value=self.lastused.read_by_key('url_type'))

        # ウィジェットの作成
        l_import_path = Label(root, text = 'GMS2-Robohelp-en.zip:\n[.../ProgramData/GameMakerStudio2/GMS2-Robohelp-en.zip]')
        e_import_path = Entry(textvariable = self.w_import_path)
        b_import_path = Button(root, text = 'パスを指定', command = self.SetImportPath)

        l_export_path = Label(root, text = '変換したファイルの出力先:\n[.../]')
        e_export_path = Entry(textvariable = self.w_export_path)
        b_export_path = Button(root, text = 'パスを指定', command = self.SetExportPath)

        l_old_path = Label(root, text = '前バージョンのcsvからアップデート（任意指定）:\n[.../utf8/csv/]')
        e_old_path = Entry(textvariable = self.w_old_path)
        b_old_path = Button(root, text = 'パスを指定', command = self.SetOldPath)

        l_gms_version = Label(root, text = 'GMS2のバージョン（小数点なしのメジャーVer）')
        e_gms_version = Entry(textvariable = self.w_gms_version)

        c_add_url = Checkbutton(root, variable = self.w_url_is_add, text='コンテキストにURLを追加')
        c_url_type = Checkbutton(root, variable = self.w_url_type, text='URLをフレーム同時表示可にする')

        l_en_url = Label(root, text = '英語版マニュアルのURL:')
        e_en_url = Entry(textvariable = self.w_url_en)
        l_jp_url = Label(root, text = '日本語版マニュアルのURL:')
        e_jp_url = Entry(textvariable = self.w_url_jp)

        c_simple_structure = Checkbutton(root, variable = self.w_simple_structure, text='ディレクトリ構成を簡易化')

        b_run = Button(root, text = '変換開始', padx = 50, command = self.Run)

        self.lb = Listbox(root)

        sb1 = Scrollbar(root, orient = 'v', command = self.lb.yview)
        sb2 = Scrollbar(root, orient = 'h', command = self.lb.xview)

        self.lb.configure(yscrollcommand = sb1.set)
        self.lb.configure(xscrollcommand = sb2.set)

        # ウィジェットを配置
        l_import_path.place(rely=0, relwidth=1.0)
        e_import_path.place(rely=0.06, relx=0.03, relwidth=0.83)
        b_import_path.place(rely=0.055, relx=0.87, width=80)
        l_export_path.place(rely=0.10, relwidth=1.0)
        e_export_path.place(rely=0.16, relx=0.03, relwidth=0.83)
        b_export_path.place(rely=0.155, relx=0.87, width=80)
        l_old_path.place(rely=0.20, relwidth=1.0)
        e_old_path.place(rely=0.26, relx=0.03, relwidth=0.83)
        b_old_path.place(rely=0.255, relx=0.87, width=80)

        l_gms_version.place(rely=0.32, relx=0.20)
        e_gms_version.place(rely=0.32, relx=0.615, width=50)
        c_simple_structure.place(rely=0.37, relx=0.05)
        c_add_url.place(rely=0.37, relx=0.32)
        c_url_type.place(rely=0.37, relx=0.59)

        l_en_url.place(rely=0.42, relwidth=1.0)
        e_en_url.place(rely=0.47, relx=0.04, relwidth=0.81)
        l_jp_url.place(rely=0.52, relwidth=1.0)
        e_jp_url.place(rely=0.57, relx=0.04, relwidth=0.81)

        b_run.place(rely=0.62, relx=0.35, width=150)
        self.lb.place(rely=0.68, relx=0.02, relwidth=0.84, relheight=0.25)
        sb1.place(rely=0.68, relx=0.9, relheight=0.3)
        sb2.place(rely=0.95, relx=0.02, relwidth=0.84)


    def SetImportPath(self):
        fTyp = [("","*.zip")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        val = tkinter.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)
        val = val.replace('/', os.sep)
        self.w_import_path.set(str(val))
        return

    def SetExportPath(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        val = tkinter.filedialog.askdirectory(initialdir = iDir)
        val = val.replace('/', os.sep)
        self.w_export_path.set(str(val))
        return

    def SetOldPath(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        val = tkinter.filedialog.askdirectory(initialdir = iDir)
        val = val.replace('/', os.sep)
        self.w_old_path.set(str(val))
        return


    def Run(self):
        import_path = self.w_import_path.get()
        export_path = self.w_export_path.get()
        old_path = self.w_old_path.get()
        gms_version = self.w_gms_version.get()
        simple_structure = self.w_simple_structure.get()
        url_is_add = self.w_url_is_add.get()
        url_en = self.w_url_en.get()
        url_jp = self.w_url_jp.get()
        url_type = self.w_url_type.get()

        if import_path == '...' or import_path == '':
            tkinter.messagebox.showinfo('アーカイブが未指定', 'アーカイブのパスが指定されていません。\nProgramData にある GameMakerStudio2/GMS2-Robohelp-en.zip を指定してください。')
            return
        elif not os.path.isfile(import_path):
            tkinter.messagebox.showinfo('無効なアーカイブ', 'アーカイブが存在しない、または無効なアーカイブです。\nProgramData にある GameMakerStudio2/GMS2-Robohelp-en.zip を指定してください。')
            return

        if not os.path.isfile(ignore_files_path):
            tkinter.messagebox.showinfo('エラー', '無視ファイルリスト（ignore_files.ini）が存在しません。')
            return

        if export_path == '...' or export_path == '':
            export_path = os.getcwd()
            self.w_export_path.set(str(export_path))

        if url_is_add == True:
            en_parse = urllib.parse.urlparse(url_en)
            jp_parse = urllib.parse.urlparse(url_jp)

            if url_en == '':
                tkinter.messagebox.showinfo('URLが未指定', '英語版マニュアルのURLが指定されていません。\nURLを指定し直すか、チェックを外してください。')
                return
            elif len(en_parse.netloc) == 0 or (en_parse.scheme != 'http' and en_parse.scheme != 'https'):
                tkinter.messagebox.showinfo('不正なURL', '英語版マニュアルのURLが不正です。\nhttps://url/ 形式で指定する必要があります。\nURLを指定し直すか、チェックを外してください。')
                return
            elif url_jp == '':
                tkinter.messagebox.showinfo('URLが未指定', '日本語版マニュアルのURLが指定されていません。\nURLを指定し直すか、チェックを外してください。')
                return
            elif len(jp_parse.netloc) == 0 or (jp_parse.scheme != 'http' and jp_parse.scheme != 'https'):
                tkinter.messagebox.showinfo('不正なURL', '日本語版マニュアルのURLが不正です。\nhttps://url/ 形式で指定する必要があります。\nURLを指定し直すか、チェックを外してください。')
                return
            elif gms_version < 230 and url_type:
                tkinter.messagebox.showinfo('エラー', '2.30より古いバージョンでは ”フレーム同時表示可” オプションを使用できません。')
                return

        if gms_version == 0:
            tkinter.messagebox.showinfo('バージョン情報が未指定', 'バージョン情報が空です。\nGMS本体のバージョンを小数点なしで指定してください。\n（例: 2.2.5.378 > 225）')
            return
        elif gms_version < 100:
            tkinter.messagebox.showinfo('エラー', 'バージョン情報は100（1.0.0）以上にしてください。')
            return

        if old_path and not tkinter.messagebox.askokcancel(title="アップデート用 csv を出力", message="前バージョンと新バージョンの csv を比較し、変更点がある csv を 'paratranz_updated' に出力します。\nさらに翻訳をコピーした csv を 'paratranz_with_tr' に出力します。"):
            return

        self.lb.delete(0, tkinter.END) # ログの表示をクリア

        # -----------------------------------------------------------------------


        start = time.time()

        # 現在の設定をテキストに書き出し
        self.lastused.write_txt(import_path, export_path, gms_version, simple_structure, 
            url_is_add, url_en, url_jp, url_type)

        # 無視するファイルを追加
        with open(ignore_files_path, "r") as f:
            lines = f.read()
        ignore_files = [file for file in lines.splitlines(False)]

        # 各ディレクトリのパスを定義
        export_path = os.path.join(export_path, dir_name_output)
        paratranz_path = os.path.join(export_path, dir_name_paratranz)
        paratranz_tr_path = os.path.join(export_path, dir_name_tr_paratranz)
        paratranz_up_path = os.path.join(export_path, dir_name_up_paratranz)
        repository_path = os.path.join(export_path, dir_name_repository)

        # pot_output_dir = os.path.join(paratranz_path, dir_name_source_pot)
        po_output_dir = os.path.join(paratranz_path, dir_name_po)
        csv_output_dir = os.path.join(paratranz_path, dir_name_csv)

        source_csv_output_dir = os.path.join(repository_path, dir_name_source_csv)
        html_output_dir = os.path.join(repository_path, dir_name_source_html)
        db_output_dir = os.path.join(repository_path, dir_name_source_db)
        docs_output_dir = os.path.join(repository_path, dir_name_docs)
        tmp_dir = os.path.join(export_path, 'tmp')

        # 古いディレクトリがあったら掃除
        shutil.rmtree(paratranz_path, ignore_errors=True)
        shutil.rmtree(paratranz_tr_path, ignore_errors=True)
        shutil.rmtree(paratranz_up_path, ignore_errors=True)
        os.makedirs(paratranz_path, exist_ok=True)
        shutil.rmtree(repository_path, ignore_errors=True)
        os.makedirs(repository_path, exist_ok=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir, exist_ok=True)

        # キーが変動しないようアーカイブを一時ディレクトリにコピーしてリネーム
        tmp_archive_path = os.path.join(tmp_dir, archive_name)
        shutil.copy(import_path, tmp_archive_path)
        import_path = tmp_archive_path

        zip_output_dir = os.path.join(export_path, os.path.splitext(os.path.split(import_path)[1])[0])

        # whxdata関連ファイルをアーカイブから事前に取り出し
        self.lb.insert('end', 'Converting whxdata files...')
        self.update()

        with zipfile.ZipFile(import_path) as zip_file:
            infos = zip_file.infolist()

            for info in infos:
                if re.match(r'.*/$', info.filename): # ディレクトリは除外
                    continue
                if info.filename.startswith('whxdata') is False:
                    continue

                SKIP = False
                for file in db_exclude_files:
                    if re.search(file, info.filename): # 除外するファイルを検索
                        SKIP = True
                        break
                if SKIP:
                    continue

                path_db = os.path.join(export_path, db_output_dir, info.filename)

                os.makedirs(os.path.split(path_db)[0], exist_ok=True)

                with open(path_db, "wb+") as f_db:
                    f_db.write(zip_file.read(info.filename))

        # 用語集を抽出してcsvファイル化（whxdata）
        if old_path:
            os.makedirs(paratranz_up_path, exist_ok=True)

        path_source_glossary = os.path.join(db_output_dir, 'whxdata', 'gdata1.new.js')
        with open(path_source_glossary, "r", encoding="utf_8_sig", newline="\n") as f:
            lines = f.read()

        lines_glossary = generate_sub().glossary(lines)
        path_glossary = os.path.join(paratranz_path, 'manual_glossary.csv')
        with open(path_glossary, "w+", encoding="utf_8_sig", newline="\n") as f:
            f.write(lines_glossary)
        if old_path:
            path_glossary = os.path.join(paratranz_up_path, 'manual_glossary.csv')
            with open(path_glossary, "w+", encoding="utf_8_sig", newline="\n") as f:
                f.write(lines_glossary)

        # 左メニューの.jsファイルをまとめてcsvファイル化（whxdata）
        lines_contents = generate_sub().table_of_contents(os.path.join(db_output_dir, 'whxdata'))
        path_contents = os.path.join(paratranz_path, 'manual_leftmenu.csv')
        with open(path_contents, "w+", encoding="utf_8_sig", newline="\n") as f:
            f.write(lines_contents)
        if old_path:
            path_contents = os.path.join(paratranz_up_path, 'manual_leftmenu.csv')
            with open(path_contents, "w+", encoding="utf_8_sig", newline="\n") as f:
                f.write(lines_contents)

        self.lb.insert('end', 'All whxdata files have been converted.')
        self.update()

        # -----------------------------------------------------------------------


        # アーカイブの展開を開始
        with zipfile.ZipFile(import_path) as zip_file:
            infos = zip_file.infolist()
            export_count = 0 # ファイル処理数（ログ更新のしきい値）

            for info in infos:
                passed = False

                if re.match(r'.*/$', info.filename): # ディレクトリは除外
                    continue

                if re.match(r'.*.htm?$', info.filename) is None:
                    passed = True

                # 無視するファイルを検索
                if passed == False:
                    for ignore in ignore_files:
                        if re.search(ignore, info.filename):
                            passed = True
                            break

                # 翻訳対象ファイルでないためdocs（GitHub Pagesのディレクトリ）にコピー
                if passed == True:
                    path_others = os.path.join(export_path, docs_output_dir, os.path.join(os.path.split(info.filename)[0]), os.path.split(info.filename)[1])
                    os.makedirs(os.path.split(path_others)[0], exist_ok=True)

                    with open(path_others, "wb+") as f:
                        f.write(zip_file.read(info.filename))

                    continue

                # 基本パス
                base_dir = os.path.join(os.path.split(info.filename)[0])


                # ソースHTMLを別ディレクトリにコピー
                path_html = os.path.join(export_path, zip_output_dir, base_dir, os.path.split(info.filename)[1])

                os.makedirs(os.path.split(path_html)[0], exist_ok=True)
                with open(path_html, "wb+") as f_html:
                    f_html.write(zip_file.read(info.filename))


                # HTMLの整形
                with open(path_html, "r", encoding="utf_8_sig") as f_html:
                    html_lines = f_html.read()

                html_lines = format_lines()._html(html_lines, base_dir)

                with open(path_html, "w+", encoding="utf_8_sig") as f_html:
                    f_html.write(html_lines)


                # HTML > POファイルの変換処理
                path_pot = os.path.join(repository_path, dir_name_source_pot, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.pot'
                path_po = os.path.join(po_output_dir, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.po'

                os.makedirs(os.path.split(path_po)[0], exist_ok=True)
                os.makedirs(os.path.split(path_pot)[0], exist_ok=True)

                f_input = open(path_html, 'rb')
                f_output = open(path_po, 'wb+')
                f_template = open(path_pot, 'wb+')

                converthtml(inputfile=f_input, outputfile=f_output, templates=f_template, pot=True, keepcomments=True) # HTML から PO に変換

                f_input.close()
                f_output.close()
                f_template.close()


                # POの整形
                with open(path_po, "r", encoding="utf_8_sig") as f_po:
                    po_lines = f_po.read()

                po_lines = format_lines()._po(po_lines, import_path)

                with open(path_po, "w", encoding="utf_8_sig") as f_po:
                    f_po.write(po_lines)


                # Translate-Kit 3.0.0現在、空のPOTファイルが出力されてしまうためPOの内容をPOTに上書き
                with open(path_pot, "w", encoding="utf_8_sig") as f_po:
                    f_po.write(po_lines)


                # CSVファイルの出力先をセット
                path_source_csv = ''
                path_csv = ''
                csv_root = ''

                if simple_structure: # ディレクトリ構成の簡易化がチェックされている場合

                    separated = re.findall(r'^([^/]+/)(' + dnd_dirname[1] + '|' + gml_dirname[1] + ')?(.*)', base_dir, flags=re.IGNORECASE)
                    new_path = []

                    split_range = ['A-B', 'C-D', 'E-L', 'M-P', 'Q-Z']
                    is_split = False

                    if len(separated) > 0:

                        for idx, item in enumerate(separated[0]):

                            if idx > 0 and not re.match(dnd_dirname[1], item, flags=re.IGNORECASE) and not re.match(gml_dirname[1], item, flags=re.IGNORECASE):
                                item = item.replace('/', '／') # パスのスラッシュをファイル名としてのスラッシュに置換

                            if GML_SEPARATE and re.match(gml_dirname[1], item, flags=re.IGNORECASE): # GML_SEPARATEがTrueに設定されている場合、GMLリファレンスのパス名を細分化
                                is_split = True
                            elif is_split:
                                for pattern in split_range: # アルファベット区間ごとに細分化する
                                    if re.match(r'[' + pattern + ']', item, flags=re.IGNORECASE):
                                        item = os.path.join(pattern, item)
                                        break
                                is_split = False

                            new_path.append(item)
                            idx += 1

                        # ParaTranzでの取り回しを良くするため、深層のディレクトリをファイル名に置き換え
                        csv_root = os.path.join(''.join(new_path) + '／') + os.path.splitext(os.path.split(info.filename)[1])[0] + '.csv'

                if csv_root == '':
                    csv_root = os.path.join(base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.csv'

                path_csv = os.path.join(csv_output_dir, csv_root)
                path_source_csv = os.path.join(repository_path, dir_name_source_csv, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.csv'


                # PO > CSV ファイルの変換処理
                os.makedirs(os.path.split(path_source_csv)[0], exist_ok=True)

                f_po = open(path_po, 'rb')
                f_csv = open(path_source_csv, 'wb+')
                f_template = open(path_html, 'r') # 実際には未使用であるものの、動作のためにテンプレートを指定する必要あり

                convertcsv(f_po, f_csv, f_template) # PO から CSV に変換

                f_po.close()
                f_csv.close()
                f_template.close()


                # ソースCSVの書き出し
                with open(path_source_csv, "r", encoding="utf_8_sig") as f_csv:
                    csv_lines = f_csv.read()

                csv_lines = format_lines()._csv(csv_lines, base_dir, info.filename, url_is_add, url_en, url_jp, url_type)

                with open(path_source_csv, "w", encoding="utf_8_sig", newline="\n") as f_csv:
                    f_csv.write(csv_lines)

                # CSVの書き出し
                csv_lines = re.sub(r'#CSV_COMMENT_OUT#[^\r\n]+[\r\n]+', '', csv_lines) # コメントアウトされたエントリを除外

                os.makedirs(os.path.split(path_csv)[0], exist_ok=True)
                with open(path_csv, "w+", encoding="utf_8_sig", newline="\n") as f_csv:
                    f_csv.write(csv_lines)


                # 前バージョンの翻訳が指定されている場合はアップデート処理を行う
                if old_path:
                    old_csv_path = os.path.join(old_path, csv_root)
                    add_updated = False

                    if not os.path.isfile(old_csv_path):
                        add_updated = True
                    else:
                        with open(old_csv_path, "r", encoding="utf_8_sig") as f:
                            old_lines = f.read()

                        if csv_is_diff(old_lines, csv_lines):
                            add_updated = True

                            # 翻訳をマージさせたcsvを出力
                            output_merged_path = os.path.join(paratranz_tr_path, dir_name_csv, csv_root)

                            lines = merge_translation(old_csv_path, path_csv, output_merged_path, tmp_dir)

                            if lines:
                                # マージ後のCSVを再整形
                                lines = format_lines()._csv(lines, base_dir, info.filename, url_is_add, url_en, url_jp, url_type)

                                # 変更確認

                                if csv_is_diff(old_lines, lines) == False or not isJp.findall(lines):
                                    os.remove(output_merged_path) # 変更がなければ削除
                                    try:
                                        os.removedirs(os.path.split(output_merged_path)[0])
                                    except OSError:
                                        pass
                                else:
                                    with open(output_merged_path, "w+", encoding="utf_8_sig", newline="\n") as f_output_csv:
                                        f_output_csv.write(lines)

                    if add_updated:
                        output_updated_path = os.path.join(paratranz_up_path, dir_name_csv, csv_root)
                        os.makedirs(os.path.split(output_updated_path)[0], exist_ok=True)
                        with open(output_updated_path, "w+", encoding="utf_8_sig", newline="\n") as f:
                            f.write(csv_lines)

                # リストボックスにログを出力
                path_csv = path_csv.replace('/', os.sep) # スラッシュを\\に置き換え
                self.lb.insert('end', path_csv)
                self.lb.see('end')

                export_count += 1

                if export_count % 10 == 0: # 10ファイル処理したらログを更新
                    self.update()


        # バージョンファイルを生成

        version_path = os.path.join(repository_path, '_VERSION')
        with open(version_path, "w+") as f:
            lines = str(gms_version)
            f.write(lines)

        # 不要となったディレクトリを削除
        shutil.rmtree(html_output_dir, ignore_errors=True)
        os.rename(zip_output_dir, html_output_dir)
        shutil.rmtree(po_output_dir, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)

        # その他のファイルをテンプレートからコピー
        if os.path.exists("./template"):
            shutil.copytree("./template", repository_path, dirs_exist_ok=True)

        elapsed_time = time.time() - start
        self.lb.insert('end', 'elapsed time = {0} sec'.format(elapsed_time))
        self.lb.see('end')
        self.update()
        tkinter.messagebox.showinfo('変換完了','CSV, POT ファイルへの変換が完了しました。')
        return

##############################################################################################


def csv_is_diff(old_read, new_read):

    old_read = comma_replacer.sub(r'\t', old_read)
    old_read = re.sub(r'"([^\t\r\n]*)"', r'\1', old_read, flags=re.MULTILINE)
    old_read = re.sub(r'(^[^\t\r\n]+\t[^\t\r\n]+)\t[^\r\n]+', r'\1', old_read, flags=re.MULTILINE)
    old_lines = old_read.splitlines(False)

    new_read = comma_replacer.sub(r'\t', new_read)
    new_read = re.sub(r'"([^\t\r\n]*)"', r'\1', new_read, flags=re.MULTILINE)
    new_read = re.sub(r'(^[^\t\r\n]+\t[^\t\r\n]+)\t[^\r\n]+', r'\1', new_read, flags=re.MULTILINE)
    new_lines = new_read.splitlines(False)

    if old_read != new_read:
        return True

    return False

def merge_translation(old_path, new_path, output_path, tmp_path):

    tmp_old_path = os.path.join(tmp_path, 'old.csv')
    tmp_new_path = os.path.join(tmp_path, 'new.csv')
    lines = ''

    if os.path.isfile(old_path):

        # 正確にマッチさせるため列と表記を合わせ、比較用の一時ファイルとして出力
        with open(old_path, "r", encoding="utf_8_sig", newline="\n") as f_csv:
            old_lines = f_csv.read()

        old_lines = comma_replacer.sub(r'\t', old_lines)
        old_lines = re.sub(r'(^[^"\r\n])', r'"\1', old_lines, flags=re.MULTILINE)
        old_lines = re.sub(r'([^"\r\n]$)', r'\1"', old_lines, flags=re.MULTILINE)
        old_lines = re.sub(r'(["]{0,1})\t(["]{0,1})', r'"\t"', old_lines, flags=re.MULTILINE)
        old_lines = re.sub(r'^(([^\t\r\n]+\t?){2,2})$', r'\1\t""', old_lines, flags=re.MULTILINE)
        old_lines = re.sub(r'\t', r',', old_lines)

        with open(new_path, "r", encoding="utf_8_sig", newline="\n") as f_csv:
            new_lines = f_csv.read()

        new_lines = comma_replacer.sub(r'\t', new_lines)
        new_lines = re.sub(r'^(([^\t\r\n]+\t?){0,3})\t[^\r\n]+', r'\1', new_lines, flags=re.MULTILINE)
        new_lines = re.sub(r'\t', r',', new_lines)

        with open(tmp_old_path, "w+", encoding="utf_8_sig", newline="\n") as f_csv:
            f_csv.write(old_lines)

        with open(tmp_new_path, "w+", encoding="utf_8_sig", newline="\n") as f_csv:
            f_csv.write(new_lines)

        os.makedirs(os.path.split(output_path)[0], exist_ok=True)

        # 全文一致
        f_input_csv = open(tmp_new_path, 'rb')
        f_output_csv = open(output_path, 'wb+')
        f_tm = open(tmp_old_path, 'rb')

        pretranslate_file(f_input_csv, f_output_csv, f_tm, fuzzymatching=False)

        f_input_csv.close()
        f_output_csv.close()
        f_tm.close()

        with open(output_path, "r", encoding="utf_8_sig") as f:
            no_fuzzy_lines = f.read()


        # あいまい一致用に原文のタグを消す
        new_lines = comma_replacer.sub(r'\t', new_lines)
        notags_lines = []
        for line in new_lines.splitlines(False):
            if line.count('"') % 2 != 0: # クォーテーションが一致しない＝破損したエントリ
                notags_lines.append(line)
            s = line.split('\t')
            if len(s) >= 2:
                s[1] = re.sub(r'(<[^>]+>)|(\{[^\}]+\})', '', s[1])
            notags_lines.append(','.join(s))

        with open(tmp_new_path, "w+", encoding="utf_8_sig", newline="\n") as f_csv:
            f_csv.write('\n'.join(notags_lines))

        old_lines = comma_replacer.sub(r'\t', old_lines)
        notags_lines = []
        for line in old_lines.splitlines(False):
            if line.count('"') % 2 != 0:
                notags_lines.append(line)
            s = line.split('\t')
            if len(s) >= 2:
                s[1] = re.sub(r'(<[^>]+>)|(\{[^\}]+\})', '', s[1])
            notags_lines.append(','.join(s))

        with open(tmp_old_path, "w+", encoding="utf_8_sig", newline="\n") as f_csv:
            f_csv.write('\n'.join(notags_lines))

        # あいまい一致
        f_input_csv = open(tmp_new_path, 'rb')
        f_output_csv = open(output_path, 'wb+')
        f_tm = open(tmp_old_path, 'rb')

        pretranslate_file(f_input_csv, f_output_csv, f_tm, min_similarity=75, fuzzymatching=True)

        f_input_csv.close()
        f_output_csv.close()
        f_tm.close()

        with open(output_path, "r", encoding="utf_8_sig") as f:
            fuzzy_lines = f.read()


        # 全文一致とあいまい一致を比較し、あいまい一致のラインに目印となるキーワードを入れる
        no_fuzzy_lines = comma_replacer.sub('\t', no_fuzzy_lines)
        fuzzy_lines = comma_replacer.sub('\t', fuzzy_lines)
        no_fuzzy_lines = no_fuzzy_lines.splitlines(False)
        fuzzy_lines = fuzzy_lines.splitlines(False)
        # 破損したエントリを削除
        no_fuzzy_lines = [line for line in no_fuzzy_lines if '\t' in line]
        fuzzy_lines = [line for line in fuzzy_lines if '\t' in line] 


        if len(no_fuzzy_lines) == len(fuzzy_lines):

            old_dict = {}
            for line in old_lines.splitlines(False):
                s = line.split('\t')
                if len(s) > 2 and s[2] != '""':
                    old_dict[s[2]] = s[1]

            for idx, line in enumerate(no_fuzzy_lines):
                s = line.split('\t')
                nt_s = fuzzy_lines[idx].split('\t')

                if len(s) > 2 and s[2] == '""':
                    if isJp.findall(nt_s[2]) and not ('（あいまい一致_') in nt_s[2]:

                        isdiff_source = (re.sub(r'<[^>]+>', '', s[1]) != re.sub(r'<[^>]+>', '', old_dict.get(nt_s[2], '')))
                        isdiff_tag = (''.join(re.findall(r'<[^>]+>', s[1])) != ''.join(re.findall(r'<[^>]+>', old_dict.get(nt_s[2], ''))))

                        if isdiff_tag and not isdiff_source:
                            s[2] = re.sub(r'^("?)', r'\1（あいまい一致_タグに差異）', nt_s[2])
                        elif isdiff_source and not isdiff_tag:
                            s[2] = re.sub(r'^("?)', r'\1（あいまい一致_原文に差異）', nt_s[2])
                        else:
                            s[2] = re.sub(r'^("?)', r'\1（あいまい一致）', nt_s[2])
                    else:
                        nt_s[2] = '""'
                no_fuzzy_lines[idx] = '\t'.join(s)

            no_fuzzy_lines.append('')
            lines = '\n'.join(no_fuzzy_lines)
        else:
            no_fuzzy_lines.append('')
            lines = '\n'.join(no_fuzzy_lines)

        lines = lines.replace('\t', ',')

    return lines


class format_lines():

    def _html(self, lines, base_dir): # HTMLの整形

        # コード行に識別子を挿入
        lines = re.sub(r'(<[^<]+class="code"[^>]*>)', r'\1{ANY_CODE} ', lines)

        # 戻り値/構文は識別子を外す
        lines = re.sub(r'((Returns|Syntax):?<[^>]+>[^<]+<p class="code">){ANY_CODE} ', r'\1', lines)

        # 画像のテキスト情報に識別子を挿入（作業時の目印用）
        lines = re.sub(r'(alt=")([^"]+")', r'\1{IMG_TXT} \2', lines)

        # 対訳を付加するエントリにタグを挿入
        if COUNTER_TRANSLATION:
            if re.match(''.join(dnd_dirname), base_dir, flags=re.IGNORECASE):
                lines = re.sub(r'(<h1><img alt=[^>]+(?=(?:Scripting_Reference/Drag_And_Drop/Reference))[^>]+>)([^>]+)', r'\1{WITH_ENG}\2', lines)
                lines = re.sub(r'(<div class="title" title=[^>]+>[\r\n ]*<span>)([^<]+)', r'\1{WITH_ENG}\2', lines)

        # 検索結果の表示テキストを抽出
        matched = re.search(r'<meta name="topic-comment" content="([^>]+)"/>', lines)
        if matched:
            contents = matched.group(1)
            s_comma = []
            for s in re.split(r',', contents):

                if re.search(r'^[a-zA-Z0-9_]*_[a-zA-Z0-9_]*$', s) or re.search(r'^[\p{S}\p{P}]+$', s): # 関数名/記号のみは除外
                    continue
                s = '<p>{SEARCH_RESULT} ' + s + '</p>'
                s_comma.append(s)
            if len(s_comma) > 0:
                lines = re.sub(r'</body>', lambda _: (''.join(s_comma)) + r'</body>', lines) # Translate-Kitに認識させるためテキストとして挿入

        # 索引のキーワードを抽出
        matched = re.search(r'<meta name="rh-index-keywords" content="([^>]+)"/>', lines)
        if matched:
            contents = matched.group(1)
            s_comma = []
            for s in re.split(r',', contents):
                if re.search(r'^[a-zA-Z0-9_]*_[a-zA-Z0-9_]*$', s) or re.search(r'^[\p{S}\p{P}]+$', s): # 関数名/記号のみは除外
                    continue
                s = '<p>{INDEX_KEYWORD} ' + s + '</p>'
                s_comma.append(s)
            if len(s_comma) > 0:
                lines = re.sub(r'</body>', lambda _: (''.join(s_comma)) + r'</body>', lines) # Translate-Kitに認識させるためテキストとして挿入

        # tooltipの内容をキーに置き換え
        new_lines = ''
        separated = re.split(r'(class="tooltip" title="[^>]+>[^<]+)', lines)
        for m in separated:
            if m.startswith('class="tooltip" title="'):
                m = re.sub(r'(class="tooltip" title=)"[^>]+>', '', m)
                key_name = re.sub(r'[ ,]', '_', m)
                m = 'class="tooltip" title="TITLE_KEY::' + key_name + '">' + m
            new_lines += m
        lines = new_lines

        # <span class="glossextra">s</span>のsは不要なので削除
        lines = re.sub(r'(<span class="glossextra">) *[es]+(</span>)', r'\1\2', lines)

        # ノーブレークスペースをダミータグに置換
        new_lines = ''
        separated = re.split(r'(<p class="code"> *|</p>)', lines)

        for m in separated:

            if m.startswith(r'{ANY_CODE}'):

                s_line = re.split(r'((\u00a0|&nbsp;)+)', m)
                new_line = []
                pre_match = False

                for s_nbs in s_line:

                    if pre_match:
                        pre_match = False
                        continue
                    else:
                        cnt = 0
                        if '\u00a0' in s_nbs:
                            cnt += s_nbs.count('\u00a0')
                        elif '&nbsp;' in s_nbs:
                            cnt += s_nbs.count('&nbsp;')

                        if cnt > 0:
                            s_nbs = re.sub(r'((\u00a0|&nbsp;)+)', '{nbsp_x' + str(cnt) + '}', s_nbs)
                            pre_match = True
                    new_line.append(s_nbs)

                m = ''.join(new_line)

            new_lines += m

        # 絶対URLのドットをダミータグに変換（ParaTranzでの誤ページ移動防止およびクリックでのコピーに対応）
        matched = re.findall(r'(<a href=[\r\n]*"https?://[^\/]+/)', new_lines)
        matched = list(set(matched)) # 重複したエントリを削除
        for m in matched:
            replaced = m.replace('.', '{-dot-}')
            new_lines = new_lines.replace(m, replaced)

        return new_lines


    def _po(self, lines, import_path): # POの整形

        new_lines = []
        pat = [re.compile(r'^#: ([^\r\n]+)$'), re.compile(r'^msgctxt ([^\r\n]+)$')]

        archive_name = os.path.splitext(os.path.basename(import_path))[0]
        archive_name_decoded = urllib.parse.quote(archive_name)

        po_replace_fullpath_key = [
        [re.compile(r'^#: [^\r\n]+%5C' + archive_name_decoded + r'%5'), r'#: ' + archive_name_decoded + r'%5'],
        [re.compile(r'^msgctxt [^\r\n]+' + archive_name + r'\\'), r'msgctxt "' + archive_name + r'\\'],
        [re.compile(r'^"[^\r\n]+' + archive_name + r'\\'), r'"' + archive_name + r'\\']
        ]

        for m in lines.splitlines(True):
            # 文字列位置のパスを相対パスに整形
            for path_key in po_replace_fullpath_key:
                m = path_key[0].sub(path_key[1], m)

            if pat[0].match(m):
                m = m.replace('/', '%5C') # スラッシュをurlエンコード
            if pat[1].match(m):
                m = m.replace('/', os.sep + os.sep) # スラッシュを\\に置き換え

            new_lines.append(m)

        return ''.join(new_lines)


    def _csv(self, lines, base_dir, filename, is_add_url, url_en, url_jp, url_type): # CSVの整形

        # ParaTranzでのエラー防止のため、キーのディレクトリ名をすべて省略してファイル名のみにする（Importerで後に復元）
        lines = re.sub(r'"(GMS2-Robohelp)\\([^"\r\n]+\\)*', '"', lines)

        # 不要なエントリを削除
        for key_val in csv_source_remove_key:
            lines = re.sub(key_val, '', lines)

        # 不要なエントリをコメントアウト
        for key_val in csv_source_commentout:
            lines = re.sub(key_val, r'#CSV_COMMENT_OUT#\1', lines)

        # コンテキストにURL情報をセット
        if is_add_url == True:

            urls = []
            url_dir = ''

            if base_dir and url_type == True: # 2.3（RoboHelp）用のURL
                url_dir = 'index.htm#t=' + urllib.parse.quote(base_dir + '/', safe='')
                urls = [(url_en + url_dir + os.path.split(filename)[1]), (url_jp + url_dir + os.path.split(filename)[1])]
            else: # ルートディレクトリ/旧バージョン用のURL
                if base_dir:
                    url_dir = base_dir + '/'
                urls = [(url_en + url_dir + os.path.split(filename)[1]), (url_jp + url_dir + os.path.split(filename)[1])]

            # URLを挿入
            context = r',"URL_EN : ' + urls[0] + r' \\n\\nURL_JP : ' + urls[1] + '"'
            lines = re.sub(r'(^|[\r\n])([^#][^\r\n]+)', r'\1\2' + context, lines)

        return lines


class generate_sub(): # whxdataのファイル用データを生成

    def glossary(self, lines): # 用語集の生成
        separated = re.split(r'(?:{[^}]+)("name":"[^"]+)(?:",)("value":"[^"]+)(?:"},*)', lines)

        current_key = ''
        new_lines = []

        for item in separated:
            name_key = '"name":"'
            value_key = '"value":"'

            if item.startswith(name_key):
                current_key = re.sub(r'[ ,]', '_', item[len(name_key):])
                new_lines.append(current_key + '_Name,"' + item[len(name_key):] + '"')
            elif item.startswith(value_key):
                new_lines.append(current_key + '_Desc,"' + item[len(value_key):] + '"')

        new_lines.append('')

        return '\n'.join(new_lines)


    def table_of_contents(self, base_dir): # 左メニューテーブルの生成

        # ファイルリストを作成
        file_paths = [file for file in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, file)) and re.search(r'toc[0-9]*\.new\.js', file)]
        file_paths = natsorted(file_paths)
        if file_paths[-1] == 'toc.new.js': # toc.new.jsは先頭にする
            file_paths.insert(0,file_paths.pop(-1))

        lines = []
        tips = []

        # 各ファイルの内容を代入
        for idx, file in enumerate(file_paths):
            f_path = os.path.join(base_dir, file)
            with open(f_path, "r", encoding="utf_8_sig", newline="\n") as f:
                separated = re.split(r'("[a-zA-Z]+":"[^"]+)', f.read())

            for m in separated:
                if m.startswith('"name":"'):
                    table_name = m.replace('"name":"', '')
                    line = '"toc_' + table_name.replace(' ', '_') + ':' + str(idx) + '","' + table_name + '"'

                    if table_name.find('_') != -1: # 関数名と思われる行は最初から翻訳済みに
                        line += ',"' + table_name + '"'
                    else:
                        line += ',""'
                    lines.append(line)

                elif m.startswith('"url":"'):
                    tip = ',"' + m.replace('"url":"', '') + '"'
                    tips.append(tip)

        lines_noidx = [re.sub(r'(:[0-9]+",")', '","', line) for line in lines]

        # リストから書き込み文字列を生成
        new_lines = []
        for idx, line in enumerate(lines_noidx):

            if lines_noidx.count(line) >= 2: # 重複行にはjsファイルのインデックスを付加
                new_lines.append(line) # ParaTranzで更新したときの訳抜けを防ぐため、インデックスを外した行も追加
                line = lines[idx]

            new_lines.append(line + tips[idx])

        new_lines = list(dict.fromkeys(new_lines)) # 重複行を削除

        return '\n'.join(new_lines)

##############################################################################################


def main():
    root = Tk()
    frame = App(root)
    frame.pack()
    root.mainloop()

if __name__ == '__main__':
    main()
