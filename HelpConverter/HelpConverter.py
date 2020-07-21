from tkinter import *
import tkinter.filedialog, tkinter.messagebox
import os
import shutil
import zipfile
import urllib.parse
from pathlib import Path
from translate.convert.html2po import converthtml
from translate.convert.po2csv import convertcsv

title = 'HelpConverter for GMS2 - 1.30'

# DnDアクション、Event名のラベルに対訳表示用のタグを追加するかどうか
c_translation_evnames = True
ev_dirname = 'source/_build/2_interface/1_editors/events'
dnd_dirname = 'source/_build/3_scripting/2_drag_and_drop_reference'

ignore_files_path = './ignore_files.txt'
last_used_path = './last_used.txt'

dir_name_output = 'output'
dir_name_tmp = os.path.join('tmp', 'YoYoStudioHelp')

dir_name_docs = 'docs'
dir_name_override = 'override/docs'
dir_name_override_ex = 'override_extra/docs'
dir_name_po = 'po'
dir_name_csv = 'csv'
dir_name_source_html = 'tr_sources/source_html'
dir_name_source_pot = 'tr_sources/source_pot'
dir_name_source_csv = 'tr_sources/source_csv'

po_replace_fullpath_key = [
re.compile(r'^#: [^\r\n]+%5CYoYoStudioHelp%5'), r'#: YoYoStudioHelp%5',
re.compile(r'^msgctxt [^\r\n]+YoYoStudioHelp\\'), r'msgctxt "YoYoStudioHelp\\'
]


csv_source_remove_key = [re.compile(r'("location","source","target"[\r\n]+)')]

csv_source_protect_key = [
re.compile(r'("?[^"\r\n]+\.html\+[^:]+:[0-9]+\-[0-9]+[",]+online documentation, web online help, web help, chm2web[^\r\n]+[\r\n]+)'),
re.compile(r'("?[^"\r\n]+\.html\+[^:]+:[0-9]+\-[0-9]+[",]+\(function\(i,s,o,g,r,a,m\){i\[\'GoogleAnalyticsObject\'\][^\r\n]+[\r\n]+)')
]


lastused_data = []

def create_last_used_txt():
    with open(last_used_path, "w+") as f:
        entries = ['import_path=:...', 'export_path=:...', 'en_url=:https://docs2.yoyogames.com/', 'jp_url=:', 'gms_version=:0', 'simplified=:True', 'add_url=:False']
        lines = '\n'.join(entries)
        f.write(lines)
    return

def set_lastused_data():

    result = []

    f = open(last_used_path, 'r')

    while True:
        line = f.readline()
        line = line.rstrip('\n')
        if line:
            result.append(line)
        else:
            break
    f.close()

    return result


