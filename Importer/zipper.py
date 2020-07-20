import shutil
import filecmp
import os
import zipfile

zip_root = './GMS2_Japanese-master'
old_zip = './GMS2_Japanese-master.zip'
new_zip = './Converted/GMS2_Japanese-master'

zip_ex_root = './GMS2_Japanese_Alt-master'
old_ex_zip = './GMS2_Japanese_Alt-master.zip'
new_ex_zip = './Converted/GMS2_Japanese_Alt-master'


def zipper(root_dir, old_path, new_path):

    if not os.path.exists(root_dir):
        return

    shutil.make_archive(new_path, 'zip', root_dir=root_dir) # マニュアルの内容をアーカイブ化

    new_path = new_path + '.zip'

    if os.path.isfile(old_path): # 古いアーカイブの存在確認
        
        l_old = []
        l_new = []

        with zipfile.ZipFile(old_path) as zip_file:
            infos = zip_file.infolist()

            for info in infos:
                l_old.append(zip_file.read(info.filename))


        with zipfile.ZipFile(new_path) as zip_file:
            infos = zip_file.infolist()

            for info in infos:
                l_new.append(zip_file.read(info.filename))


        if set(l_old) == set(l_new): # 古いアーカイブと内容が同じだったため削除
            print('{0} is the same zip file as the old one. No changes were detected.'.format(os.path.split(new_path)[1]))
            os.remove(new_path)

    return

if __name__ == '__main__':

    zipper(zip_root, old_zip, new_zip)
    zipper(zip_ex_root, old_ex_zip, new_ex_zip)
