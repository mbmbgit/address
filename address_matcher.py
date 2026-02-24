import argparse
import csv
import re
import time
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


MATCH_COLUMNS = [
    "matched_a",
    "matched_b",
    "matched_c",
    "matched_d",
    "matched_e",
    "match_score",
    "match_status",
]

OUTPUT_MATCH_COLUMNS = [
    "都道府県_候補",
    "市区町村_候補",
    "住所c_候補",
    "住所d_候補",
    "住所e_候補",
    "match_score",
    "match_status",
    "不一致理由",
]

SOURCE_ADDRESS_COLUMNS = ["都道府県", "市区町村", "住所"]


DEFAULT_DENTAL_PATH = Path("/workspaces/address/dental_new_tohoku_kanto.csv")
DEFAULT_MASTER_PATH = Path("/workspaces/address/adress_degital_cho .csv")
DEFAULT_OUTPUT_PATH = Path("/workspaces/address/address_matched_output.csv")


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(text)).strip()
    normalized = re.sub(r"\s+", "", normalized)
    normalized = normalized.replace("−", "-").replace("ー", "-")
    normalized = normalized.replace("ヶ", "ケ")
    return normalized


def build_master_address(row: dict) -> str:
    c = row.get("c") or ""
    d = row.get("d") or ""
    e = row.get("e") or ""
    return normalize_text(f"{c}{d}{e}")


