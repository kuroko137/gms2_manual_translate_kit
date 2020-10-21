import os
import sys
import urllib.request
import json

from pathlib import Path

def main():
    file_path = 'logs/release_stats.json'

    repository_name = os.environ.get("REPOSITORY_NAME")
    request_url = "https://api.github.com/repos/{0}/releases".format(repository_name)
    print('request_url = ', request_url)

    try:
        req = urllib.request.urlopen(request_url)
    except IOError:
        print('Release not found. Aborted stats generation.')
        return

    git_d = json.loads(req.read())

    repo_d = []
    repo_ver = {}

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            repo_d = json.loads(f.read())
        repo_ver = {d: i for i, d in enumerate(sum([list(d.keys()) for d in repo_d], []))}


    output = []

    for gd in git_d:

        ver = gd.get('tag_name')
        assets = gd.get('assets')

        data_type = ['name', 'download_count', 'created_at', 'updated_at']

        new_data = {}
        new_data[ver] = [[] for i in range(len(assets))]

        for idx, asset in enumerate(assets):
            new_data[ver][idx] = {'name' : assets[idx].get('name'), 'download_count' : assets[idx].get('download_count'), 'created_at' : assets[idx].get('created_at'), 'updated_at' : assets[idx].get('updated_at')}

        names = [nd.get('name') for nd in new_data[ver]]

        ver_idx = repo_ver.get(ver)

        if len(repo_d) > 0 and ver_idx != None:
            for nd in new_data[ver]:

                for idx, rd in enumerate(repo_d[ver_idx][ver]):
                    if rd.get('name') in nd.values():

                        if nd.get('created_at') != rd.get('created_at'):
                            repo_d[ver_idx][ver][idx]['download_count'] = rd.get('download_count') + nd.get('download_count')
                        else:
                            repo_d[ver_idx][ver][idx]['download_count'] = nd.get('download_count')
                        repo_d[ver_idx][ver][idx]['updated_at'] = nd.get('updated_at')
                        break
                else:
                    repo_d[ver_idx][ver].append(nd)

            repo_d[ver_idx][ver] = [rd for rd in repo_d[ver_idx][ver] if any(rd.get('name') == name for name in names)]
            output.append(repo_d[ver_idx])
        else:
            output.append(new_data)


    os.makedirs("logs", exist_ok=True)
    with open(file_path, 'w+') as f:
        f.write(json.dumps(output, indent=4))

    print('update {0}'.format(file_path))
    

if __name__ == '__main__':
    main()
