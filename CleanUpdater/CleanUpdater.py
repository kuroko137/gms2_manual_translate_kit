from tkinter import *
import tkinter.filedialog, tkinter.messagebox
import os
import shutil
import filecmp
from pathlib import Path

title = 'Clean Updater for GMS2 Manual - 1.00'

user_settings_path = 'user_settings.ini' # オプションの設定履歴
log_path = 'log.txt'
log_paratranz_path = 'log_paratranz.txt'

log_data = []
log_paratranz_data = []

######################################################################################

class user_settings: # オプションの設定履歴
    def __init__(self):
        self.defaults = [['extracted_path', ''], ['repository_path', '']]
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

class App(tkinter.Frame):

    def __init__(self, root):
        super().__init__(root, height=500, width=600)
        root.title(title)

        self.lastused = user_settings()
        self.lastused.create_txt()
        self.lastused.generate_list()

        self.w_extracted_path = StringVar(value=self.lastused.read_by_key('extracted_path'))
        self.w_repository_path = StringVar(value=self.lastused.read_by_key('repository_path'))

        # ウィジェットの作成
        l_extracted_path = Label(root, text = 'HelpConverterの出力先:\n[../output]')
        e_extracted_path = Entry(textvariable = self.w_extracted_path)
        b_extracted_path = Button(root, text = 'パスを指定', command = self.SetExtractedPath)

        l_repository_path = Label(root, text = 'ローカルリポジトリの場所:\n[../リポジトリ名]')
        e_repository_path = Entry(textvariable = self.w_repository_path)
        b_repository_path = Button(root, text = 'パスを指定', command = self.SetRepositoryPath)

        b_run = Button(root, text = 'アップデートを開始', padx = 50, command = self.Run)

        self.lb = Listbox(root)

        sb1 = Scrollbar(root, orient = 'v', command = self.lb.yview)
        sb2 = Scrollbar(root, orient = 'h', command = self.lb.xview)

        self.lb.configure(yscrollcommand = sb1.set)
        self.lb.configure(xscrollcommand = sb2.set)

        # ウィジェットを配置
        l_extracted_path.place(rely=0, relwidth=1.0)
        e_extracted_path.place(rely=0.08, relx=0.03, relwidth=0.83)
        b_extracted_path.place(rely=0.075, relx=0.87, width=80)
        l_repository_path.place(rely=0.15, relwidth=1.0)
        e_repository_path.place(rely=0.228, relx=0.03, relwidth=0.83)
        b_repository_path.place(rely=0.220, relx=0.87, width=80)
        b_run.place(rely=0.35, relx=0.30, width=200)

        self.lb.place(rely=0.45, relx=0.02, relwidth=0.84, relheight=0.45)
        sb1.place(rely=0.45, relx=0.9, relheight=0.5)
        sb2.place(rely=0.95, relx=0.02, relwidth=0.84)


    def SetExtractedPath(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        val = tkinter.filedialog.askdirectory(initialdir = iDir)
        val = val.replace('/', os.sep)
        self.w_extracted_path.set(str(val))
        return

    def SetRepositoryPath(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        val = tkinter.filedialog.askdirectory(initialdir = iDir)
        val = val.replace('/', os.sep)
        self.w_repository_path.set(str(val))
        return


    def Run(self):
        ext_path = self.w_extracted_path.get()
        repo_path = self.w_repository_path.get()

        global log_data
        global log_paratranz_data

        if not os.path.exists(ext_path) or not os.path.exists(repo_path):
            tkinter.messagebox.showinfo('アーカイブが未指定', 'アーカイブのパスが正しく指定されていません。')
            return

        version_path = os.path.join(ext_path, 'repository', '_VERSION')
        if not os.path.exists(version_path):
            tkinter.messagebox.showinfo('エラー', '_VERSIONファイルが見つかりません。')
            return
        else:
            with open(version_path, "r") as f:
                VERSION = f.readline()
                msg = '[--VERSION_{0}--]'.format(VERSION)
                log_data.append(msg)
                log_paratranz_data.append(msg)

        if not tkinter.messagebox.askokcancel(title="HelpConverterの出力ファイルをコピー", message="ローカルリポジトリに新バージョンのファイルをコピーします。\n変更のあるファイルのみコピーされ、新バージョンで消されたファイルは\nリポジトリでも削除されます。"):
            return

        self.lb.delete(0, tkinter.END) # ログの表示をクリア

        # -----------------------------------------------------------------------

        # 現在の設定をテキストに書き出し
        self.lastused.write_txt(ext_path, repo_path)

        udir = update_dir(self)
        udir.file_copy([os.path.join(ext_path, 'repository', 'tr_sources'), os.path.join(repo_path, 'tr_sources')], mode='Override')
        udir.file_copy([os.path.join(ext_path, 'paratranz', 'csv'), os.path.join(repo_path, 'generated', 'manual', 'csv')], mode='ParaTranz')

        os.makedirs('tmp', exist_ok=True)
        shutil.copytree(os.path.join(ext_path, 'repository', 'docs'), 'tmp', dirs_exist_ok=True)
        shutil.copytree(os.path.join(ext_path, 'repository', 'tr_sources', 'source_html'), 'tmp', dirs_exist_ok=True)
        udir.file_copy([os.path.join('tmp'), os.path.join(repo_path, 'docs')], mode='NoOverride')

        shutil.rmtree('tmp', ignore_errors=True)

        self.lb.insert('end', 'complete.')
        self.lb.see('end')
        self.update()
        tkinter.messagebox.showinfo('コピー完了', 'ローカルリポジトリに新バージョンのファイルをコピーしました。')

        if len(log_data) > 1:
            with open(log_path, "w+", encoding="utf_8_sig") as f:
                f.write('\n'.join(log_data))

        if len(log_paratranz_data) > 1:
            with open(log_paratranz_path, "w+", encoding="utf_8_sig") as f:
                f.write('\n'.join(log_paratranz_data))

        return

class update_dir():
    def __init__(self, root):
        self.root = root
        return

    def file_copy(self, base_path, mode=''):

        global log_data
        global log_paratranz_data

        source_files = {}

        source_dir = os.path.join(base_path[0])
        for current, subfolders, subfiles in os.walk(source_dir):
            for file in subfiles:
                path = os.path.join(current, file)
                key = path.replace(source_dir + os.sep, '')
                source_files[key] = path

        dest_files = {}

        dest_dir = os.path.join(base_path[1])
        for current, subfolders, subfiles in os.walk(dest_dir):
            for file in subfiles:
                path = os.path.join(current, file)
                key = path.replace(dest_dir + os.sep, '')
                dest_files[key] = path

                if source_files.get(key, ''):

                    if mode == 'Override' and not filecmp.cmp(source_files.get(key, ''), path):
                        shutil.copy2(source_files.get(key, ''), path)
                        msg = 'override file "{0}" of "{1}"'.format(os.path.basename(path), path)
                        self.root.lb.insert('end', msg)
                        self.root.lb.see('end')
                        self.root.update()
                        log_data.append(msg)
                else:
                    os.remove(path)
                    msg = 'remove file "{0}" of "{1}"'.format(os.path.basename(path), path)
                    self.root.lb.insert('end', msg)
                    self.root.lb.see('end')
                    self.root.update()
                    log_data.append(msg)
                    if mode == 'ParaTranz':
                        log_paratranz_data.append('要削除: "{0}"'.format(key))

        if mode != 'RemoveOnly':
            for k in source_files:
                if not dest_files.get(k, ''):
                    shutil.copy2(source_files.get(k, ''), os.path.join(dest_dir, k))
                    msg = 'copy file "{0}" to "{1}"'.format(os.path.basename(source_files.get(k, '')), os.path.join(dest_dir, k))
                    self.root.lb.insert('end', msg)
                    self.root.lb.see('end')
                    self.root.update()
                    log_data.append(msg)

        return

##############################################################################################


def main():
    root = Tk()
    frame = App(root)
    frame.pack()
    root.mainloop()

if __name__ == '__main__':
    main()