class App(tkinter.Frame):

    def __init__(self, root):
        super().__init__(root, height=680, width=680)
        root.title(title)


        self.s_import = StringVar(value=self.readlastused('import_path'))
        self.s_export = StringVar(value=self.readlastused('export_path'))
        self.b_add_url = BooleanVar(value=self.readlastused('add_url'))
        self.s_en_url = StringVar(value=self.readlastused('en_url'))
        self.s_jp_url = StringVar(value=self.readlastused('jp_url'))
        self.b_simple_structure = BooleanVar(value=self.readlastused('simplified'))
        self.i_gmsversion = IntVar(value=self.readlastused('gms_version'))


        l_import_path = Label(root, text = 'YoYoStudioHelp.zip:\n[../GameMaker Studio 2/chm2web/YoYoStudioHelp.zip]')
        e_import_path = Entry(textvariable = self.s_import)
        b_import_path = Button(root, text = 'パスを指定', command = self.SetImportPath)

        l_export_path = Label(root, text = '出力先:\n[変換されたcsv/potファイルの出力先]')
        e_export_path = Entry(textvariable = self.s_export)
        b_export_path = Button(root, text = 'パスを指定', command = self.SetExportPath)

        l_gms_version = Label(root, text = 'GMS2のバージョン（小数点なしのメジャーVer）')
        e_gms_version = Entry(textvariable = self.i_gmsversion)

        c_add_url = Checkbutton(root, variable = self.b_add_url, text='コンテキストにURLを追加')

        l_en_url = Label(root, text = '英語版マニュアルのURL:')
        e_en_url = Entry(textvariable = self.s_en_url)
        l_jp_url = Label(root, text = '日本語版マニュアルのURL:')
        e_jp_url = Entry(textvariable = self.s_jp_url)

        c_simple_structure = Checkbutton(root, variable = self.b_simple_structure, text='ディレクトリ構成を簡易化')

        b_run = Button(root, text = '変換開始', padx = 50, command = self.Run)

        self.lb = Listbox(root)

        sb1 = Scrollbar(root, orient = 'v', command = self.lb.yview)
        sb2 = Scrollbar(root, orient = 'h', command = self.lb.xview)

        self.lb.configure(yscrollcommand = sb1.set)
        self.lb.configure(xscrollcommand = sb2.set)

        l_import_path.place(rely=0, relwidth=1.0)
        e_import_path.place(rely=0.07, relx=0.02, relwidth=0.84)
        b_import_path.place(rely=0.06, relx=0.87, width=80)
        l_export_path.place(rely=0.11, relwidth=1.0)
        e_export_path.place(rely=0.18, relx=0.02, relwidth=0.84)
        b_export_path.place(rely=0.17, relx=0.87, width=80)

        l_gms_version.place(rely=0.25, relx=0.20)
        e_gms_version.place(rely=0.25, relx=0.615, width=50)
        c_simple_structure.place(rely=0.30, relx=0.20)
        c_add_url.place(rely=0.30, relx=0.50)

        l_en_url.place(rely=0.35, relwidth=1.0)
        e_en_url.place(rely=0.40, relx=0.04, relwidth=0.81)
        l_jp_url.place(rely=0.45, relwidth=1.0)
        e_jp_url.place(rely=0.50, relx=0.04, relwidth=0.81)

        b_run.place(rely=0.55, relx=0.35, width=150)
        self.lb.place(rely=0.62, relx=0.02, relwidth=0.84, relheight=0.3)
        sb1.place(rely=0.62, relx=0.9, relheight=0.3)
        sb2.place(rely=0.95, relx=0.02, relwidth=0.84)


    def writelastused(self):

        key = ['import_path', 'export_path', 'add_url', 'en_url', 'jp_url', 'simplified', 'gms_version']
        val = [self.s_import.get(), self.s_export.get(), self.b_add_url.get(), self.s_en_url.get(), self.s_jp_url.get(), self.b_simple_structure.get(), self.i_gmsversion.get()]

        lines = ''
        with open(last_used_path, "r") as f:

            while True:
                line = f.readline()
                if line:
                    separated = re.split('=:', line)

                    for idx in range(len(key)):

                        if separated[0] == key[idx]:
                            separated[1] = val[idx]

                    line = '=:'.join(map(str, separated))
                    lines += line + '\n'
                else:
                    break

        if lines:
            with open(last_used_path, "w") as f:
                f.write(lines)

        return

    def readlastused(self, key):

        global lastused_data

        for line in lastused_data:
            separated = re.split('=:', line)
            if separated[0] == key:
                return separated[1]
        return


    def SetImportPath(self):
        fTyp = [("","*.zip")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        val = tkinter.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)
        val = val.replace('/', os.sep)
        self.s_import.set(str(val))

    def SetExportPath(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        val = tkinter.filedialog.askdirectory(initialdir = iDir)
        val = val.replace('/', os.sep)
        self.s_export.set(str(val))


    def format_html(self, lines, base_dir): # HTMLの整形

        # 目印としてコード行に識別子を挿入
        lines = re.sub(r'(<[^<]+class="code"[^>]*>)', r'\1{ANY_CODE} ', lines)

        # 目印として画像のテキスト情報に識別子を挿入
        lines = re.sub(r'(alt=[\r\n]*")([^>]+">)', r'\1{IMG_TXT} \2', lines)

        # 対訳を付加するエントリにタグを挿入
        if c_translation_evnames:
            if dnd_dirname in base_dir:
                # lines = re.sub(r'(<td class="text"><a href=[^>]+>)([^<]+)', r'\1{CTR_N} \2', lines)
                lines = re.sub(r'(<h2><img style="vertical-align:middle" src=[^>]+>)([^<]+)', r'\1{CTR_S}\2', lines)
            # elif ev_dirname in base_dir:
            #     lines = re.sub(r'(<label class="collapse"[^>]+>)([^<]+)</label>', r'\1\2</label>', lines)

        # ノーブレークスペースをダミータグに置換
        new_lines = ''
        separated = re.split(r'((&nbsp;)+)', lines)
        pre_match = False

        for m in separated:

            if pre_match:
                pre_match = False
                continue

            elif '&nbsp;' in m:
                cnt = m.count('&nbsp;')
                m = re.sub(r'((&nbsp;)+)', '{nbsp_x' + str(cnt) + '}', m)
                pre_match = True

            new_lines += m

        # 絶対URLのドットをダミータグに変換（ParaTranzでの誤ページ移動防止およびクリックでのコピーに対応）
        matched = re.findall(r'(<a href=[\r\n]*"https?://[^\/]+/)', new_lines)
        matched = list(set(matched)) # 重複したエントリを削除
        for m in matched:
            replaced = m.replace('.', '{-dot-}')
            new_lines = new_lines.replace(m, replaced)

        return new_lines

    def format_po(self, lines): # POの整形

        new_lines = ''
        separated = lines.splitlines(True)
        pat = [re.compile(r'^#: ([^\r\n]+)$'), re.compile(r'^msgctxt ([^\r\n]+)$')]

        for m in separated:
            # 文字列位置のパスを相対パスに整形
            m = re.sub(po_replace_fullpath_key[0], po_replace_fullpath_key[1], m)
            m = re.sub(po_replace_fullpath_key[2], po_replace_fullpath_key[3], m)

            if pat[0].match(m):
                m = m.replace('/', '%5C') # スラッシュをurlエンコード
            if pat[1].match(m):
                m = m.replace('/', os.sep + os.sep) # スラッシュを\\に置き換え

            new_lines += m

        return new_lines

    def format_csv(self, lines, base_dir, filename, again): # CSVの整形

        if again == False:
            # ParaTranzでのエラー防止のため、キーのディレクトリ名をすべて省略してファイル名のみにする（Importerで復元）
            lines = re.sub(r'"YoYoStudioHelp\\([^"\r\n]+\\)*', '"', lines)

            # 不要なエントリを削除
            for key_val in csv_source_remove_key:
                lines = re.sub(key_val, '', lines)

            # 不要なエントリをコメントアウト
            for key_val in csv_source_protect_key:
                lines = re.sub(key_val, r'#CSV_COMMENT_OUT#\1', lines)

            # コンテキストにURL情報をセット
            if self.b_add_url.get() == True:
                url_dir = ''
                if base_dir:
                    url_dir = base_dir + '/'
                urls = [(self.s_en_url.get() + url_dir + os.path.split(filename)[1]), (self.s_jp_url.get() + url_dir + os.path.split(filename)[1])]
                context = r',"URL_EN : ' + urls[0] + r' \\n\\nURL_JP : ' + urls[1] + '"'

                lines = re.sub(r'(^|[\r\n])([^#][^\r\n]+)', r'\1\2' + context, lines)

        else:
            # コメントアウトしたエントリを除外
            lines = re.sub(r'#CSV_COMMENT_OUT#[^\r\n]+[\r\n]+', '', lines)

        return lines


    def Run(self):

        import_path = self.s_import.get()
        export_path = self.s_export.get()

        url_en = self.s_en_url.get()
        url_jp = self.s_jp_url.get()
        url_is_add = self.b_add_url.get()

        gms_version = self.i_gmsversion.get()

        if import_path == '...' or import_path == '':
            tkinter.messagebox.showinfo('アーカイブが未指定', 'アーカイブのパスが指定されていません。\nGame Maker Studio 2 のインストールディレクトリにある chm2web/YoYoStudioHelp.zip を指定してください。')
            return
        elif not os.path.isfile(import_path):
            tkinter.messagebox.showinfo('無効なアーカイブ', 'アーカイブが存在しない、または無効なアーカイブです。\nGame Maker Studio 2 のインストールディレクトリにある chm2web/YoYoStudioHelp.zip を指定してください。')
            return
        elif not os.path.isfile(ignore_files_path):
            tkinter.messagebox.showinfo('エラー', '無視ファイルリスト（ignore_files.txt）が存在しません。')
            return

        if not os.path.isfile(ignore_files_path):
            tkinter.messagebox.showinfo('エラー', '無視ファイルリスト（ignore_files.txt）が存在しません。')
            return

        if export_path == '...' or export_path == '':
            export_path = os.getcwd()
            self.s_export.set(str(export_path))

        if url_is_add == True:
            en_parse = urllib.parse.urlparse(url_en)
            jp_parse = urllib.parse.urlparse(url_jp)

            if url_en == '':
                tkinter.messagebox.showinfo('エラー', '英語版マニュアルのURLが指定されていません。\nURLを指定し直すか、チェックを外してください。')
                return
            elif len(en_parse.netloc) == 0 or (en_parse.scheme != 'http' and en_parse.scheme != 'https'):
                tkinter.messagebox.showinfo('エラー', '英語版マニュアルのURLが不正です。\nhttps://url/ 形式で指定する必要があります。\nURLを指定し直すか、チェックを外してください。')
                return
            elif url_jp == '':
                tkinter.messagebox.showinfo('エラー', '日本語版マニュアルのURLが指定されていません。\nURLを指定し直すか、チェックを外してください。')
                return
            elif len(jp_parse.netloc) == 0 or (jp_parse.scheme != 'http' and jp_parse.scheme != 'https'):
                tkinter.messagebox.showinfo('エラー', '日本語版マニュアルのURLが不正です。\nhttps://url/ 形式で指定する必要があります。\nURLを指定し直すか、チェックを外してください。')
                return
            elif gms_version == 0:
                tkinter.messagebox.showinfo('エラー', 'バージョン情報が空です。\nGMS本体のバージョンを小数点なしで指定してください。\n（例: 2.2.5.378 > 225）')
                return


        # 無視するファイルを追加
        ignore_files = []
        f = open(ignore_files_path, 'r')

        while True:
            line = f.readline()
            line = line.rstrip('\n')
            if line:
                ignore_files.append(line)
            else:
                break
        f.close()

        self.writelastused()
        self.lb.delete(0, tkinter.END)

        # 各ディレクトリのパスを定義
        export_path = os.path.join(export_path, dir_name_output)
        override_dir = os.path.join(export_path, dir_name_override)
        override_ex_dir = os.path.join(export_path, dir_name_override_ex)
        html_output_dir = os.path.join(export_path, dir_name_source_html)
        tmp_output_dir = os.path.join(export_path, dir_name_tmp)
        # pot_output_dir = os.path.join(export_path, dir_name_source_pot)
        po_output_dir = os.path.join(export_path, dir_name_po)
        csv_output_dir = os.path.join(export_path, dir_name_csv)
        source_csv_output_dir = os.path.join(export_path, dir_name_source_csv)
        docs_output_dir = os.path.join(export_path, dir_name_docs)
        zip_output_dir = os.path.join(export_path, os.path.splitext(os.path.split(import_path)[1])[0])

        if os.path.exists(csv_output_dir):
            shutil.rmtree(csv_output_dir)

        if os.path.exists(source_csv_output_dir):
            shutil.rmtree(source_csv_output_dir)


        # アーカイブの展開を開始
        with zipfile.ZipFile(import_path) as zip_file:
            infos = zip_file.infolist() # 各メンバのオブジェクトをリストとして返す
            export_count = 0 # ファイル処理数

            for info in infos:
                passed = False

                if re.match(r'.*/$', info.filename): # ディレクトリは除外
                    continue

                if re.match(r'.*.html$', info.filename) is None:
                    passed = True

                # 無視するファイルを検索
                if passed == False:
                    for ignore in ignore_files:
                        if re.match(ignore, info.filename):
                            passed = True
                            continue

                # 基本パス
                base_dir = os.path.join(os.path.split(info.filename)[0])


                # 翻訳対象ファイルでないためdocs（GitHub Pagesのディレクトリ）にコピー
                if passed == True:
                    path_others = os.path.join(export_path, docs_output_dir, base_dir, os.path.split(info.filename)[1])

                    if os.path.dirname(path_others) != '':
                        os.makedirs(os.path.dirname(path_others), exist_ok=True)

                    with open(path_others, "wb+") as f:
                        f.write(zip_file.read(info.filename))
                    continue

                export_count += 1


                # ソースHTMLを別ディレクトリにコピー
                path_html = os.path.join(export_path, zip_output_dir, base_dir, os.path.split(info.filename)[1])

                if os.path.dirname(path_html) != '':
                    os.makedirs(os.path.dirname(path_html), exist_ok=True)

                with open(path_html, "wb+") as f_html:
                    f_html.write(zip_file.read(info.filename))


                # HTMLの整形

                with open(path_html, "r", encoding="utf_8_sig", newline="\n") as f_html:
                    html_lines = self.format_html(f_html.read(), base_dir)
                with open(path_html, "w+", encoding="utf_8_sig", newline="\n") as f_html:
                    f_html.write(html_lines)


                # HTML > POファイルの変換処理
                path_pot = os.path.join(export_path, dir_name_source_pot, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.pot'
                path_po = os.path.join(export_path, dir_name_po, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.po'

                if not os.path.exists(os.path.split(path_po)[0]):
                    os.makedirs(os.path.split(path_po)[0])
                if not os.path.exists(os.path.split(path_pot)[0]):
                    os.makedirs(os.path.split(path_pot)[0])

                f_input = open(path_html, 'rb')
                f_output = open(path_po, 'wb+')
                f_template = open(path_pot, 'wb+')

                converthtml(inputfile=f_input, outputfile=f_output, templates=f_template, pot=True, keepcomments=True) # HTML から PO に変換

                f_input.close()
                f_output.close()
                f_template.close()


                # POの整形
                with open(path_po, "r", encoding="utf_8_sig", newline="\n") as f_po:
                    po_lines = self.format_po(f_po.read())
                with open(path_po, "w", encoding="utf_8_sig",newline="\n") as f_po:
                    f_po.write(po_lines)


                # Translate-Kit 3.0.0現在、空のPOTファイルが出力されてしまうためPOの内容をPOTに上書き
                with open(path_pot, "w", encoding="utf_8_sig",newline="\n") as f_po:
                    f_po.write(po_lines)


                # CSVファイルの出力先を生成
                path_source_csv = ''
                path_csv = ''

                if self.b_simple_structure.get(): # ディレクトリ構成の簡易化がチェックされている場合

                    separated = []
                    separated = re.findall(r'^source/_build/([^/]+/?)(2_drag_and_drop_reference/|4_gml_reference/)?(.*)', base_dir)
                    new_path = []

                    if separated:

                        new_path.append('source/_build/')
                        idx = 0
                        for item in separated[0]:
                            if idx > 0 and item != '2_drag_and_drop_reference/' and item != '4_gml_reference/':
                                item = item.replace('/', '／')
                            new_path.append(item)
                            idx += 1

                        # ParaTranzでの取り回しを良くするため、深層のディレクトリをファイル名に置き換え
                        path_csv = ''.join(new_path) + '／'
                        path_csv = os.path.join(export_path, dir_name_csv, path_csv) + os.path.splitext(os.path.split(info.filename)[1])[0] + '.csv'

                if path_csv == '':
                    path_csv = os.path.join(export_path, dir_name_csv, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.csv'

                path_source_csv = os.path.join(export_path, dir_name_source_csv, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.csv'


                # PO > CSV ファイルの変換処理
                if not os.path.exists(os.path.split(path_source_csv)[0]):
                    os.makedirs(os.path.split(path_source_csv)[0])

                f_po = open(path_po, 'rb')
                f_csv = open(path_source_csv, 'wb+')
                f_template = open(path_html, 'r') # 実際には未使用であるものの、動作のためにテンプレートを指定する必要あり

                convertcsv(f_po, f_csv, f_template) # PO から CSV に変換

                f_po.close()
                f_csv.close()
                f_template.close()


                # ソースCSVの書き出し
                with open(path_source_csv, "r", encoding="utf_8_sig") as f_csv:
                    csv_lines = self.format_csv(f_csv.read(), base_dir, info.filename, False)
                with open(path_source_csv, "w", encoding="utf_8_sig") as f_csv:
                    f_csv.write(csv_lines)

                # CSVの書き出し
                if not os.path.exists(os.path.split(path_csv)[0]):
                    os.makedirs(os.path.split(path_csv)[0])

                with open(path_csv, "w+", encoding="utf_8_sig") as f_csv:
                    # コメントアウトされたエントリを除外
                    csv_lines = self.format_csv(csv_lines, base_dir, info.filename, True)
                    f_csv.write(csv_lines)


                # リストボックスにログを出力
                path_csv = path_csv.replace('/', os.sep) # スラッシュを\\に置き換え
                self.lb.insert('end', path_csv)
                self.lb.see('end')

                if export_count % 10 == 0: # 10ファイル処理したらアップデート
                    self.update()


        if not os.path.exists(override_dir):
            os.makedirs(override_dir)

        if not os.path.exists(override_ex_dir):
            os.makedirs(override_ex_dir)

        # バージョンファイルを生成

        version_path = os.path.join(export_path, '_VERSION')
        with open(version_path, "w+") as f:
            lines = str(gms_version)
            f.write(lines)

        # .nojekyllを生成
        jerky_path = os.path.join(override_dir, '.nojekyll')
        with open(jerky_path, "w+") as f:
            f.write('')

        # .gitkeepを生成
        gitkeep_path = os.path.join(override_ex_dir, '.gitkeep')
        with open(gitkeep_path, "w+") as f:
            f.write('')

        # 不要となったディレクトリを削除
        if os.path.exists(tmp_output_dir):
            shutil.rmtree(tmp_output_dir)
        if os.path.exists(html_output_dir):
            shutil.rmtree(html_output_dir)
        os.rename(zip_output_dir, html_output_dir) 
        shutil.rmtree(po_output_dir)

        tkinter.messagebox.showinfo('変換完了','CSV, POT ファイルへの変換が完了しました。')
        return


def main():

    if not os.path.isfile(last_used_path):
        create_last_used_txt()

    global lastused_data
    lastused_data = set_lastused_data()

    root = Tk()
    frame = App(root)
    frame.pack()
    root.mainloop()

if __name__ == '__main__':
    main()
