from address_matcher import (
    build_master_address,
    classify_score,
    match_single_row,
    normalize_text,
)


def test_normalize_text_unifies_common_variants():
    raw = " 保原町　元木88−4ヶ "
    normalized = normalize_text(raw)
    assert normalized == "保原町元木88-4ケ"


def test_match_single_row_prefecture_is_hard_filter():
    dental_row = {
        "都道府県": "福島県",
        "市区町村": "伊達市",
        "住所": "保原町元木88-4",
    }
    master_rows = [
        {"a": "北海道", "b": "札幌市", "c": "中央区", "d": "大通西", "e": ""},
        {"a": "福島県", "b": "伊達市", "c": "保原町", "d": "元木", "e": ""},
    ]

    result = match_single_row(dental_row, master_rows)

    assert result["matched_a"] == "福島県"
    assert result["matched_b"] == "伊達市"


def test_match_single_row_picks_most_similar_address_with_same_prefecture():
    dental_row = {
        "都道府県": "福島県",
        "市区町村": "伊達市",
        "住所": "上保原神明町18-3",
    }
    master_rows = [
        {"a": "福島県", "b": "伊達市", "c": "上保原", "d": "神明町", "e": ""},
        {"a": "福島県", "b": "伊達市", "c": "中町", "d": "", "e": ""},
    ]

    result = match_single_row(dental_row, master_rows)

    assert result["matched_c"] == "上保原"
    assert result["matched_d"] == "神明町"
    assert result["match_score"] >= 70


def test_match_single_row_requires_city_match_after_prefecture():
    dental_row = {
        "都道府県": "福島県",
        "市区町村": "伊達市",
        "住所": "保原町元木88-4",
    }
    master_rows = [
        {"a": "福島県", "b": "福島市", "c": "保原町", "d": "元木", "e": ""},
    ]

    result = match_single_row(dental_row, master_rows)

    assert result["match_status"] == "unmatched"
    assert result["matched_a"] == ""
    assert result["matched_b"] == ""


def test_classify_score_thresholds():
    assert classify_score(85) == "matched"
    assert classify_score(84.9) == "review"
    assert classify_score(70) == "review"
    assert classify_score(69.9) == "unmatched"


def test_build_master_address_handles_none_e_column():
    row = {"c": "中央区", "d": "大通西", "e": None}
    assert build_master_address(row) == "中央区大通西"
