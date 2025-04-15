import boto3
import os
import tkinter as tk
from tkinter import filedialog, ttk
import time

def download_folder_from_s3(bucket_name, s3_folder, local_folder):
    s3 = boto3.client('s3')
    downloaded_count = 0
    start_time = time.time()
    
    try:
        # S3バケット内のオブジェクトを一覧表示
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=s3_folder)
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                s3_key = obj['Key']
                
                # フォルダ自体は飛ばす（サイズが0のオブジェクト）
                if s3_key.endswith('/') and obj['Size'] == 0:
                    continue
                
                # ローカルでのファイルパスを決定
                if s3_folder:
                    relative_path = s3_key[len(s3_folder):].lstrip('/')
                else:
                    relative_path = s3_key
                    
                local_file_path = os.path.join(local_folder, relative_path)
                
                # ディレクトリが存在しない場合は作成
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # ファイルをダウンロード
                try:
                    print(f"Downloading {bucket_name}/{s3_key} to {local_file_path}")
                    s3.download_file(bucket_name, s3_key, local_file_path)
                    print(f"Successfully downloaded {s3_key}")
                    downloaded_count += 1
                except Exception as e:
                    print(f"Error downloading {s3_key}: {str(e)}")
                    
    except Exception as e:
        print(f"Error listing objects in bucket: {str(e)}")
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / downloaded_count if downloaded_count > 0 else 0
    
    return downloaded_count, total_time, avg_time

def select_folder():
    folder = filedialog.askdirectory()
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, folder)

def get_bucket_list():
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    return [bucket['Name'] for bucket in response['Buckets']]

def list_s3_folders():
    bucket_name = bucket_combobox.get()
    if not bucket_name:
        return []
    
    s3 = boto3.client('s3')
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Delimiter='/')
        folders = []
        
        # 'CommonPrefixes'がある場合はフォルダとして扱う
        if 'CommonPrefixes' in response:
            folders = [prefix['Prefix'] for prefix in response['CommonPrefixes']]
        
        # ルートディレクトリも選択肢に追加
        folders.insert(0, "")
        return folders
    except Exception as e:
        print(f"Error listing folders: {str(e)}")
        return []

def update_s3_folders(*args):
    s3_folder_combobox['values'] = list_s3_folders()
    s3_folder_combobox.current(0)

def start_download():
    bucket_name = bucket_combobox.get()
    s3_folder = s3_folder_combobox.get()
    local_folder = folder_entry.get()
    
    if bucket_name and local_folder:
        downloaded_count, total_time, avg_time = download_folder_from_s3(bucket_name, s3_folder, local_folder)
        result_text = (f"ダウンロード完了\n"
                       f"処理件数: {downloaded_count}件\n"
                       f"総処理時間: {total_time:.2f}秒\n"
                       f"1件あたりの平均時間: {avg_time:.2f}秒")
        result_label.config(text=result_text)
    else:
        result_label.config(text="バケットとローカルフォルダを選択してください")

# GUIの設定
root = tk.Tk()
root.title("S3 Folder Downloader")

tk.Label(root, text="S3バケット:").grid(row=0, column=0, sticky="e")
bucket_combobox = ttk.Combobox(root, values=get_bucket_list(), width=47)
bucket_combobox.grid(row=0, column=1)
bucket_combobox.bind("<<ComboboxSelected>>", update_s3_folders)

tk.Label(root, text="S3フォルダ:").grid(row=1, column=0, sticky="e")
s3_folder_combobox = ttk.Combobox(root, width=47)
s3_folder_combobox.grid(row=1, column=1)

tk.Label(root, text="ローカルフォルダ:").grid(row=2, column=0, sticky="e")
folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=2, column=1)
tk.Button(root, text="選択", command=select_folder).grid(row=2, column=2)

tk.Button(root, text="ダウンロード開始", command=start_download).grid(row=3, column=1)

result_label = tk.Label(root, text="", justify=tk.LEFT)
result_label.grid(row=4, column=1)

# 初期値の設定
if bucket_combobox['values']:
    bucket_combobox.current(0)
    update_s3_folders()

root.mainloop()