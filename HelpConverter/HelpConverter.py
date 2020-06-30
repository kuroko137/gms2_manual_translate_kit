from tkinter import *
import tkinter.filedialog, tkinter.messagebox
import os
import shutil
import zipfile
from pathlib import Path
from translate.convert.html2po import converthtml
from translate.convert.po2csv import convertcsv


ignore_files_path = './ignore_files.txt'

dir_name_output = 'output'
dir_name_docs = 'docs'
dir_name_html = 'source_html'
dir_name_pot = 'source_pot'
dir_name_po = 'po'
dir_name_csv = 'csv'

po_replace_fullpath_key = [
r'^#: [^\r\n]+%5CYoYoStudioHelp%5', r'#: YoYoStudioHelp%5',
r'^msgctxt [^\r\n]+YoYoStudioHelp\\', r'msgctxt "YoYoStudioHelp\\',
]

po_remove_key = [
r'#: YoYoStudioHelp%5Csource%5[^\n]+[\r\n]+msgid "online documentation, web online help, web help, chm2web"[\r\n]+msgstr ""[\r\n]+', 
r'#: YoYoStudioHelp%5Csource%5C_build%5Cindex\.html%2Bhtml\.body\.div:463\-57(\n|\r\n)msgid ""(\n|\r\n)"\(function\(i,s,o,g,r,a,m\)\{i\[\'GoogleAnalyticsObject\'\]=r;i\[r\]=i\[r\]\|\|function\(\)\{ "(\n|\r\n)"\(i\[r\]\.q=i\[r\]\.q\|\|\[\]\)\.push\(arguments\)\},i\[r\]\.l=1\*new Date\(\);a=s\.createElement\(o\)"(\n|\r\n)", m=s\.getElementsByTagName\(o\)\[0\];a\.async=1;a\.src=g;m\.parentNode\."(\n|\r\n)"insertBefore\(a,m\) \}\)\(window,document,\'script\',\'https:\/\/www\.google\-analytics\."(\n|\r\n)"com\/analytics\.js\',\'ga\'\); ga\(\'create\', \'UA\-2711665\-14\', \'auto\'\); ga\(\'send\', "(\n|\r\n)"\'pageview\'\);"(\n|\r\n)msgstr ""(\n|\r\n)'
]

csv_remove_key = [r'"location","source","target"[\r\n]+']