def bigram_jaccard(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if len(a) == 1 and len(b) == 1:
        return 1.0 if a == b else 0.0
    a_set = {a[i : i + 2] for i in range(max(len(a) - 1, 1))}
    b_set = {b[i : i + 2] for i in range(max(len(b) - 1, 1))}
    union = a_set | b_set
    if not union:
        return 0.0
    return len(a_set & b_set) / len(union)


def similarity_score(query_address: str, candidate_address: str, city_match: bool) -> float:
    if not query_address and not candidate_address:
        return 0.0
    seq = SequenceMatcher(None, query_address, candidate_address).ratio() * 100
    jac = bigram_jaccard(query_address, candidate_address) * 100
    contains_bonus = 0.0
    if candidate_address and query_address:
        if candidate_address in query_address or query_address in candidate_address:
            contains_bonus = 15.0
    city_bonus = 10.0 if city_match else 0.0
    score = (0.65 * seq) + (0.35 * jac) + contains_bonus + city_bonus
    return min(100.0, score)


def classify_score(score: float) -> str:
    if score >= 85:
        return "matched"
    if score >= 70:
        return "review"
    return "unmatched"


def _empty_match_result() -> dict:
    return {
        "matched_a": "",
        "matched_b": "",
        "matched_c": "",
        "matched_d": "",
        "matched_e": "",
        "match_score": 0.0,
        "match_status": "unmatched",
    }


def _match_from_candidates(dental_row: dict, candidates: list[dict]) -> dict:
    addr = normalize_text(dental_row.get("住所", ""))

    best_row = None
    best_score = -1.0
    for row in candidates:
        candidate_addr = build_master_address(row)
        score = similarity_score(addr, candidate_addr, city_match=True)
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is None:
        return _empty_match_result()

    return {
        "matched_a": best_row.get("a", ""),
        "matched_b": best_row.get("b", ""),
        "matched_c": best_row.get("c", ""),
        "matched_d": best_row.get("d", ""),
        "matched_e": best_row.get("e", ""),
        "match_score": round(best_score, 2),
        "match_status": classify_score(best_score),
    }


def build_master_index(master_rows: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in master_rows:
        pref = normalize_text(row.get("a", ""))
        city = normalize_text(row.get("b", ""))
        index[pref][city].append(row)
    return index


def match_single_row(dental_row: dict, master_rows: list[dict]) -> dict:
    pref = normalize_text(dental_row.get("都道府県", ""))
    city = normalize_text(dental_row.get("市区町村", ""))
    pref_rows = [r for r in master_rows if normalize_text(r.get("a", "")) == pref]
    if not pref_rows:
        return _empty_match_result()

    city_rows = [r for r in pref_rows if normalize_text(r.get("b", "")) == city]
    if not city_rows:
        return _empty_match_result()

    return _match_from_candidates(dental_row, city_rows)

def read_csv_rows(path: Path) -> tuple[list[dict], list[str], int]:
    with path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile, restkey="__extra__", restval="")
        original_fieldnames = reader.fieldnames or []
        rows: list[dict] = []
        malformed_row_count = 0

        for row in reader:
            extras = row.pop("__extra__", None)
            if extras:
                malformed_row_count += 1

            if None in row:
                row.pop(None, None)
                malformed_row_count += 1

            clean_row = {key: (value if value is not None else "") for key, value in row.items()}
            rows.append(clean_row)

        return rows, original_fieldnames, malformed_row_count


def write_csv_rows(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(
    dental_path: Path,
    master_path: Path,
    output_path: Path,
    progress_every: int = 500,
    show_progress: bool = True,
) -> None:
    dental_rows, _, dental_malformed = read_csv_rows(dental_path)
    master_rows, _, master_malformed = read_csv_rows(master_path)

    if dental_malformed > 0 or master_malformed > 0:
        print(
            f"warning: malformed rows detected dental={dental_malformed}, master={master_malformed}. "
            "extra columns were ignored and missing columns were treated as empty.",
            flush=True,
        )

    master_index = build_master_index(master_rows)
    total = len(dental_rows)
    started_at = time.perf_counter()

    output_rows = []
    for i, dental_row in enumerate(dental_rows, start=1):
        pref = normalize_text(dental_row.get("都道府県", ""))
        city = normalize_text(dental_row.get("市区町村", ""))
        pref_bucket = master_index.get(pref, {})
        city_candidates = pref_bucket.get(city, [])

        mismatch_reason = ""
        if not pref_bucket:
            match_result = _empty_match_result()
            mismatch_reason = "都道府県一致なし"
        elif not city_candidates:
            match_result = _empty_match_result()
            mismatch_reason = "市区町村一致なし"
        else:
            match_result = _match_from_candidates(dental_row, city_candidates)
            if match_result["match_status"] == "unmatched":
                mismatch_reason = "住所類似度しきい値未満"

        merged = {column: dental_row.get(column, "") for column in SOURCE_ADDRESS_COLUMNS}
        merged.update(
            {
                "都道府県_候補": match_result["matched_a"],
                "市区町村_候補": match_result["matched_b"],
                "住所c_候補": match_result["matched_c"],
                "住所d_候補": match_result["matched_d"],
                "住所e_候補": match_result["matched_e"],
                "match_score": match_result["match_score"],
                "match_status": match_result["match_status"],
                "不一致理由": mismatch_reason,
            }
        )
        output_rows.append(merged)

        if show_progress and total > 0 and (i % progress_every == 0 or i == total):
            elapsed = time.perf_counter() - started_at
            percent = (i / total) * 100
            speed = i / elapsed if elapsed > 0 else 0.0
            print(
                f"progress: {i}/{total} ({percent:.1f}%) elapsed={elapsed:.1f}s speed={speed:.1f} rows/s",
                flush=True,
            )

    if not output_rows:
        return

    fieldnames = SOURCE_ADDRESS_COLUMNS + OUTPUT_MATCH_COLUMNS
    write_csv_rows(output_path, output_rows, fieldnames)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="住所CSVを都道府県一致+類似度でマッチングします")
    parser.add_argument("--dental", type=Path, default=DEFAULT_DENTAL_PATH)
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--progress-every", type=int, default=500)
    parser.add_argument("--no-progress", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        args.dental,
        args.master,
        args.output,
        progress_every=max(1, args.progress_every),
        show_progress=not args.no_progress,
    )
    print(f"matched file written: {args.output}")


if __name__ == "__main__":
    main()
