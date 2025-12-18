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
    if not url:
        st.warning("URLを入力してください！")
    else:
        try:
            with st.spinner('分析中...'):
                # スクレイピング実行
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = response.apparent_encoding  # 文字化け防止
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # タイトル取得
                    page_title = soup.title.string if soup.title else "タイトル不明"
                    
                    # 本文抽出（簡易的）
                    text_content = soup.get_text().replace("\n", "").replace(" ", "")
                    char_count = len(text_content)
                    
                    # 結果表示エリア
                    st.success("取得成功！")
                    
                    # 基本情報
                    st.subheader("📊 基本データ")
                    col1, col2 = st.columns(2)
                    col1.metric("文字数（目安）", f"{char_count:,} 文字")
                    col2.metric("ステータス", response.status_code)
                    
                    st.info(f"**記事タイトル**: {page_title}")
                    
                    # 見出し抽出 (H1, H2, H3)
                    st.subheader("📑 見出し構成")
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
                    
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

st.markdown("---")
st.caption("※ サイトの仕様によっては取得できない場合があります。スクレイピングは節度を持って行いましょう。")