import pandas as pd

def compare_sapporo_addresses():
    """
    「北海道札幌市中央区」の住所に限定して2つのCSVファイルを比較し、
    一致する件数をカウントします。
    """
    # --- ファイルパス ---
    path_digital_cho = '/workspaces/address/adress_degital_cho .csv'
    path_ken_all = '/workspaces/address/utf_ken_all_pref_city_address_clean.csv'

    try:
        # --- CSVファイルの読み込み ---
        df_digital_cho = pd.read_csv(path_digital_cho, header=0)
        df_digital_cho.columns = ['a', 'b', 'c', 'd', 'e']

        df_ken_all = pd.read_csv(path_ken_all)

        # --- 「北海道札幌市中央区」でデータをフィルタリング ---
        # デジタル庁データ
        df_digital_cho_sapporo = df_digital_cho[
            (df_digital_cho['a'] == '北海道') &
            (df_digital_cho['b'] == '札幌市中央区')
        ]

        # 郵便番号データ
        df_ken_all_sapporo = df_ken_all[
            (df_ken_all['都道府県'] == '北海道') &
            (df_ken_all['市区町村'] == '札幌市中央区')
        ]

        # --- 「完全な住所」のリストを作成 ---
        # デジタル庁データ
        addresses_digital_cho = (df_digital_cho_sapporo['a'].fillna('') +
                                 df_digital_cho_sapporo['b'].fillna('') +
                                 df_digital_cho_sapporo['c'].fillna('')).unique()

        # 郵便番号データ
        addresses_ken_all = (df_ken_all_sapporo['都道府県'].fillna('') +
                             df_ken_all_sapporo['市区町村'].fillna('') +
                             df_ken_all_sapporo['住所'].fillna('')).unique()

        # --- 住所の一致をカウント ---
        set_digital_cho = set(addresses_digital_cho)
        set_ken_all = set(addresses_ken_all)
        common_addresses = set_digital_cho.intersection(set_ken_all)
        match_count = len(common_addresses)

        # --- 結果の表示 ---
        print("--- 比較範囲: 北海道 札幌市中央区 ---")
        print(f"ファイル1 ({path_digital_cho.split('/')[-1]}) の一意な住所数: {len(set_digital_cho)}")
        print(f"ファイル2 ({path_ken_all.split('/')[-1]}) の一意な住所数: {len(set_ken_all)}")
        print("-" * 30)
        print(f"一致する住所の数: {match_count}")

    except FileNotFoundError as e:
        print(f"エラー: ファイルが見つかりません。 {e.filename}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == '__main__':
    compare_sapporo_addresses()