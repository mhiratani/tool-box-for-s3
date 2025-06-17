import os
import sys
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

def upload_file_to_s3(file_path):
    """
    指定されたファイルをS3バケットにアップロードします。
    .envファイルからAWS認証情報とS3バケット名を読み込みます。
    """
    # .envファイルの読み込み
    load_dotenv()

    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    s3_bucket_name = os.getenv("S3_BUCKET_NAME")

    # 環境変数が正しく読み込まれたか確認
    if not all([aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket_name]):
        print("エラー: .envファイルから必要なAWS情報が読み込めませんでした。")
        print("AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAMEが定義されているか確認してください。")
        sys.exit(1)

    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"エラー: 指定されたファイル '{file_path}' が見つかりません。")
        sys.exit(1)

    # S3クライアントの初期化
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
    except ClientError as e:
        print(f"S3クライアントの初期化に失敗しました: {e}")
        sys.exit(1)

    # S3にアップロードするオブジェクトキー（ファイル名）
    # デフォルトでは元のファイル名をそのまま使用します
    object_name = os.path.basename(file_path)

    print(f"ファイル '{file_path}' をS3バケット '{s3_bucket_name}' にアップロード中...")
    try:
        s3_client.upload_file(file_path, s3_bucket_name, object_name)
        print(f"ファイル '{file_path}' がS3に '{s3_bucket_name}/{object_name}' として正常にアップロードされました。")
    except ClientError as e:
        print(f"ファイルのアップロードに失敗しました: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # コマンド引数の確認
    if len(sys.argv) != 2:
        print("使用方法: python s3_uploader.py <アップロードするファイルのパス>")
        sys.exit(1)

    file_to_upload = sys.argv[1]
    upload_file_to_s3(file_to_upload)
