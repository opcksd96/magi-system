from time import sleep
from seleniumbase import SB

EMAIL = "w77cf87b3f3yg@gmail.com"
PASSWORD = "gv7SCDR@YfANdH4"

JS_LOGIC = """
/**
 * MAGI Sniffer Engine
 * 1. テキストボックスへの注入
 * 2. 生成完了の監視
 * 3. 回答エレメントの抽出
 */
window.magiSniffer = {
    // 指定した要素が出るまで待つ汎用関数
    waitForElement: async (selector, timeout = 3000) => {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = document.querySelector(selector);
            if (el) return el;
            await new Promise(r => setTimeout(r, 100)); // 100msごとに確認
        }
        return null;
    },

    selectModel: async function(targetModelValue) {
        try {
            const selectorBtn = document.querySelector('button[aria-label="モデルを選択"]');
            if (!selectorBtn) return false;

            // 1. メニューを展開（既に開いている場合はスキップ）
            if (selectorBtn.getAttribute('aria-expanded') !== 'true') {
                selectorBtn.click();
            }

            // 2. モデルリストが出るまで粘る（エラーが出てもループを抜けない）
            for (let i = 0; i < 30; i++) { 
                await new Promise(r => setTimeout(r, 200)); // 200ms間隔
                
                // data-value を持つボタンを全探索
                const target = document.querySelector(`button[data-value="${targetModelValue}"]`);
                
                if (target) {
                    // 3. 要素が見つかっても、少し待ってからクリック（安定化のため）
                    target.scrollIntoView({ block: 'center' }); // 画面外ならスクロール
                    // 物理的なDOM更新を待つ
                    await new Promise(r => setTimeout(r, 800)); 
                    target.click();
                    console.log(`[MAGI] Clicked: ${targetModelValue}`);
                    return true; // ここでようやく結果を返す
                }
            }
        } catch (e) {
            console.error("[MAGI] JS Error during selectModel:", e);
        }
        console.log("ここまで読んだ！");
        return false;
    },

    // JS_LOGIC 内の injectPrompt を以下に差し替え
    injectPrompt: async function(prompt) {
        const maxRetries = 10; // 定義を追加
        const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

        for (let i = 0; i < maxRetries; i++) {
            // ループのたびに document.querySelector し直すのがコツ（最新のDOMを掴むため）
            const el = document.querySelector('#chat-input');
            if (el && el.getAttribute('contenteditable') === 'true') {
                el.focus();
                document.execCommand('insertText', false, prompt);

                // 入力されたか確認
                if (el.innerText.length > 0) {
                    await sleep(200);
                    const btn = document.querySelector('button[type="submit"]');
                    if (btn && !btn.disabled) {
                        btn.click();
                        return true;
                    }
                }
            }
            await sleep(500);
        }
        return false;
    },

    getLastResponse: function() {
        // 全てのチャット回答要素を取得
        const assistants = document.querySelectorAll('.chat-assistant');
        if (assistants.length === 0) return null;

        // 最後の要素が現在の回答
        const lastAssistant = assistants[assistants.length - 1];
        
        // DOMをクローンして操作（画面への影響を防ぐ）
        const clone = lastAssistant.cloneNode(true);

        // 1. コンテナを特定 (HTML構造に基づく)
        const container = clone.querySelector('#response-content-container');
        if (!container) return clone.innerText; // フォールバック

        // 2. 不要な要素（思考プロセス表示など）を削除
        // 構造: <div class="w-fit text-gray-500 ...">...思考...</div>
        const thoughts = container.querySelectorAll('.text-gray-500');
        thoughts.forEach(el => el.remove());

        // 3. フローティングボタンを削除
        const buttons = container.querySelectorAll('[id^="floating-buttons-"]');
        buttons.forEach(el => el.remove());

        // 4. テキストを返却
        return container.innerText.trim();
    },

    getTokenUsage: async function() {
        // 全てのinfoボタンを取得 (idが "info-" で始まる)
        const infos = document.querySelectorAll('button[id^="info-"]');
        if (infos.length === 0) return null;

        // 最後のボタンが最新の回答に対応するはず
        const lastInfo = infos[infos.length - 1];

        // マウスオーバーイベントを発火させてツールチップを表示
        const mouseoverEvent = new MouseEvent('mouseover', {
            bubbles: true,
            cancelable: true,
            view: window
        });
        const mouseenterEvent = new MouseEvent('mouseenter', {
            bubbles: true,
            cancelable: true,
            view: window
        });
        lastInfo.dispatchEvent(mouseoverEvent);
        lastInfo.dispatchEvent(mouseenterEvent);

        // ツールチップが表示されるのを少し待つ
        await new Promise(r => setTimeout(r, 500));

        // ツールチップ要素を探す
        // OpenWebUIの実装依存だが、通常は body 直下か、特定の tooltip クラスを持つ要素として現れる
        // ここでは "Token" という文字列を含む要素を探索する戦略をとる
        // ただし、画面全体から探すと誤爆するので、最近追加された要素や z-index が高い要素などを優先したいが...
        // 単純に body 内のテキストで "Token" を含む最後の要素を探してみる
        
        // 1. role="tooltip" を探す
        let tooltips = document.querySelectorAll('[role="tooltip"]');
        if (tooltips.length > 0) {
            return tooltips[tooltips.length - 1].innerText;
        }

        // 2. なければ、怪しいdivを探す (classに "tooltip" があるかも?)
        tooltips = document.querySelectorAll('.tooltip');
        if (tooltips.length > 0) {
            return tooltips[tooltips.length - 1].innerText;
        }
        
        // 3. 汎用的な探索: visible な要素で "Token" を含む最小の要素
        // これは重いので、とりあえず body の innerText から簡易的に取得してみる
        // ただし、ツールチップは通常DOMの最後の方に追加される
        const allDivs = document.body.querySelectorAll('div');
        for (let i = allDivs.length - 1; i >= 0; i--) {
            const div = allDivs[i];
            if (div.innerText && div.innerText.includes("Token") && div.innerText.length < 500) {
                 // 自身のテキストに見えるか？ (親要素だと長すぎる)
                 return div.innerText.trim();
            }
        }

        return "Token info not found";
    }
};
"""

