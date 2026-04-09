import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# ページ設定
st.set_page_config(page_title="記事構成・見出し抽出ツール", layout="centered")

st.title("🔍 記事構成・見出し抽出ツール")
st.markdown("URLを入力するだけで、その記事の「タイトル」「見出し構成」「文字数」を丸裸にします。")

# ユーザーエージェントの設定（スマホとしてアクセスしてブロックを防ぐ）
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
}

# URL入力フォーム
url = st.text_input("分析したい記事のURLを入力してください", placeholder="https://note.com/...")

if st.button("分析開始"):
    # 1. バリデーション（入力値のチェック）
    if not url:
        st.warning("URLを入力してください！")
    elif not url.startswith(("http://", "https://")):
        st.error("⚠️ セキュリティ保護のため、http:// または https:// から始まる有効なURLを入力してください。")
    else:
        try:
            with st.spinner('分析中...'):
                # 2. ストリームモードで取得し、巨大ファイルを弾く（上限5MB）
                # stream=True にすることで、中身を全部一気に読み込まないようにする
                response = requests.get(url, headers=headers, timeout=10, stream=True)
                
                # Content-Length（ファイルサイズ）のチェック
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > 5 * 1024 * 1024:
                    st.error("⚠️ 対象のページサイズが大きすぎるため、分析を中断しました（上限5MB）。")
                    st.stop()
                
                # HTMLのテキストを取得
                html_text = response.text
                response.encoding = response.apparent_encoding  # 文字化け防止
                
                if response.status_code == 200:
                    soup = BeautifulSoup(html_text, "html.parser")
                    
                    # --- (ここから下は元のコードと同じです) ---
                    # タイトル取得
                    page_title = soup.title.string if soup.title else "タイトル不明"
                    
                    # 本文抽出（簡易的）
                    text_content = soup.get_text(separator=" ", strip=True)
                    char_count = len(text_content)
                    
                    st.success(f"✅ 分析完了！")
                    st.subheader(f"📑 タイトル: {page_title}")
                    st.write(f"**推定文字数**: 約 {char_count:,} 文字")
                    st.markdown("---")
                    
                    # 見出しタグの抽出
                    st.subheader("📌 見出し構成")
                    headings = soup.find_all(["h1", "h2", "h3"])
                    
                    if headings:
                        data = []
                        for h in headings:
                            tag = h.name.upper()
                            text = h.get_text().strip()
                            # 視覚的なインデント
                            indent = ""
                            if tag == "H2": indent = "├ "
                            if tag == "H3": indent = "│ └ "
                            
                            st.markdown(f"**{tag}**: {indent}{text}")
                            data.append([tag, text])
                        
                        # CSVダウンロード
                        df = pd.DataFrame(data, columns=["タグ", "見出し内容"])
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        
                        st.download_button(
                            label="見出しリストをダウンロード (CSV)",
                            data=csv,
                            file_name="headings.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("見出し(H1-H3)が見つかりませんでした。")
                        
                else:
                    st.error(f"アクセスできませんでした。ステータスコード: {response.status_code}")
                    
        # 3. エラーハンドリングの細分化（何が起きたか明確にする）
        except requests.exceptions.Timeout:
            st.error("⚠️ 通信がタイムアウトしました。対象のサイトが重いか、アクセスがブロックされています。")
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ サイトへのアクセスに失敗しました。URLが正しいか確認してください。")

st.markdown("---")
st.caption("※ サイトの仕様によっては取得できない場合があります。スクレイピングは節度を持って行いましょう。")
