# TCP ConnectとOSエラーを読み解く

## TCP Connectとは

`socket.socket(socket.AF_INET, socket.SOCK_STREAM)` はIPv4のTCPストリームソケットを生成します。`connect_ex((target,port))` で宛先へ接続を試み、通常成功で0、失敗でエラー番号を返します。タイムアウトやOS条件によっては例外が発生します。実際のネットワークパケットはOSのTCP実装が生成します。生のSYN/ACK/FINを自分で組み立てるScapyの例とは混同しないこと。

## 結果の分類

- `open`: TCP接続の成立が観測された。アプリケーションが正しい応答を返すことや脆弱でないことは示さない。
- `refused`: OSがECONNREFUSEDを返した。通常は接続先がそのポートの接続を受け付けなかった。どの機器が応答したかを特定できるわけではない。
- `timeout`: OSからETIMEDOUTが返った、またはPythonがTimeoutErrorを送出した。応答が来ない原因はネットワークやフィルタなど複数あり、閉じたポートと断定できない。
- `unreachable`: EHOSTUNREACH/ENETUNREACHが返った。宛先ホストまたはネットワークへ到達できないというOSからの情報。TCPポートの状態を直接証明しない。
- `error_or_unknown`: 上記以外のエラーコードまたは例外で、十分な根拠がない。安易にclosedへ寄せず、errnoとOSを記録して調査する。

## どうしてTimeoutErrorを先に捕捉するのか

Pythonの`TimeoutError`は`OSError`のサブクラスです。`except OSError`を先に書くとTimeoutErrorもそちらに入るため、`.errno` が `None` の場合に分類できなくなります。`except TimeoutError:` を先に置いて `errno.ETIMEDOUT` に揃え、その後でほかの`OSError`を処理します。これは実際のネットワークの全タイムアウトの種類を網羅するという主張ではありません。

## なぜ異常系をモックするのか

意図的に第三者IPをスキャンしてタイムアウトを作る必要はありません。`unittest.mock.patch("scanner.socket.socket")` を使い、`connect_ex` が `TimeoutError()` を送出する・ENETUNREACHを戻すという条件を作ります。検査するのはPythonプログラムの分岐ロジックであり、経路制御やファイアウォールの挙動ではありません。

## スコープ管理の注意

プライベートIPであることはアクセスの許可ではありません。`--authorized` はスキャナ内部の追加確認フラグで、対象管理者の署名や許可を取得する仕組みではありません。権限を取得した場合のみ、自分のラボのCIDRと対象を明示して実行します。既定値はloopbackに留めることで誤操作を減らしていますが、ソフトウェア上の制限を絶対的なアクセス制御と見なさないでください。
