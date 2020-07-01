import shutil
import filecmp
import os
import zipfile

zip_root = './GMS2_Japanese-master'
new_zip = './Converted/GMS2_Japanese-master'
old_zip = './GMS2_Japanese-master.zip'


if __name__ == '__main__':
    shutil.make_archive(new_zip, 'zip', root_dir=zip_root)

    new_zip = new_zip + '.zip'

    if os.path.isfile(old_zip):
        
        l_old = []
        l_new = []

        with zipfile.ZipFile(old_zip) as zip_file:
            infos = zip_file.infolist()

            for info in infos:
                l_old.append(zip_file.read(info.filename))


        with zipfile.ZipFile(new_zip) as zip_file:
            infos = zip_file.infolist()

            for info in infos:
                l_new.append(zip_file.read(info.filename))


        if set(l_old) == set(l_new):  
            print('This is the same zip file as the old one. No changes were detected.')
            os.remove(new_zip)
