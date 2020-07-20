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
  * リリースからダウンロードしたHelpConverterを実行し、以下を参考に必要なファイルを生成してください。
  
  * **バージョン**にはGMS2のメジャーバージョンを小数点なしで指定してください（例: 2.2.5.378の場合は225）  
  
  * **ディレクトリ構成の簡易化**オプションはParaTranzでのファイル管理を容易化するためのものです。深層にあるファイルの名前を'ディレクトリ／ファイル名'に変更し、上位のディレクトリに出力させます。
  
  * **コンテキストの追加**オプションはParaTranzのcontext欄に、英語/日本語マニュアルの実ページへのURLリンクを追加するオプションです。このオプションによって、編集中のページがどのように見えるか簡単に確認できるようになります。  
  使用する場合はチェックし、有効なURLを入力してください。  
  日本語版マニュアルのURL例: ***https://ユーザー名.github.io/リポジトリ名/***
    
* ParaTranzへのアップロード:
  * HelpConverterで生成された**csv**ディレクトリを**ParaTranz**のプロジェクトの最上位にアップロードしてください。
  サブディレクトリのファイルをすべてアップロードできなかった場合は、ParaTranzの該当ディレクトリを開いてファイルだけをアップロードするとうまくいくはずです。  
    
* リポジトリの構築:
  * GitHubで新規リポジトリを作成します（リポジトリ名がGitHub PagesのURL名となります）。作成後、キットに含まれている**Importer**ディレクトリ、**.gitattributes**ファイル、さらにHelp2CSVで生成された **_VERSION** ファイル、および**tr_sources**、**docs**、**override**、**override_extra**ディレクトリをリポジトリの最上位にコミットしてください。  
  
  * リポジトリのSettingsを開き、OptionsメニューからGitHub Pagesのソースディレクトリを**master branch / docs folder**にセットします。
  
  * リポジトリのSettingsを開き、Secretsメニューから必要なSecretsを作成します（**NAME: VALUE**）  
  **PARATRANZ_SECRET:** - ParaTranzのプロフィールページ、鍵マークから確認できる英数字の文字列（********************************）  
  **PARATRANZ_CODE:** - ParaTranzのプロジェクト番号（projects/***の数字）  
  
* ワークフローの作成と実行:
  * リポジトリのActionsページを開き、**New workflow** > **set up a workflow yourself**でワークフローの作成ページを開きます。  
  入力欄にキットのworkflows/**importer.yml**ファイルの中身をコピーし、**Start Commit**からymlファイルをコミットしてワークフローを作成します。
  以上でワークフローが有効となり、一定時間おきにParaTranzの翻訳データがGitHub Pagesに反映されます。
  
  * デフォルトでは3時間おきにデータが取得されます。時間を変更する場合は、ymlファイルの ***- cron:  '0 */3 * * *'*** （クーロン形式のスケジュール設定）を任意の値に変更してください。
  
* GitHub PagesのURL:
  * ***https://ユーザー名.github.io/リポジトリ名*** がページのURLです。リポジトリ作成直後はページが有効になるまで一定時間かかる場合があります。
  
* アップデート:
  * Gamemaker Studio 2のアップデートによってマニュアルに変更が加えられた場合、リポジトリの関連ファイルをHelp2CSVで再生成したファイルに置き換えてください。  
  ファイルの増減があった場合はtr_sources、docs、およびgeneratedディレクトリ内のファイルをいったん削除してやり直しても差し支えありません。  
  
  * 2020/07/17現在、ParaTranzにおけるファイルの更新/翻訳のインポートはディレクトリ単位で行うことができないため、各ディレクトリを直接開いてファイルのみアップロードする必要があります。
  
* ParaTranzの管理外ファイルの翻訳
  * **override/docs**以下にアップロードされたファイルはImporterの実行時、コミットの直前でdocsに上書きコピーされます。翻訳したファイルをこのディレクトリに追加することで、ParaTranzの管理対象外となっている.jsファイルや画像ファイルを日本語化することができます。
  * 機能を有効とするには、overrideディレクトリの直下に_VERSIONファイルをコミットする必要があります。
  このファイルはリポジトリ直下の_VERSIONファイルと比較されます。記述されているバージョンがリポジトリ直下のものより古い場合は機能が無効となり、コピーが行われません。
  
