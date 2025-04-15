import tkinter as tk
from tkinter import ttk
import boto3
from botocore.exceptions import ClientError

def get_bucket_list():
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    return [bucket['Name'] for bucket in response['Buckets']]

def delete_objects_in_batches(bucket_name, prefix, batch_size=1000, max_delete=None):
    s3 = boto3.client('s3')
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        total_deleted = 0
        for page in page_iterator:
            if "Contents" not in page:
                result_label.config(text="削除するオブジェクトがありません。")
                return

            delete_us = []
            for obj in page.get('Contents', []):
                delete_us.append({'Key': obj['Key']})
                if len(delete_us) >= batch_size or (max_delete and total_deleted + len(delete_us) >= max_delete):
                    break

            if not delete_us:
                break

            # 削除実行
            s3.delete_objects(Bucket=bucket_name, Delete={'Objects': delete_us})
            total_deleted += len(delete_us)
            result_label.config(text=f"{len(delete_us)} オブジェクトを削除しました。合計: {total_deleted}")
            root.update()

            if max_delete and total_deleted >= max_delete:
                break

        result_label.config(text=f"削除処理が完了しました。合計: {total_deleted}オブジェクトを削除しました。")

    except ClientError as e:
        result_label.config(text=f"エラーが発生しました: {e}")

def start_delete():
    bucket_name = bucket_combobox.get()
    prefix = s3_folder_entry.get()
    batch_size = 1000
    max_delete = max_delete_entry.get()

    if not bucket_name:
        result_label.config(text="S3バケットを選択してください。")
        return

    if max_delete:
        try:
            max_delete = int(max_delete)
        except ValueError:
            result_label.config(text="上限件数は整数で入力してください。")
            return
    else:
        max_delete = None

    result_label.config(text=f"s3://{bucket_name}/{prefix} 配下のオブジェクトの削除を開始します。")
    root.update()
    delete_objects_in_batches(bucket_name, prefix, batch_size, max_delete)

# GUIの設定
root = tk.Tk()
root.title("S3オブジェクト削除ツール")

tk.Label(root, text="S3バケット:").grid(row=1, column=0, sticky="e")
bucket_combobox = ttk.Combobox(root, values=get_bucket_list(), width=47)
bucket_combobox.grid(row=1, column=1)

tk.Label(root, text="S3フォルダ (オプション):").grid(row=2, column=0, sticky="e")
s3_folder_entry = tk.Entry(root, width=50)
s3_folder_entry.grid(row=2, column=1)

tk.Label(root, text="削除上限件数 (オプション):").grid(row=3, column=0, sticky="e")
max_delete_entry = tk.Entry(root, width=50)
max_delete_entry.grid(row=3, column=1)

tk.Button(root, text="削除開始", command=start_delete).grid(row=4, column=1)

result_label = tk.Label(root, text="", justify=tk.LEFT, wraplength=400)
result_label.grid(row=5, column=0, columnspan=2)

root.mainloop()