from datetime import date, datetime

from nadiem_sentimen.normalisasi import (
    bersihkan,
    daftar_emoji,
    fase_peristiwa,
    hanya_emoji,
    kunci_duplikat,
)


def test_bersihkan_melipat_huruf_mewah_dan_spasi():
    assert bersihkan("menang di #\U0001d5de\U0001d5e2\U0001d5df\U0001d5d8\U0001d5e0\U0001d5d4\U0001d5eb") == "menang di #KOLEMAX"
    assert bersihkan("  halo \n\n  dunia\t ") == "halo dunia"


def test_bersihkan_mempertahankan_emoji_dan_kapital():
    assert bersihkan("I AM CRYING 😭😭") == "I AM CRYING 😭😭"


def test_hanya_emoji():
    assert hanya_emoji("😭😭😭")
    assert hanya_emoji("🥺🥺💔💔")
    assert hanya_emoji("🤲🏻")          # dengan skin tone modifier
    assert hanya_emoji("😭 … 😭")       # tanda baca boleh menyertai
    assert not hanya_emoji("ok 😭")
    assert not hanya_emoji("...")
    assert not hanya_emoji("")


def test_daftar_emoji():
    assert daftar_emoji("sedih 😭💔 banget") == ["😭", "💔"]


def test_kunci_duplikat_menyamakan_varian_spam():
    a = kunci_duplikat("Alhamdulillah di kasih menang 7,2jt di ZOYAMAX 💸")
    b = kunci_duplikat("alhamdulillah dikasih menang 12,6jt di 𝗭𝗢𝗬𝗔𝗠𝗔𝗫!!")
    assert a == b


def test_kunci_duplikat_emoji_only_mengelompok():
    assert kunci_duplikat("😭😭😭") == kunci_duplikat("😭😭")
    assert kunci_duplikat("😭") != kunci_duplikat("💔")


def test_fase_peristiwa_batas():
    assert fase_peristiwa(date(2025, 9, 8)) == "f1_sep2025"
    assert fase_peristiwa(date(2026, 2, 8)) == "f2_awal2026"
    assert fase_peristiwa(datetime(2026, 5, 15, 12, 0)) == "f3_mei2026"
    assert fase_peristiwa(date(2026, 6, 28)) == "f3_mei2026"
    assert fase_peristiwa(date(2026, 6, 29)) == "f4_jul2026"
    assert fase_peristiwa(date(2026, 7, 11)) == "f4_jul2026"
