# gms2_manual_translate_kit

## 概要
Game Maker Studio 2のマニュアル翻訳所を運用するためのキットです。  
必要ファイルを生成するためのHelpConverter、翻訳データをGitHub Pagesに反映するImporterという2つのツールからなります。

### [HelpConverter]
マニュアルのアーカイブファイル（YoYoStudioHelp.zip）から翻訳に必要なファイルを生成するツールです。  

### [Importer]
ParaTranzの翻訳データを一定時間おきに取得し、ミラーサイトであるGitHub Pagesに反映するツールです。  
取得した翻訳データをhtmlに復元し、GitHub Actionsを経由してdocs（GitHub Pagesのソースディレクトリ）に自動でコミットします。  

## 使用方法
* 必要ファイルの生成:
  * リリースからダウンロードしたHelp2CSVを実行してください。Gamemaker Studio 2のインストールディレクトリにあるchm2web/YoYoStudioHelp.zipを指定し、変換を実行するとcsv、source_html、source_pot、docsという4つのディレクトリが作成されます。  
  そのうちのcsvディレクトリを、ParaTranzのプロジェクトの最上位にアップロードしてください。サブディレクトリのファイルを完全にアップロードできなかった場合は、ParaTranzの該当ディレクトリを開いてファイルだけをアップロードするとうまくいくはずです。  
  
  * 「コンテキストの追加」オプションはParaTranzのcontext欄に、英語/日本語マニュアルの実ページへのURLリンクを追加するオプションです。このオプションによって、編集中のページがどのように見えるか簡単に確認できるようになります。  
  使用する場合はチェックし、有効なURLを入力してください。  
  日本語版マニュアルのURL例: ***https://ユーザー名.github.io/リポジトリ名/***

  * 「ディレクトリ構成の簡易化」オプションはParaTranzでのファイル管理を容易化するためのものです。深層にあるファイルの名前を'ディレクトリ／ファイル名'に変更し、上位のディレクトリに出力させます。
    
* リポジトリの構築:
  * GitHubで新規リポジトリを作成します（リポジトリ名がGitHub PagesのURL名となります）。作成後、キットに含まれているImporterディレクトリ、.gitattributesファイル、さらにHelp2CSVで生成されたtr_sources、docsディレクトリをリポジトリの最上位にコミットしてください。  
  * リポジトリのSettingsを開き、OptionsメニューからGitHub Pagesのソースディレクトリを**master branch / docs folder**にセットします。
  * リポジトリのSettingsを開き、Secretsメニューから必要なSecretsを作成します（**NAME: VALUE**）。  
  * **PARATRANZ_SECRET:** - ParaTranzのプロフィールページ、鍵マークから確認できる英数字の文字列（********************************）
  * **PARATRANZ_CODE:** - ParaTranzのプロジェクト番号（projects/***の数字）
  
* ワークフローの作成と実行:
  * リポジトリのActionsページを開き、**New workflow** > **set up a workflow yourself**でワークフローの作成ページを開きます。  
  入力欄にキットのworkflows/**importer.yml**ファイルの中身をコピーし、**Start Commit**からymlファイルをコミットしてワークフローを作成します。
  以上でワークフローが有効となり、一定時間おきにParaTranzの翻訳データがGitHub Pagesに反映されます。
  * デフォルトでは3時間おきにデータが取得されます。時間を変更する場合は、ymlファイルの ***- cron:  '0 */3 * * *'*** （クーロン形式のスケジュール設定）を任意の値に変更してください。
  
* GitHub PagesのURL:
  * ***https://ユーザー名.github.io/リポジトリ名*** がページのURLです。リポジトリ作成直後はページが有効になるまで一定時間かかる場合があります。
  
* アップデート:
  * Gamemaker Studio 2のアップデートによってマニュアルに変更が加えられた場合、関連ファイルをHelp2CSVで再生成したファイルに置き換えてください。  
  ファイルの増減があった場合はsource_html、source_pot、docs、およびcsv、poディレクトリ内のファイルをいったん削除してやり直しても差し支えありません。

### 予備情報
  
* 生成されるファイル:
  * CSV、POディレクトリにはParaTranzの翻訳データがバックアップされます。
  * GMS2_Japanese-master.zipはGitHub Pagesの中身を圧縮したファイルです。GitHubの仕様により、翻訳済みのHTMLファイルの改行コードがCRLFからLFに強制変換されているため、GitHub外で利用する場合はご注意ください。
  * docs直下にある **.nojekyll** というファイルはHelpConverterでの変換時に追加されたもので、元のアーカイブには存在しないファイルです。これはGitHub Pagesの動作に必要なファイルであり、GitHub外で利用する場合は不要となるため削除してください。
  
* テキストの整形
  * Importer/main.pyのSpace_Adjustmentを変更することで日本語と英数字とのあいだに自動で半角スペースを挿入することができます。またそれとは逆に、スペースを削除して字間を詰めることもできます。  
    デフォルトでは自動挿入が有効となっています。
  
* POファイルのメタ情報:
  * Importer/main.pyの設定値を編集することでPOファイルに追記されるメタ情報を変更することができます。  
    （翻訳チーム名＋プロジェクトURL、プロジェクト名）

- - -

* 手動でコミット/翻訳する必要があるファイル:

|名称|概要|
|:---:|:---:|
|docs/files/treearr.js|ツリーのトピック名|
|docs/files/helpindex.js|トピックの選択ダイアログ|
|docs/files/search.js|検索時のエラーメッセージ類|

* リポジトリ構成:

|名称|概要|
|:---:|:---:|
|docs|GitHub Pagesの実体|
|tr_sources|翻訳対象となるベースファイル群（html, pot, csv）。Importerによる変換処理時に参照|
|Importer|ParaTranzからCSVをダウンロードし、HTMLに変換してからdocs以下に出力|
|.github\workflows|定期実行アクション用のワークフローファイル|
|.gitattributes|マニュアル内ファイルの改行コードを統一するための設定ファイル|
|readme.md||
|generated\csv|ImporterによってParaTranzからダウンロードされたCSVファイル。バックアップ用途|
|generated\csv_cnv|Importerによって整形されたCSVファイル|
|generated\po_cnv|csv_cnvから変換されたPOファイル。HTMLの復元時に参照されるほか、OmegaTなど、他のエディタのためのバックアップ用途にも|
|GMS2_Japanese-master.zip|GitHub Pagesをアーカイブ化したファイル。翻訳済みファイルの改行コードがLFに変更されているため注意|

## 謝辞
* **☆ (ゝω・)v** - [**Trasnlation data importer**](https://github.com/matanki-saito/paratranz2es "Trasnlation data importer")
  * このキットは (ゝω・)vさんのTrasnlation data importerをもとに制作されています。

