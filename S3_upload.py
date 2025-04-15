import boto3
import os
import tkinter as tk
from tkinter import filedialog, ttk
import time

def upload_folder_to_s3(local_folder, bucket_name, s3_folder):
    s3 = boto3.client('s3')
    uploaded_count = 0
    start_time = time.time()

    # ローカルフォルダ内のすべてのファイルを走査
    for root, dirs, files in os.walk(local_folder):
        for file in files:
            local_file_path = os.path.join(root, file)
            
            # S3内のファイルパスを決定
            relative_path = os.path.relpath(local_file_path, local_folder)
            s3_file_path = os.path.join(s3_folder, relative_path).replace("\\", "/")

            # ファイルをアップロード
            try:
                print(f"Uploading {local_file_path} to {bucket_name}/{s3_file_path}")
                s3.upload_file(local_file_path, bucket_name, s3_file_path)
                print(f"Successfully uploaded {local_file_path}")
                uploaded_count += 1
            except Exception as e:
                print(f"Error uploading {local_file_path}: {str(e)}")

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / uploaded_count if uploaded_count > 0 else 0

    return uploaded_count, total_time, avg_time

def select_folder():
    folder = filedialog.askdirectory()
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, folder)

def get_bucket_list():
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    return [bucket['Name'] for bucket in response['Buckets']]

def start_upload():
    local_folder = folder_entry.get()
    bucket_name = bucket_combobox.get()
    s3_folder = s3_folder_entry.get()
    
    if local_folder and bucket_name:
        uploaded_count, total_time, avg_time = upload_folder_to_s3(local_folder, bucket_name, s3_folder)
        result_text = (f"アップロード完了\n"
                       f"処理件数: {uploaded_count}件\n"
                       f"総処理時間: {total_time:.2f}秒\n"
                       f"1件あたりの平均時間: {avg_time:.2f}秒")
        result_label.config(text=result_text)
    else:
        result_label.config(text="フォルダとバケットを選択してください")

# GUIの設定
root = tk.Tk()
root.title("S3 Folder Uploader")

tk.Label(root, text="ローカルフォルダ:").grid(row=0, column=0, sticky="e")
folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=0, column=1)
tk.Button(root, text="選択", command=select_folder).grid(row=0, column=2)

tk.Label(root, text="S3バケット:").grid(row=1, column=0, sticky="e")
bucket_combobox = ttk.Combobox(root, values=get_bucket_list(), width=47)
bucket_combobox.grid(row=1, column=1)

tk.Label(root, text="S3フォルダ (オプション):").grid(row=2, column=0, sticky="e")
s3_folder_entry = tk.Entry(root, width=50)
s3_folder_entry.grid(row=2, column=1)

tk.Button(root, text="アップロード開始", command=start_upload).grid(row=3, column=1)

result_label = tk.Label(root, text="", justify=tk.LEFT)
result_label.grid(row=4, column=1)

root.mainloop()