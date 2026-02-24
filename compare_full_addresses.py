import pandas as pd

def compare_addresses():
    """
    2つのCSVファイルの「完全な住所」を比較し、一致する件数をカウントします。
    """
    # --- ファイルパス ---
    path_digital_cho = '/workspaces/address/adress_degital_cho .csv'
    path_ken_all = '/workspaces/address/utf_ken_all_pref_city_address_clean.csv'

    try:
        # --- CSVファイルの読み込み ---
        # デジタル庁の住所データ (最初の行がヘッダー 'a,b,c,d,e' なので header=0)
        df_digital_cho = pd.read_csv(path_digital_cho, header=0)
        # 念のため列名を再設定
        df_digital_cho.columns = ['a', 'b', 'c', 'd', 'e']

        # 郵便番号データから作成した住所データ
        df_ken_all = pd.read_csv(path_ken_all)

        # --- 「完全な住所」のリストを作成 ---
        # デジタル庁データ: a, b, c列を結合
        # 欠損値(NaN)はエラーを防ぐために空文字列として扱います
        addresses_digital_cho = (df_digital_cho['a'].fillna('') +
                                 df_digital_cho['b'].fillna('') +
                                 df_digital_cho['c'].fillna('')).unique()

        # 郵便番号データ: 1, 2, 3列目を結合
        addresses_ken_all = (df_ken_all['都道府県'].fillna('') +
                             df_ken_all['市区町村'].fillna('') +
                             df_ken_all['住所'].fillna('')).unique()

        # --- 住所の一致をカウント ---
        # 高速な比較のためにセットに変換
        set_digital_cho = set(addresses_digital_cho)
        set_ken_all = set(addresses_ken_all)

        # 共通の住所を計算
        common_addresses = set_digital_cho.intersection(set_ken_all)

        # 一致する住所の数をカウント
        match_count = len(common_addresses)

        # --- 結果の表示 ---
        print(f"ファイル1 ({path_digital_cho.split('/')[-1]}) の一意な住所数: {len(set_digital_cho)}")
        print(f"ファイル2 ({path_ken_all.split('/')[-1]}) の一意な住所数: {len(set_ken_all)}")
        print("-" * 30)
        print(f"一致する住所の数: {match_count}")

    except FileNotFoundError as e:
        print(f"エラー: ファイルが見つかりません。 {e.filename}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == '__main__':
    compare_addresses()