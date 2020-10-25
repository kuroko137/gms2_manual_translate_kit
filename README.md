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
  * リリースからダウンロードしたHelpConverterを実行し、必要なファイルを生成してください。  
    以下は各オプションについての説明です。  
    
    * **バージョン**: GMS2のメジャーバージョンを小数点なしで指定します（例: 2.3.0.529の場合は230）
    * **ディレクトリ構成を簡易化**: ParaTranzでのファイル管理を容易化するためのオプションです。深層にあるファイルの名前を'ディレクトリ／ファイル名'に変更し、上位のディレクトリに出力させます。
    * **コンテキストにURLを追加**: ParaTranzのcontext欄にページの元URL（英語版/日本語版）を記載するオプションです。使用する場合はチェックし、有効なURLを入力してください。  
    日本語版マニュアルのURL例: ***https://ユーザー名.github.io/リポジトリ名/***
    * **URLをフレーム同時表示可にする**: コンテキストに記載されるURL形式を変更し、ページ単体ではなくフレームごと表示させるオプションです。2.3.0以降のマニュアルでのみ使用可能です。

* ParaTranzへのアップロード:
  * HelpConverterで生成された**paratranz**ディレクトリをParaTranzのルートディレクトリにアップロードしてください。  
  > サブディレクトリのファイルをすべてアップロードできなかった場合は、ParaTranzの該当ディレクトリを開いてファイルだけをアップロードするとうまくいくはずです。

* リポジトリの構築:
  * GitHubで新規リポジトリを作成します（リポジトリ名がGitHub PagesのURL名となります）。作成後、キットに含まれている**Importer**フォルダ、さらにHelpConverterで生成された **repository** フォルダの中にあるすべてのファイル/フォルダを取り出し、リポジトリの最上位にコミットしてください。容量についての警告は無視して問題ありません。

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


* リリースの利用:
  * GitHub Actionsの実行に成功すると、マニュアルをアーカイブ化したzipファイル、整形済みのIDE言語ファイル（csv）がリリースとして自動生成されます。これらはGamemaker Studio 2でそのまま利用することができます。

  * リリースのURLは動的となるため、他のアプリを通してダウンロードする場合は *https://api.github.com/repos/ユーザー名/リポジトリ名/releases* からリリースのURLを取得してください。