with SB(uc=True, headless=False) as sb:
    sb.open("http://localhost:8080")

    # ログイン処理
    sb.type("#email", EMAIL)
    sb.type("#password", PASSWORD)
    # ログイン処理後
    sb.click("button[type='submit']")

    # --- 重要：画面遷移とUIの描画完了を待つ ---
    print("MAGI: UIの初期化を待機中...")
    # 「モデルを選択」ボタンが画面に現れ、かつクリック可能になるまで最大15秒待つ
    # これにより、SPAのレンダリング完了を保証します
    sb.wait_for_element_visible('button[aria-label="モデルを選択"]', timeout=15)

    # UIが整ってからJSを注入
    print("MAGI: UserScriptを注入...")
    sb.execute_script(JS_LOGIC)

    # 2. プロンプトの注入実行
    target_model = "qwen3:4b-instruct-2507-q4_K_M"
    prompt = "こんにちは"

    # モデル選択を実行
    print(f"MAGI: モデル選択フェーズ開始... ({target_model})")
    # JS側でもリトライするようにしてあるので、ここで確実に仕留める
    # --- 修正版：windowオブジェクト経由で結果を受け渡す ---
    sb.execute_script("window.magiResult = null;")  # 初期化

    script = f"""
    (async () => {{
        const result = await window.magiSniffer.selectModel('{target_model}');
        window.magiResult = result;
    }})()
    """
    sb.execute_script(script)

    # ポーリングで結果を待つ
    success = False
    for _ in range(30):  # 最大15秒待機 (0.5s * 30)
        res = sb.execute_script("return window.magiResult;")
        if res is not None:
            success = res
            break
        sb.sleep(0.5)

    print(f"MAGI: selectModel result = {success}")
    if success:
        print("MAGI: モデル選択成功。DOMの安定を待機...")
        sb.sleep(1.5)  # モデル切り替えによるDOM再構築時間を確保

        # 次にエディタが準備できるのを待つ
        sb.wait_for_element_present("#chat-input", timeout=10)

        print("MAGI: プロンプト注入...")
        # 注入も非同期なので await するか、戻り値を確認する
        # injectPrompt は同期的に書かれているが内部で await している
        # ここも window.magiResult 方式にするか、単純に実行
        # test.pyの元のコードは単発実行だったので、ここでは単純に実行して、その後監視に入る

        sb.execute_script(f"window.magiSniffer.injectPrompt('{prompt}')")

        print("MAGI: 注入完了（想定）。回答生成を監視します...")

        # 回答監視ループ
        prev_text = ""
        stable_count = 0
        max_wait_loops = 60  # 60秒

        for i in range(max_wait_loops):
            sb.sleep(1)
            current_text = sb.execute_script(
                "return window.magiSniffer.getLastResponse();"
            )

            if current_text:
                # 何か返ってきた
                if current_text == prev_text and len(current_text) > 0:
                    stable_count += 1
                else:
                    stable_count = 0  # 変化したのでリセット

                prev_text = current_text

                # 3秒間変化なしなら完了とみなす
                if stable_count >= 3:
                    print("\n--- MAGI RESPONSE ---")
                    print(current_text)
                    print("---------------------")

                    # --- 追加：トークン情報の取得 ---
                    print("MAGI: トークン情報を取得中...")
                    # JS側で waitForTokenUsage を呼ぶ (JS側で定義した getTokenUsage を非同期で呼ぶ)
                    token_script = """
                    (async () => {
                        const usage = await window.magiSniffer.getTokenUsage();
                        window.magiTokenUsage = usage;
                    })();
                    """
                    sb.execute_script("window.magiTokenUsage = null;")
                    sb.execute_script(token_script)

                    # ポーリング
                    usage_info = None
                    for _ in range(10):  # 最大5秒
                        res = sb.execute_script("return window.magiTokenUsage;")
                        if res is not None:
                            usage_info = res
                            break
                        sb.sleep(0.5)

                    if usage_info:
                        print("\n[Token Usage]")
                        print(usage_info)
                    else:
                        print("\n[Token Usage] Failed to retrieve.")

                    break
            else:
                # まだ回答が始まっていない可能性
                pass

            if i % 10 == 0:
                print(f"MAGI: Waiting... ({i}s)")

    else:
        print("MAGI: モデル選択に失敗しました。")

    sleep(300)
