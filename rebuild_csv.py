import csv, re
from pathlib import Path

src = Path('/workspaces/address/utf_ken_all.csv')
dst = Path('/workspaces/address/utf_ken_all_pref_city_address_clean.csv')

# 全角・半角括弧とその中身を除去するパターン
paren_re = re.compile(r'[（(][^）)]*[）)]')

written = 0
with src.open('r', encoding='utf-8', newline='') as f_in, \
     dst.open('w', encoding='utf-8', newline='') as f_out:
    reader = csv.reader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(['都道府県', '市区町村', '住所'])
    for row in reader:
        if len(row) < 9:
            continue
        pref, city, addr = row[6], row[7], row[8]
        # 「以下に掲載がない場合」を空文字に置換（行は残す）
        addr = addr.replace('以下に掲載がない場合', '')
        # 括弧とその中身を除去
        addr = paren_re.sub('', addr).strip()
        writer.writerow([pref, city, addr])
        written += 1

print(f"完了: {written} 行を書き込みました → {dst}")