* アップデート:
  * Gamemaker Studio 2のアップデートによってマニュアルに変更が加えられた場合、リポジトリの関連ファイルをHelpConverterで再生成したファイルに置き換えてください。
  ファイルの増減があった場合はtr_sources、docs、およびgeneratedディレクトリ内のファイルをいったん削除してやり直しても差し支えありません。
  >> 2020/07/17現在、ParaTranzにおけるファイルの更新/翻訳のインポートはディレクトリ単位で行うことができないため、各ディレクトリを直接開いてファイルのみアップロードする必要があります。
  
  * [**Winmerge**](https://winmerge.org/?lang=ja)などで新旧のディレクトリを比較すると、どのファイルが追加/削除されたかを簡単に見分けることができます。

  * HelpConverterでの変換時、**前バージョンの翻訳をコピー**欄にParaTranzからダウンロードした前バージョンのプロジェクトディレクトリを指定すると、前バージョンの翻訳をマージしたcsvが**paratranzwith_tr**ディレクトリに出力されます。  
  このオプションを利用し、以下のようにすると翻訳ズレや訳抜けを起こさずにアップデートできます。  
    - 1: **ParaTranz**以下のcsvを**Add Files**で追加  
    - 2: **paratranzwith_tr**以下のcsvを**Import Translations**で追加し、**Force Import**を実行  

  * それぞれの_VERSIONファイルが更新されるまでoverride、override_extraのコピー機能は無効となります。

* ParaTranzの管理外ファイルの翻訳
  * **override/docs**以下にアップロードされたファイルはImporterの実行時、コミットの直前でdocsに上書きコピーされます。翻訳したファイルをこのディレクトリに追加することで、ParaTranzの管理対象外となっている.jsファイルや画像ファイルを日本語化できます。

  * 機能を有効とするには、overrideディレクトリの直下に_VERSIONファイルをコミットする必要があります。
  このファイルはリポジトリ直下の_VERSIONファイルと比較されます。記述されているバージョンがリポジトリ直下のものより古い場合は機能が無効となり、コピーが行われません。

  * ファイル名の先頭にgit_noadd_というフレーズが付加されたファイルはGitHub Pagesおよびアーカイブにコピーされません。メモ書きなど、参考資料としたいファイルを追加するときに使うといいでしょう。

## 予備情報

* 一部エントリへの追加タグ
  * **{IMG_TXT}** 画像の代替テキスト（alt属性）に付加されるタグです。
  * **{ANY_CODE}** GML向けのサンプルコードなど、何らかのコードに付加されるタグです。
  このタグを付加されたエントリは主に文脈情報として利用するためのもので、そのほとんどは翻訳不要です。ただし中にはコメント行が含まれているエントリもあり、そうしたものは翻訳する必要があります。
  * **{SEARCH_RESULT}** 検索結果のページ内容テキストです。
  * **{INDEX_KEYWORD}** 索引のキーワード名です。
  * **{CTR_S}** 特定のエントリを対訳表示させるためのタグです。

* 類似翻訳に付加される文字列
  * **（あいまい一致）** HelpConverterによる前バージョンの翻訳コピー時、類似翻訳が行われた項目に付加される文字列です。上記のタグと異なり残さなくていい文字列のため、翻訳を直した後は消しておきましょう。

* テキストの整形
  * Importer/main.pyの*SPACE_ADJUSTMENT*を変更することで日本語と英数字との間に自動で半角スペースを挿入できます。またそれとは逆に、スペースを削除して字間を詰めることもできます。
    デフォルトでは自動挿入が有効となっています。

* POファイルのメタ情報:
  * Importer/main.pyの*po_replacer*を編集することでPOファイルに追記されるメタ情報を変更できます。
    （翻訳チーム名＋プロジェクトURL、プロジェクト名）

* Discordへの通知:
  * **DISCORD_WEBHOOK**というSecretsを作成してDiscordのウェブフックURLを登録すると、GitHhub Pagesが更新されたときに指定したチャンネルへ通知メッセージが送られます。
  通知メッセージには翻訳された行数、ワード数といった統計も付されます。

## 二次ファイル
以下の機能を利用することで、DnDアクション名とイベント名を日本語化した二次ファイルを生成できます。いずれも有効にするにはimporter/main.pyの**ENABLE_FULL_TRANSLATION**を*True*に設定する必要があります。

* 自動置換:
  * ユーザー辞書を参照し、キーワードの自動置換をマニュアル全体に行う機能です。ユーザー辞書は*dict_dnd.dict（DnDアクション名）*、*dict_misc.dict（イベント名等）*の2つに分けられ、これらを**override_extra/dict**にコミットする必要があります。

  * GitHub Actionsが実行されると、IDEの翻訳データから生成された辞書のサンプルがgenerated/dict_templateに作られます。こちらをベースに辞書を調整していくといいでしょう。
  * dict_dnd.dictによる自動置換は*Drag_And_Drop/Drag_And_Drop_Reference/*以下のHTMLファイルにのみ行われ、dict_misc.dictはそれ以外のすべてのHTMLファイルに行われます。
  * フォーマット:
    - 原文    TAB    訳文    TAB    正規表現パターン_原文    TAB    正規表現パターン_訳文    TAB    i （小/大文字の区別を無視）
    >> 各項目はタブで区切られます。正規表現パターン、小/大文字の区別無視フラグは省略可能です。正規表現パターンを省略した場合はかわりに単純置換が行われます。
    - SAMPLE	サンプル	( ?)SAMPLE( ?)	\1サンプル\2	i

* オーバーライド:
  * **override_extra/docs**以下にアップロードされたファイルを上書きコピーする機能です。前述した通常用のoverrideディレクトリに次いで上書きが行われ、こちらは二次ファイルにのみ適用されます。有効とするにはoverride_extraの直下に_VERSIONファイルをコミットする必要があります。

  * マニュアルだけでなく、IDEの二次ファイルも生成できます。override_extra直下に**ide_overrides.csv**というcsvを作成し、上書きさせるエントリの内容をそのまま記述してください。

  * オーバーライドは自動置換よりも優先されるため、override_extra/docs以下に置かれているHTMLファイルには辞書による自動置換が適用されません。

- - -

* 手動でコミット/翻訳する必要があるファイル（override/docsへのコミットが必要）:

|名称|概要|
|:---:|:---:|
|docs/whxdata/projectsettings.js|フレームのUI項目全般|
|docs/template/Charcoal_Grey/usersettings.js|フレーム中央上部のボタン名|
|docs/*.png, *.gif|各種画像ファイル|

* リポジトリ構成:

|名称|概要|
|:---:|:---:|
|docs|GitHub Pagesの実体|
|.github/workflows|GitHub Actionsのワークフローファイル|
|Importer|ParaTranzの翻訳をGitHub Pagesに反映するためのワークフロー用ツール|
|tr_sources|翻訳対象となるベースファイル群（htm, pot, js, csv）。Importerによる変換処理時に参照|
|_VERSION|マニュアルのバージョン|
|logs|各種ログ|
|override/docs|Importerの実行時、docsに上書きコピーされるファイル群|
|override/_VERSION|overrideのバージョン|
|override/ide_overrides.csv|IDEのオーバーライドcsv|
|override_extra/docs|二次ファイル用。overrideに続いて上書きコピーされるファイル群|
|override_extra/_VERSION|override_extraのバージョン|
|override_extra/ide_overrides.csv|二次ファイル用。IDEのオーバーライドcsv|
|override_extra/dict/dict_dnd.dict|自動置換の辞書ファイル（DnDアクション名）|
|override_extra/dict/dict_event_all.dict|自動置換の辞書ファイル|
|generated/english.csv|ParaTranzのバックアップ（IDE用CSV）|
|generated/manual/csv|ParaTranzのバックアップ（マニュアル用csv）|
|generated/manual/cnv_csv, cnv_po|バックアップに復元処理を施し、ファイル形式を変換したもの。ParaTranz外で翻訳する場合のバックアップ|
|generated/ide/dict_template|自動置換の辞書サンプル|
|generated/ide/japanese_alt.csv|二次IDE言語ファイル|

* リリースの出力ファイル:

|名称|概要|
|:---:|:---:|
|japanese.csv|IDE言語ファイル|
|YoYoStudioRoboHelp.zip|アーカイブ化したマニュアル|
|japanese_alt.csv|IDE言語ファイル（DnDアクション名とイベント名も日本語）|
|YoYoStudioRoboHelp_Alt.zip|アーカイブ化したマニュアル（DnDアクション名とイベント名も日本語）|

## コミットについて
実装したい機能や直したい点などあれば、気軽にプルリクエストいただければと思います。

## 謝辞
* **☆ (ゝω・)v** - [**Trasnlation data importer**](https://github.com/matanki-saito/paratranz2es "Trasnlation data importer")
  * このキットは (ゝω・)vさんのTrasnlation data importerをもとに制作されています。
