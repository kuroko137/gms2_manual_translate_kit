function get_graph_data() {
  // GitHubのレポジトリからグラフ用のログデータを取得し、スプレッドシートに反映します
  var res = UrlFetchApp.fetch("https://raw.githubusercontent.com/user/repo/main/logs/update_stats_graph.log");
  var data = res.getContentText();
  data = data.replace("pct_lines", "翻訳率 (行)")
  data = data.replace("pct_words", "翻訳率 (ワード)")
  var sheet = SpreadsheetApp.getActiveSheet();
  var csv = Utilities.parseCsv(data, '\t');
  sheet.getRange(1, 1, csv.length, csv[0].length).setValues(csv);
}
