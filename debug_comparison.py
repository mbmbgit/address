import pandas as pd
import re
import zenhan

def advanced_normalize_address(address: str) -> str:
    """
    住所文字列をより高度に正規化する関数。
    """
    if not isinstance(address, str):
        return ''
    
    address = zenhan.z2h(address, zenhan.ASCII)
    address = zenhan.h2z(address, zenhan.KANA)

    try:
        address = zenhan.kansuji2arabic(address, zenhan.ALL)
    except:
        pass

    address = address.replace('ヶ', 'ケ').replace('ガ', 'ケ')
    address = re.sub(r'^(大字|字)', '', address)
    address = re.sub(r'(丁目|丁|番地|番|号)$', '', address)
    address = re.sub(r'\s+', '', address)
    
    return address

def analyze_and_export_matches():
    """
    住所を正規化し、一致・不一致の結果をそれぞれ別のCSVファイルに出力します。
    """
    # --- 入力ファイルパス ---
    path_digital_cho = '/workspaces/address/adress_degital_cho .csv'
    path_ken_all = '/workspaces/address/utf_ken_all_pref_city_address_clean.csv'

    # --- 出力ファイルパス ---
    output_matched = '/workspaces/address/matched_addresses.csv'
    output_unmatched_digital = '/workspaces/address/unmatched_digital_cho.csv'
    output_unmatched_ken_all = '/workspaces/address/unmatched_ken_all.csv'

    try:
        print("ファイルを読み込んでいます...")
        df_digital_cho = pd.read_csv(path_digital_cho, header=0, dtype=str)
        df_digital_cho.columns = ['都道府県', '市', '区', '町域名', 'e']

        df_ken_all = pd.read_csv(path_ken_all, dtype=str)

        print("住所を正規化しています...")
        # --- 正規化列を作成 ---
        df_digital_cho['original_address'] = df_digital_cho.iloc[:, :4].fillna('').agg(''.join, axis=1)
        df_digital_cho['normalized_address'] = df_digital_cho['original_address'].apply(advanced_normalize_address)

        df_ken_all['original_address'] = df_ken_all.iloc[:, :3].fillna('').agg(''.join, axis=1)
        df_ken_all['normalized_address'] = df_ken_all['original_address'].apply(advanced_normalize_address)
        
        # 重複を削除しておく
        df_digital_cho.drop_duplicates(subset=['normalized_address'], inplace=True)
        df_ken_all.drop_duplicates(subset=['normalized_address'], inplace=True)

        print("データをマージして分析しています...")
        # --- マージ処理 ---
        # indicator=Trueで、どのファイルに由来するかがわかる列が追加される
        merged_df = pd.merge(
            df_digital_cho,
            df_ken_all,
            on='normalized_address',
            how='outer',
            suffixes=('_digital', '_ken_all'),
            indicator=True
        )

        # --- 結果を分類 ---
        # 一致したデータ (both)
        matched_df = merged_df[merged_df['_merge'] == 'both']
        
        # digital_choにのみ存在するデータ (left_only)
        unmatched_digital_df = merged_df[merged_df['_merge'] == 'left_only']

        # ken_allにのみ存在するデータ (right_only)
        unmatched_ken_all_df = merged_df[merged_df['_merge'] == 'right_only']

        # --- CSVファイルに出力 ---
        print(f"一致したデータを '{output_matched}' に出力しています...")
        matched_df.to_csv(output_matched, index=False)

        print(f"digital_choのみのデータを '{output_unmatched_digital}' に出力しています...")
        unmatched_digital_df.to_csv(output_unmatched_digital, index=False)

        print(f"ken_allのみのデータを '{output_unmatched_ken_all}' に出力しています...")
        unmatched_ken_all_df.to_csv(output_unmatched_ken_all, index=False)

        print("\n--- 分析結果 ---")
        print(f"一致した住所の数: {len(matched_df)}")
        print(f"digital_choのみに存在する住所の数: {len(unmatched_digital_df)}")
        print(f"ken_allのみに存在する住所の数: {len(unmatched_ken_all_df)}")
        print("\n処理が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == '__main__':
    analyze_and_export_matches()