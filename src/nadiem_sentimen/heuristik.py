"""Heuristik lemah: indikasi spam dan pemetaan emoji → emosi.

Ini BUKAN detektor final — dipakai untuk stratifikasi sampling, sinyal lemah
saat pelabelan, dan aturan deterministik yang memang bisa di-rule-kan
(emosi komentar emoji-only). Keputusan akhir spam/sikap tetap milik model
yang dilatih dari label.
"""

from __future__ import annotations

import re
import unicodedata

from .normalisasi import daftar_emoji

# Kosakata khas spam judi/jasa/promo. Diterapkan pada teks yang sudah
# di-NFKC + casefold sehingga varian huruf mewah (𝗭𝗢𝗬𝗔𝗠𝗔𝗫) ikut tertangkap.
_SPAM = re.compile(
    r"slot|gacor|maxwin|max win|jackpot|jekpot|\bjp\b|\brtp\b|\bwd\b|"
    r"zoyamax|kolemax|dikasih menang|di kasih menang|bawa modal|modal \d+|"
    r"jasa bor|bor sumur|sedot wc|sumur bor|"
    r"olshop|open order|open jasa|promo|giveaway|cek profil|link di bio|"
    r"bonus new member|depo(?:sit)?\b"
)


def indikasi_spam(teks: str) -> bool:
    t = unicodedata.normalize("NFKC", teks).casefold()
    return bool(_SPAM.search(t))


# Pemetaan emoji → emosi untuk komentar emoji-only, sesuai
# skills/sentiment-labeling-id/SKILL.md. Urutan kemunculan pertama menang.
_EMOJI_EMOSI = {
    "duka": set("😭😢💔🥀🥺🥹🥲😔😞😥😪☹🙁😿"),
    "sinis": set("😂🤣😅😏🙃😆"),
    "marah": set("😡🤬💢👎😠"),
    "harapan": set("🙏🤲💪✊❤🔥🫶💚🤍❣💜🩷🧡💛💙👏🙌✨🌟😇"),
}


def emosi_dari_emoji(teks: str) -> str:
    for e in daftar_emoji(teks):
        for emosi, anggota in _EMOJI_EMOSI.items():
            if e in anggota:
                return emosi
    return "netral"
