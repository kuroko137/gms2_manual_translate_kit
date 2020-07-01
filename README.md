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
  * リリースからダウンロードしたHelp2CSVを実行してください。Gamemaker Studio 2のインストールディレクトリにあるchm2web/YoYoStudioHelp.zipを指定し、変換を実行するとcsv、source_html、source_pot、docsという4つのフォルダが作成されます。
  そのうちのcsvフォルダをParaTranzのプロジェクトの最上位にアップロードしてください。残りのフォルダは後述のImporterで使用します。
    
* リポジトリの構築:
  * GitHubで新規リポジトリを作成します（リポジトリ名がGitHub PagesのURL名となります）。作成後、キットに含まれているImporterフォルダ、.gitattributesファイル、さらにHelp2CSVで生成されたsource_html、source_pot、docsフォルダをリポジトリの最上位にコミットしてください。  
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

### 予備情報
  
* 生成されるファイル:
  * CSV、POディレクトリにはParaTranzの翻訳データがバックアップされます。
  * GMS2_Japanese-master.zipはGitHub Pagesの中身を圧縮したファイルです。GitHubの仕様により、翻訳済みのHTMLファイルの改行コードがCRLFからLFに強制変換されているため、GitHub外で利用する場合はご注意ください。
  * docs直下にある **.nojekyll** というファイルはHelpConverterでの変換時に追加されたもので、元のアーカイブには存在しないファイルです。これはGitHub Pagesの動作に必要なファイルであり、GitHub外で利用する場合は不要となるため削除してください。

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
|source_html|翻訳対象となるベースhtml。Importerによる変換処理時に参照|
|source_pot|ベースhtmlから生成されたpot。Importerによる変換処理時に参照|
|Importer|ParaTranzからCSVをダウンロードし、HTMLに変換してからdocs以下に出力|
|.github\workflows|定期実行アクション用のワークフローファイル|
|.gitattributes|マニュアル内ファイルの改行コードを統一するための設定ファイル|
|readme.md||
|csv|ImporterによってParaTranzからダウンロードされたCSVファイル。バックアップ用途|
|po|ImporterによってCSVファイルから変換されたPOファイル。HTMLの復元時に参照されるほか、OmegaTなど、他のエディタのためのバックアップ用途にも|
|GMS2_Japanese-master.zip|GitHub Pagesをアーカイブ化したファイル。翻訳済みファイルの改行コードがLFに変更されているため注意|

## 謝辞
* **☆ (ゝω・)v** - [**Trasnlation data importer**](https://github.com/matanki-saito/paratranz2es "Trasnlation data importer")
  * このキットは (ゝω・)vさんのTrasnlation data importerをもとに制作されています。

