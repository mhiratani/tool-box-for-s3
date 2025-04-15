import streamlit as st
import boto3
from botocore.exceptions import ClientError
import re
from typing import List, Dict, Any, Tuple

# ページ設定
st.set_page_config(page_title="S3 ファイル検索", layout="wide", page_icon="🔍")

# セッション状態の初期化
def initialize_session_state():
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1
    if 'bucket_list' not in st.session_state:
        st.session_state.bucket_list = []
    if 'selected_bucket' not in st.session_state:
        st.session_state.selected_bucket = ""
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'search_type' not in st.session_state:
        st.session_state.search_type = "部分一致"
    if 'case_sensitive' not in st.session_state:
        st.session_state.case_sensitive = False
    if 'items_per_page' not in st.session_state:
        st.session_state.items_per_page = 50

# S3クライアントを初期化する関数
def initialize_s3_client():
    try:
        return boto3.client('s3')
    except Exception as e:
        st.error(f"S3クライアントの初期化に失敗しました: {str(e)}")
        return None

# バケットリストを取得する関数
def get_bucket_list(s3_client) -> List[str]:
    try:
        response = s3_client.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]
    except ClientError as e:
        st.error(f"バケットリストの取得に失敗しました: {str(e)}")
        return []
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {str(e)}")
        return []

# S3内のオブジェクトを検索する関数
def search_s3(s3_client, bucket: str, term: str, search_type: str, case_sensitive: bool) -> List[Dict[str, Any]]:
    try:
        if not term:
            return []
            
        results = []
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket)

        search_term = term if case_sensitive else term.lower()

        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                compare_key = key if case_sensitive else key.lower()

                if search_type == '完全一致' and compare_key == search_term:
                    results.append(obj)
                elif search_type == '前方一致' and compare_key.startswith(search_term):
                    results.append(obj)
                elif search_type == '部分一致' and search_term in compare_key:
                    results.append(obj)

        return results
    except ClientError as e:
        st.error(f"検索中にエラーが発生しました: {str(e)}")
        return []
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {str(e)}")
        return []

# 検索結果を表示する関数
def display_search_results(results: List[Dict[str, Any]], page_number: int, items_per_page: int):
    if not results:
        st.info('該当するファイルが見つかりませんでした。')
        return

    st.write(f'{len(results)}件のファイルが見つかりました:')
    
    # ページネーション
    total_pages = (len(results) - 1) // items_per_page + 1
    
    # ページ選択UI
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button('前のページ', disabled=(page_number <= 1)):
            st.session_state.page_number = max(1, page_number - 1)
            st.rerun()
    
    with col2:
        page_number = st.slider('ページ', min_value=1, max_value=total_pages, value=page_number)
        st.session_state.page_number = page_number
    
    with col3:
        if st.button('次のページ', disabled=(page_number >= total_pages)):
            st.session_state.page_number = min(total_pages, page_number + 1)
            st.rerun()
    
    # 現在のページのアイテムを表示
    start_idx = (page_number - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(results))
    
    # 検索結果をテーブルとして表示
    result_data = []
    for i, item in enumerate(results[start_idx:end_idx], start=start_idx + 1):
        key = item['Key']
        size = f"{item['Size'] / 1024:.2f} KB" if item['Size'] < 1024 * 1024 else f"{item['Size'] / (1024 * 1024):.2f} MB"
        last_modified = item['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
        result_data.append({"#": i, "ファイル名": key, "サイズ": size, "最終更新日": last_modified})
    
    st.table(result_data)
    
    st.write(f'ページ {page_number} / {total_pages}')

# 検索フォームを表示する関数
def display_search_form(s3_client):
    st.subheader("検索条件")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # バケット選択（ドロップダウン）
        if not st.session_state.bucket_list:
            st.session_state.bucket_list = get_bucket_list(s3_client)
        
        if st.session_state.bucket_list:
            st.session_state.selected_bucket = st.selectbox(
                'S3バケットを選択してください:',
                options=st.session_state.bucket_list,
                index=0 if st.session_state.selected_bucket == "" else st.session_state.bucket_list.index(st.session_state.selected_bucket)
            )
        else:
            st.session_state.selected_bucket = st.text_input('S3バケット名を入力してください:', value=st.session_state.selected_bucket)
    
    with col2:
        st.session_state.search_term = st.text_input('検索語を入力してください:', value=st.session_state.search_term)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.session_state.search_type = st.selectbox(
            '検索タイプを選択してください:',
            options=['完全一致', '前方一致', '部分一致'],
            index=['完全一致', '前方一致', '部分一致'].index(st.session_state.search_type)
        )
    
    with col4:
        st.session_state.case_sensitive = st.checkbox('大文字小文字を区別する', value=st.session_state.case_sensitive)
    
    # 検索ボタン
    search_col1, search_col2, search_col3 = st.columns([1, 1, 3])
    with search_col1:
        search_button = st.button('検索', type="primary", use_container_width=True)
    
    with search_col2:
        if st.button('クリア', use_container_width=True):
            st.session_state.search_term = ""
            st.session_state.page_number = 1
            st.session_state.search_results = []
            st.rerun()
    
    return search_button

# メイン関数
def main():
    st.title('S3 ファイル検索')
    
    # セッション状態の初期化
    initialize_session_state()
    
    # S3クライアントの初期化
    s3_client = initialize_s3_client()
    if not s3_client:
        st.error("S3クライアントの初期化に失敗しました。AWS認証情報を確認してください。")
        return
    
    # 検索フォームの表示
    search_button = display_search_form(s3_client)
    
    # 検索実行
    if search_button:
        if st.session_state.selected_bucket and st.session_state.search_term:
            with st.spinner('検索中...'):
                results = search_s3(
                    s3_client,
                    st.session_state.selected_bucket,
                    st.session_state.search_term,
                    st.session_state.search_type,
                    st.session_state.case_sensitive
                )
                st.session_state.search_results = results
                st.session_state.page_number = 1
        else:
            st.warning('バケット名と検索語の両方を入力してください。')
    
    # 検索結果の表示
    if st.session_state.search_results:
        display_search_results(
            st.session_state.search_results,
            st.session_state.page_number,
            st.session_state.items_per_page
        )

# アプリケーションの実行
if __name__ == "__main__":
    main()