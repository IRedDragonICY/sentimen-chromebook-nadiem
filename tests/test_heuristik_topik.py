from nadiem_sentimen.heuristik import emosi_dari_emoji, indikasi_spam
from nadiem_sentimen.topik import topik_komentar


def test_spam_terdeteksi_setelah_nfkc():
    # Huruf "mewah" 𝗞𝗢𝗟𝗘𝗠𝗔𝗫 harus tertangkap via normalisasi NFKC.
    assert indikasi_spam("Alhamdulillah dikasih menang 12,6jt di #\U0001d5de\U0001d5e2\U0001d5df\U0001d5d8\U0001d5e0\U0001d5d4\U0001d5eb")
    assert indikasi_spam("main slot gacor maxwin")
    assert indikasi_spam("JASA BOR AIR SUMUR melayani jabodetabek")
    assert not indikasi_spam("Allah bersama bapak Nadiem")
    assert not indikasi_spam("rpy. 4r r.")  # gibberish, bukan spam


def test_emosi_dari_emoji():
    assert emosi_dari_emoji("😭😭😭") == "duka"
    assert emosi_dari_emoji("😂😂") == "sinis"
    assert emosi_dari_emoji("🙏🤲") == "harapan"
    assert emosi_dari_emoji("😡🤬") == "marah"
    assert emosi_dari_emoji("👀") == "netral"


def test_topik_multi():
    t = topik_komentar("Inilah fungsi menaikkan gaji hakim 280% biar bisa vonis pesanan")
    assert "gaji_hakim" in t and "peradilan" in t
    assert "chromebook" in topik_komentar("Chromebook dari google mahal, mark up")
    assert "politik" in topik_komentar("TURUNKAN PRABOWO, mulyono juga diadili")
    assert topik_komentar("😭😭😭") == []
