# 採点斬り 2021バージョン
![トップ](./appfigs/top.png)
* <font color="red">このページ下部に、Q＆Aや過去のトラブル一覧があります。ソフトを使う前に、まずはそちらをご覧ください。</font>

### 更新記録
* 解説動画を作りました。[Youtubeに飛びます。](https://youtu.be/zhaWaxFah2g)
* 2022.3.9  採点結果の用紙に○×△の記号を付ける拡張ソフトをリリースしました。[こちら](https://phys-ken.github.io/saitenGiri2021-marubatu/)からダウンロードできます。

## はじめに
* 竹内俊彦氏作成の[採点革命](http://www.nurs.or.jp/~lionfan/freesoft_45.html)や島守睦美氏作成の[採点斬り](http://www.nurs.or.jp/~lionfan/freesoft_49.html)などの素晴らしいフリーソフトを参考に、現在の環境でも動く同様のソフトを作成しました。
* フリーソフトですが、著作権は放棄しません。
* 転載、再配布は自由ですが、バグ対応等もあるので、現在のページ (https://phys-ken.github.io/saitenGiri2021/) へのリンクを貼ってください。
* ライセンスは、GPLv3.0です。
* なお、このソフトウェアの使用によって生じた一切の損害について責任を負わないものとし、フリー版・シェアウェア版を問わず、個別のバグ対応は一切行いませんのでご注意下さい。
* とは言っても、バグの報告をいただけた場合にはできる限り対応します。[TwitterのDM](https://twitter.com/phys_ken)か、Githubのissueにあげてください。
* Qiitaに記事を書きました。処理の概要やコードに関する踏み込んだ解説はこっちの方に書きました。[【デジタル採点】採点斬り2021verをPythonで作ってみた](https://qiita.com/phys-ken/items/4fac021504d7fe6b98b2)

## 想定している状況
* 学校の定期試験や小テストでの利用を想定しています。
* 解答用紙をスキャナー等で読み取る必要があります。
* 表面はマークシート式で、裏面で記述式で試験を実施するのが良いと思います。
* 両面読み取り可能なスキャナーを使用するとスムーズです。しかし、多くのスキャナーでは表面と裏面が連番を振られてしまいます。その時のために、[ウラオモテヤマネコ](https://phys-ken.github.io/uraomoteYamaneko/)というフリーソフトを作りました。

## 使い方
0. まず、このページ下部の**Q＆A**と**寄せられた質問・意見**をみることをおすすめします。過去にあったトラブルが載っています、読んでおくと、ミスが未然に防げるかもしれません。
1. このページ右上のダウンロードボタンか、[Release](https://github.com/phys-ken/saitenGiri2021/releases)のページから、最新版をダウンロードしてください。`dist_XXX`フォルダの中身が、アプリになります。
1. Windowsだと**採点斬り2021.exe**、Macだと**saitenGiri2021**がソフト本体になります。インストール等は不要なので、お好みの場所にソフトを保存してください。
1. 採点斬りを起動してください。
    1. windowsの場合は、ダブルクリックしてください。
    1. macの場合は、ターミナルでアプリが保存されているフォルダに移動してから、`./saitenGiri2021`で起動してください。ダブルクリックだと、うまく起動されません。
1. 初期設定ボタンを押してください。同じ場所に、settingフォルダが展開されます。
1. 解答用紙を、`./setting/input`に保存してください。
    1. 練習用の画像を、`test_fig`の中に入れています。これは、元の採点斬りのサンプルを利用させていただいています。
3. 斬る範囲を決めてください。(1枚目の解答用紙がロードされます。)![gifアニメ](appfigs/1giri.gif)
    1. １か所目は名前、２か所目以降は回答部分になります。
    1. 範囲を決める際は、実寸で0.5cm程度余白があるように選択すると、スキャン時の微妙なブレにも対応できると思います。
    1. 決まったら、**入力終了**を押してください。
4. 斬ります。裏側で動作しています。進み具合が気になる場合は、こっそり起動しているターミナルをみると、進捗のログが表示されています。
    1. このタイミングで、裏では`saiten.xlsx`が作成されています。
5. いよいよ採点です。ver.3.0以降は、画面が少し見やすくなっています。...![gifアニメ](appfigs/2saiten.gif)
    1. 点数をキーボードの数字キーで入力します。
    1. 矢印キーで、`次へ進む・前に戻る`ができます。
    1. `shift` や `Enter` を押すと、`skip` できます。`skip`とした項目は採点ボタンを押しても採点されず、次回選択時にまた出てきます。
    1. **採点実行**を押すと、得点をつけた項目が採点され、`setting/output`の中にある`saiten.xlsx`も更新されます。
        1. `saiten.xlsx`を起動している状態で**採点実行**をすると、動作がクラッシュします。
6. **Excelに出力**を押して、`saiten.xlsx`を作成します。 ![画像](appfigs/3xlsx.png)
7. **採点済み画像を出力**で、採点結果を出力します。![画像](appfigs/4kaitouyousi.jpg)
    1. 未採点の項目は`?`と表示させています。合計点は、`?`を無視して計算します。


## Q&A
* 画面が**応答なし**になる、フリーズか時間がかかっているだけなのか区別がつかない。
  * 裏で起動しているコンソール(文字だけの画面)に、進捗が表示されています。そちらを見てください。
* 一回採点した内容を、もう一度確認したいときは？
  * 採点の点検機能が実装できませんでした。`setting/output/Q_000X`の中に、配点ごとにフォルダが作成されています。お手数ですが、自分でフォルダ内を漁って、画像ファイルを`setting/output/Q_000X`の直下に保存して、再度採点をしてください。
  * 多分、フォルダのプレビューで一括表示した方が見やすいと思います。

## 実際に寄せられたご意見・ご感想など(Twitterで募集中)
* ソフトのエラーによる採点ミスはなかった。(320人分、50問の試験)
  * 安心しました。計算ミス等のソフトのエラーがあれば、早急に教えてください。
* (アドバイス)まずは、模範解答１枚で試しに採点してみる
  * 元の採点斬りを使っていた方からのアドバイスです。ソフトから出力される**採点済み解答用紙**の文字サイズなどを事前に確認してから始めた方が良いとのことです。
* 採点結果の画像が、グレースケールになってしまう。**（未解決、解決策求ム）**
  * 採点画像保存の際に、ファイルの容量が大きくなりすぎないように最適化をしています。元の画像が高画質すぎたり、カラーで保存されていたりしてファイルの容量が大きいと保存の際に勝手にグレースケール化してしまうみたいです。元画像のファイルサイズを小さくすればよいのではと思います。
* 画像の切り出し、採点結果画像の出力が思ったより時間がかかる(1枚1分ほど)。
  * 問題数が増えると、画像処理はどうしても時間がかかってしまいます。元の画像の画質を落としておく、カラー画像ではなくグレースケールで保存するなどしてください。また、PCで同時にほかの作業をしないなども、ありきたりですが結構効果があります。
  * 作者がよくやるのは、授業や試験監督の直前に採点処理開始ボタンを押します。教室に戻ってくるとあら不思議、処理が終わっています。
    * なんで学校の教員用のPCってこれどまでに低スペックなのだろうか...。 
* 出力した採点ずみ解答用紙の得点が重なってしまう

  ![参考画像を準備中です。](appfigs/kasanari.png)
  * 採点時の文字サイズは、**氏名欄の高さの半分**に設定しています。氏名欄の高さがあまりに高すぎると、採点時に文字同士が被ってしまいます。
  * 文字サイズを設問欄の高さと合わせようかとも思いましたが、解答欄が縦長になることもあります(例えば、数学の作図など)。お手数ですが、氏名欄の大きさを解答欄と揃えていただいた方が良いと思います。


## 参考にしたサイト等
* [【Python】簡易的な仕分け機能付き画像ビューワー作ってみた](https://qiita.com/hisakichi95/items/84b73ba14731bc68608a)
* [【python】マウスドラッグで画像から範囲指定する](https://qiita.com/hisakichi95/items/47f6d37e6f425f29c8a8)
* [How to make a tkinter canvas rectangle transparent?](https://stackoverflow.com/questions/54637795/how-to-make-a-tkinter-canvas-rectangle-transparent/54645103)
* [【python, pyinstaller】画像や音楽などの外部ファイルも一括でexe化して配布する](https://msteacher.hatenablog.jp/entry/2020/06/27/170529)


### 作者
* 公立高校教員(理科・物理)
* Twitterのリンクは[こちら](https://twitter.com/phys_ken)
* Qiitaのリンクは[こちら](https://qiita.com/phys-ken)
