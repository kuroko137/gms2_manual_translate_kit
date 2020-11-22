import os
import sys
import re
import datetime


def write_update_stats(log_dir, ver, infos, files):
    lines = []
    header = 'time\tver\tlines\ttr_lines\twords\ttr_words\tpct_lines\tadd_pct_lines\tadd_lines\tadd_words'
    old_ver = 0

    # ログから前の統計を取得

    latest_path = os.path.join(log_dir, 'discord_latest_notice.log')
    log_path = os.path.join(log_dir, 'update_stats.csv')
    log_lines = []

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log_lines = f.read().splitlines(False)[1:]
        if log_lines:
            old_ver = int(log_lines[0].split('\t')[1])

    # ログに統計を書き込み
    total_lines = infos[0]
    total_words = infos[3]
    tr_lines = infos[1]
    tr_words = infos[4]
    add_lines = '{:,}'.format(infos[2])
    add_words = '{:,}'.format(infos[5])

    total_pct = '{:.3f}'.format((infos[1] / infos[0]) * 100)
    add_pct = '{:.3f}'.format((infos[2] / infos[0]) * 100)

    dt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    time = dt.strftime('%Y/%m/%d %H:%M:%S')

    if infos[2] > 0:
        line = '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}'.format(time, ver, total_lines, tr_lines, total_words, tr_words, total_pct, add_pct, add_lines, add_words)
    else:
        line = '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}'.format(time, ver, total_lines, tr_lines, total_words, tr_words, total_pct)

    lines.insert(0, line)
    lines.insert(0, header)
    lines = lines + log_lines

    with open(log_path, "w+") as f:
        f.write('\n'.join(lines))


    # ------------------------------------
    # Discordへの通知メッセージを環境変数にセット

    # 通知インターバルのチェック

    NOTIFICATION_SKIP = False

    WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
    WEBHOOK_ID = os.environ.get("DISCORD_WEBHOOK_ID")

    if WEBHOOK == None or WEBHOOK == '' or WEBHOOK_ID == None or WEBHOOK_ID == '':
        NOTIFICATION_SKIP = True

    if log_lines and NOTIFICATION_SKIP == False:

        interval = os.environ.get("DISCORD_INTERVAL")
        if interval != None and interval != '':
            interval = int(interval)
            if interval < 0:
                interval = 0
            else:
                interval = interval * 3600
        else:
            interval = 0

        interval_play = 1800 # Actionの実行時間がずれた場合のために30分の猶予時間を設ける

        cs = [int(d) for d in re.split(r'[/ :]', time)]
        cd = datetime.datetime(cs[0], cs[1], cs[2], cs[3], cs[4])

        if os.path.exists(latest_path):
            with open(latest_path) as f:
                ls = [int(d) for d in re.split(r'[/ :]', f.readline())]
                ld = datetime.datetime(ls[0], ls[1], ls[2], ls[3], ls[4])

                if cd < (ld + datetime.timedelta(seconds=(interval - interval_play))): # 現在時間がインターバル未満
                    NOTIFICATION_SKIP = True

        if interval > 0 and NOTIFICATION_SKIP == False:
            for line in log_lines:
                s = line.replace(',', '').split('\t')
                ls = [int(d) for d in re.split(r'[/ :]', s[0])]
                nd = datetime.datetime(ls[0], ls[1], ls[2], ls[3], ls[4])

                if nd < (cd - datetime.timedelta(seconds=interval)):
                    break

                if len(s) > 9:
                    infos[2] += int(s[8])
                    infos[5] += int(s[9])

            add_lines = '{:,}'.format(infos[2])
            add_words = '{:,}'.format(infos[5])

            total_pct = '{:.3f}'.format((infos[1] / infos[0]) * 100)
            add_pct = '{:.3f}'.format((infos[2] / infos[0]) * 100)

    if NOTIFICATION_SKIP:
        print('The interval has not passed. Cancel notification.')
        return
    else:
        with open(latest_path, "w+") as f:
            f.write(time)

    # 通知メッセージを設定
    if old_ver > 0 and ver > old_ver:
        message = 'notify_message={0} - 日本語化率: {1}% (バージョン {2} > {3}\n'.format(time, total_pct, old_ver, ver)
    elif add_lines:
        message = 'notify_message={0} - 日本語化率: {1}% (+{2}%, {3} 行, {4} 語)\n'.format(time, total_pct, add_pct, add_lines, add_words)
    else:
        message = 'notify_message={0} - 日本語化率: {1}% (変更のみ)\n'.format(time, total_pct)

    msg_path = '_ENV_NOTIFY_MESSAGE'
    with open(msg_path, "w+", encoding='utf_8') as f: # 環境変数に代入できなくなるためBOM無しで出力する
        f.write(message)

    # 変更されたファイルの名前を通知するかどうか
    DETAILS = os.environ.get("DISCORD_DETAILS")
    if DETAILS == None or DETAILS == '' or DETAILS.lower() == 'false':
        DETAILS = False
    else:
        DETAILS = True

    if DETAILS and len(files) > 0:
        detail_path = '_ENV_NOTIFY_DETAILS'
        str_files = ''

        files = [re.sub(r'.*／', r'', file) for file in files]
        files = [file for file in files if file != '']

        for idx, file in enumerate(files):
            if idx >= 10: # 10ファイル以上は省略
                break
            str_files += file + ', '
        str_files = str_files.strip(', ')
        if len(files) > 10:
            str_files += '...'

        message = 'notify_details=更新ファイル: {0}\n'.format(str_files)
        with open(detail_path, "w+", encoding='utf_8') as f:
            f.write(message)

    return