class App(tkinter.Frame):

    def __init__(self, root):
        super().__init__(root)

        self.s_import = StringVar(value='...')
        self.s_export = StringVar(value='...')

        l_import_path = Label(root, text = 'YoYoStudioHelp.zip:\n[../GameMaker Studio 2/chm2web/YoYoStudioHelp.zip]')
        e_import_path = Entry(width = 80, textvariable = self.s_import)
        b_import_path = Button(root, text = 'パスを指定', padx = 5, command = self.SetImportPath)

        l_export_path = Label(root, text = '出力先:\n[変換されたcsv/potファイルの出力先]')
        e_export_path = Entry(width = 80, textvariable = self.s_export)
        b_export_path = Button(root, text = 'パスを指定', padx = 5, command = self.SetExportPath)

        b_run = Button(root, text = '変換開始', padx = 50, command = self.Run)

        self.lb = Listbox(root, height = 15)

        sb1 = Scrollbar(root, orient = 'v', command = self.lb.yview)
        sb2 = Scrollbar(root, orient = 'h', command = self.lb.xview)

        self.lb.configure(yscrollcommand = sb1.set)
        self.lb.configure(xscrollcommand = sb2.set)

        l_import_path.grid(row = 0, column = 0, sticky = 'nsew', padx = 10)
        e_import_path.grid(row = 1, column = 0, padx = 10, pady = 5)
        b_import_path.grid(row = 1, column = 1, padx = 5, pady = 5)
        l_export_path.grid(row = 2, column = 0, sticky = 'nsew', padx = 10)
        e_export_path.grid(row = 3, column = 0, padx = 10, pady = 5)
        b_export_path.grid(row = 3, column = 1, padx = 5, pady = 5)
        b_run.grid(row = 4, column = 0, padx = 50, pady = 10)
        self.lb.grid(row = 6, column = 0, sticky = 'nsew', padx = 10, pady = 30)
        sb1.grid(row = 6, column = 1, sticky = 'ns', padx = 10)
        sb2.grid(row = 7, column = 0, sticky = 'ew', padx = 10)


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


    def Run(self):

        import_path = self.s_import.get()
        export_path = self.s_export.get()

        if import_path == '...' or import_path == '':
            tkinter.messagebox.showinfo('アーカイブが未指定', 'アーカイブのパスが指定されていません。\nGame Maker Studio 2 のインストールディレクトリにある chm2web/YoYoStudioHelp.zip を指定してください。')
            return
        elif not os.path.isfile(import_path):
            tkinter.messagebox.showinfo('無効なアーカイブ', 'アーカイブが存在しない、または無効なアーカイブです。\nGame Maker Studio 2 のインストールディレクトリにある chm2web/YoYoStudioHelp.zip を指定してください。')
            return
        elif not os.path.isfile(ignore_files_path):
            tkinter.messagebox.showinfo('エラー', '無視ファイルリスト（ignore_files.txt）が存在しません。')
            return

        if export_path == '...' or export_path == '':
            export_path = os.getcwd()
            self.s_export.set(str(export_path))

        export_path = os.path.join(export_path, dir_name_output)

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

        html_output_dir = os.path.join(export_path, dir_name_html)
        pot_output_dir = os.path.join(export_path, dir_name_pot)
        po_output_dir = os.path.join(export_path, dir_name_po)
        csv_output_dir = os.path.join(export_path, dir_name_csv)
        docs_output_dir = os.path.join(export_path, dir_name_docs)
        zip_output_dir = os.path.join(export_path, os.path.splitext(os.path.split(import_path)[1])[0])

        with zipfile.ZipFile(import_path) as zip_file:
            infos = zip_file.infolist() # 各メンバのオブジェクトをリストとして返す
            count = 0

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

                # 翻訳対象ファイルでないためdocsにコピー
                if passed == True:
                    path_others = os.path.join(export_path, docs_output_dir, base_dir, os.path.split(info.filename)[1])

                    if os.path.dirname(path_others) != '':
                        os.makedirs(os.path.dirname(path_others), exist_ok=True)

                    with open(path_others, "wb+") as f:
                        f.write(zip_file.read(info.filename))
                    continue

                count += 1

                # HTML から PO への変換処理
                path_html = os.path.join(export_path, zip_output_dir, base_dir, os.path.split(info.filename)[1])

                if os.path.dirname(path_html) != '':
                    os.makedirs(os.path.dirname(path_html), exist_ok=True)

                with open(path_html, "wb+") as f_html:
                    f_html.write(zip_file.read(info.filename))

                path_pot = os.path.join(export_path, dir_name_pot, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.pot'
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


                # PO ファイルの整形
                with open(path_po, "r", encoding="utf-8",newline="\n") as f_po:

                    po_lines = ''
                    pat = [re.compile(r'^#: ([^\r\n]+)$'), re.compile(r'^msgctxt ([^\r\n]+)$')]

                    while True:
                        line = f_po.readline()
                        # line = line.rstrip('\n')
                        if line:
                            # 文字列位置のパスを相対パスに整形
                            line = re.sub(po_replace_fullpath_key[0], po_replace_fullpath_key[1], line)
                            line = re.sub(po_replace_fullpath_key[2], po_replace_fullpath_key[3], line)

                            if pat[0].match(line):
                                line = line.replace('/', '%5C') # スラッシュをurlエンコード
                            if pat[1].match(line):
                                line = line.replace('/', os.sep + os.sep) # スラッシュを\\に置き換え

                            po_lines += line
                        else:
                            break

                    for key_val in po_remove_key:
                        # 不要なエントリを削除
                        po_lines = re.sub(key_val, '', po_lines)

                with open(path_po, "w", encoding="utf-8",newline="\n") as f_po:
                    f_po.write(po_lines)


                # Translate-Kit 3.0.0 現在、空の POT ファイルが出力されてしまうため PO の内容を POT に上書き
                with open(path_pot, "w", encoding="utf-8",newline="\n") as f_po:
                    f_po.write(po_lines)


                # PO から CSV ファイルへの変換処理
                path_csv = os.path.join(export_path, dir_name_csv, base_dir, os.path.splitext(os.path.split(info.filename)[1])[0]) + '.csv'

                if not os.path.exists(os.path.split(path_csv)[0]):
                    os.makedirs(os.path.split(path_csv)[0])

                f_po = open(path_po, 'rb')
                f_csv = open(path_csv, 'wb+')
                f_template = open(path_html, 'r') # 実際には未使用であるものの、指定する必要あり

                convertcsv(f_po, f_csv, f_template) # PO から CSV に変換

                f_po.close()
                f_csv.close()
                f_template.close()

                # CSV ファイルの整形
                with open(path_csv, "r", encoding="utf-8", newline="\n") as f_csv:
                    csv_lines = f_csv.read()
                    for key_val in csv_remove_key:
                        # 不要なエントリを削除
                        csv_lines = re.sub(key_val,'',csv_lines)
                        csv_lines = csv_lines.replace('\r', '') # 改行コードをCRLFからLFに統一

                with open(path_csv, "w+", encoding="utf-8", newline="\n") as f_csv:
                    f_csv.write(csv_lines)


                # リストボックスにログを出力
                path_csv = path_csv.replace('/', os.sep) # スラッシュを\\に置き換え
                self.lb.insert('end', path_csv)
                self.lb.see('end')

                if count % 15 == 0:
                    self.update()

        jerky_path = os.path.join(docs_output_dir, '.nojekyll')
        with open(jerky_path, "w+") as f:
            f.write('')

        if os.path.exists(html_output_dir):
            shutil.rmtree(html_output_dir)
        os.rename(zip_output_dir, html_output_dir) 
        shutil.rmtree(po_output_dir)

        tkinter.messagebox.showinfo('変換完了','CSV, POT ファイルへの変換が完了しました。')
        return


def main():
    root = Tk()
    root.title(u"HelpConverter for GMS2 - 1.00")
    root.geometry("680x600")
    frame = App(root)
    root.mainloop()

if __name__ == '__main__':
    main()
