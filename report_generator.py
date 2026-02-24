import argparse
import csv
from collections import defaultdict
from pathlib import Path


def normalize_status(status: str) -> str:
    value = (status or "").strip().lower()
    if value in {"matched", "mathed"}:
        return "matched"
    if value in {"unmatched", "unmathed"}:
        return "unmatched"
    if value == "review":
        return "review"
    return "unmatched"


def build_counts(csv_path: Path) -> dict[str, dict[str, int]]:
    counts = defaultdict(lambda: {"matched": 0, "review": 0, "unmatched": 0, "total": 0})

    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            prefecture = (row.get("都道府県") or "").strip() or "不明"
            status = normalize_status(row.get("match_status", ""))
            counts[prefecture][status] += 1
            counts[prefecture]["total"] += 1

    return counts


def build_markdown(csv_name: str, counts: dict[str, dict[str, int]]) -> str:
    prefectures = sorted(counts.keys())
    grand_total = sum(counts[p]["total"] for p in prefectures)
    grand_matched = sum(counts[p]["matched"] for p in prefectures)
    grand_review = sum(counts[p]["review"] for p in prefectures)
    grand_unmatched = sum(counts[p]["unmatched"] for p in prefectures)

    lines = [
        "# 都道府県別 マッチ結果レポート",
        "",
        f"- 対象ファイル: {csv_name}",
        f"- 総件数: {grand_total}",
        f"- matched: {grand_matched}",
        f"- review: {grand_review}",
        f"- unmatched: {grand_unmatched}",
        "",
        "## 都道府県別件数",
        "",
        "| 都道府県 | matched | review | unmatched | 合計 |",
        "|---|---:|---:|---:|---:|",
    ]

    for prefecture in prefectures:
        row = counts[prefecture]
        lines.append(
            f"| {prefecture} | {row['matched']} | {row['review']} | {row['unmatched']} | {row['total']} |"
        )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="都道府県別のmatch_status件数をMarkdownで出力します")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/workspaces/address/address_matched_output.csv"),
        help="集計対象のCSVファイル",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/workspaces/address/match_status_report_by_prefecture.md"),
        help="出力するMarkdownファイル",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = build_counts(args.input)
    markdown = build_markdown(args.input.name, counts)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"report written: {args.output}")


if __name__ == "__main__":
    main()