* DnDアクション/イベント名の翻訳
  * importer/main.pyのGenerate_FullTranslationオプションをTrueに設定すると、ParaTranzのenglish.csvから生成した辞書をもとにマニュアル中のDnDアクション名を自動翻訳（単純置換）することができます。  
  * 自動翻訳が行われたマニュアルはGMS2_Japanese_Alt-master.zipという二次アーカイブに含められ、Github Pagesと通常用のアーカイブ（GMS2_Japanese-master.zip）には影響を与えません。  
  * override_extraディレクトリは二次アーカイブ用のoverrideディレクトリであり、overrideに続いて上書きコピーを行います。こちらも機能させるにはoverride_extraディレクトリの直下に_VERSIONファイルをコミットする必要があります。  
  * イベント名は自動翻訳されないため、このディレクトリに手動でイベント名を翻訳したHTMLをコミットする必要があります。
  
### 予備情報
 
* 一部エントリへの追加タグ
  * **{IMG_TXT}** 画像の代替テキスト（alt属性）に付加されるタグです。  
  * **{ANY_CODE}** GML向けのサンプルコードなど、何らかのコードに付加されるタグです。  
  このタグを付加されたエントリはおもに文脈情報として利用するためのもので、そのほとんどは翻訳不要です。ただし中にはコメント行が含まれているエントリもあり、そうしたものは翻訳する必要があります。
  * **{CTR_S}, {CTR_N}** 見出しのDnD名を対訳表示するためのタグです。  
  
* テキストの整形
  * Importer/main.pyのSpace_Adjustmentを変更することで日本語と英数字とのあいだに自動で半角スペースを挿入することができます。またそれとは逆に、スペースを削除して字間を詰めることもできます。  
    デフォルトでは自動挿入が有効となっています。
  
* POファイルのメタ情報:
  * Importer/main.pyの設定値を編集することでPOファイルに追記されるメタ情報を変更することができます。  
    （翻訳チーム名＋プロジェクトURL、プロジェクト名）
  
* 生成されるファイル:
  * generated/CSVにはParaTranzの翻訳データが、残りのディレクトリには変換後の翻訳データがバックアップされます。
  
  * **GMS2_Japanese-master.zip**は翻訳されたマニュアルをアーカイブ化したファイルです。
  
  * **GMS2_Japanese_Alt-master.zip**は上記に加え、DnDアクション/イベント名が翻訳されています。
  
  * docs直下に置かれる**.nojekyll**というファイルはHelpConverterでの変換時に追加されたもので、元のアーカイブには存在しないファイルです。これはGitHub Pagesの動作に必要なファイルであり、GitHub外で利用する場合は不要となるため削除してください。
  
* Discordへの通知:
  * **DISCORD_WEBHOOK**というSecretsを作成してDiscordのウェブフックURLを登録すると、Github Pagesが更新されたときに指定したチャンネルへ通知が送られます。
  importer.ymlを編集することで通知メッセージの内容を変更可能です。

- - -

* 手動でコミット/翻訳する必要があるファイル（override/docsへのコミットが必要）:

|名称|概要|
|:---:|:---:|
|docs/files/treearr.js|ツリーのトピック名|
|docs/files/helpindex.js|トピックの選択ダイアログ|
|docs/files/search.js|検索時のエラーメッセージ類|
|docs/*.png, *.gif|各種画像ファイル|

* リポジトリ構成:

|名称|概要|
|:---:|:---:|
|docs|GitHub Pagesの実体|
|.gitattributes|マニュアル内ファイルの改行コードを統一するための設定ファイル|
|.github/workflows|Github Actionsのワークフローファイル|
|Importer|ParaTranzの翻訳をGithub Pagesに反映するためのワークフロー用ツール|
|tr_sources|翻訳対象となるベースファイル群（html, pot, csv）。Importerによる変換処理時に参照|
|_VERSION|マニュアルのバージョン|
|override/docs|Importerの実行時、docsに上書きコピーされるファイル群|
|override/_VERSION|overrideのバージョン|
|override_extra/docs|overrideに続いて上書きコピーされるファイル群|
|override_extra/_VERSION|override_extraのバージョン|

## 謝辞
* **☆ (ゝω・)v** - [**Trasnlation data importer**](https://github.com/matanki-saito/paratranz2es "Trasnlation data importer")
  * このキットは (ゝω・)vさんのTrasnlation data importerをもとに制作されています。
