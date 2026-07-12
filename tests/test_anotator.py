from nadiem_sentimen.anotator_llm import _cocokkan, _ekstrak_json, _valid
from nadiem_sentimen.model import KELAS_SIKAP, KELAS_EMOSI

SIKAP = set(KELAS_SIKAP)
EMOSI = set(KELAS_EMOSI)


def test_cocokkan_prefix():
    # Near-miss dari model (ornith) harus dipetakan ke kelas sah.
    assert _cocokkan("dukacita", EMOSI) == "duka"
    assert _cocokkan("duk", EMOSI) == "duka"
    assert _cocokkan("duk a", EMOSI) == "duka"
    assert _cocokkan("pro_nadiem", SIKAP) == "pro_nadiem"
    assert _cocokkan("PRO_NADIEM", SIKAP) == "pro_nadiem"


def test_cocokkan_ambigu_ditolak():
    # "k" cocok dengan banyak kelas sikap → tak boleh menebak.
    assert _cocokkan("k", SIKAP) is None
    assert _cocokkan("sesuatu", EMOSI) is None


def test_ekstrak_json_dari_pagar_kode():
    assert _ekstrak_json('```json\n{"spam": false, "sikap": "pro_nadiem", "emosi": "duka"}\n```') == \
        {"spam": False, "sikap": "pro_nadiem", "emosi": "duka"}
    assert _ekstrak_json('{"spam": true, "sikap": "tak_jelas", "emosi": "netral"}')["spam"] is True
    assert _ekstrak_json("bukan json sama sekali") == {}


def test_valid_spam_dipaksa_konsisten():
    # Spam harus selalu tak_jelas + netral apa pun kata modelnya.
    p = _valid({"spam": True, "sikap": "pro_nadiem", "emosi": "duka"})
    assert p.spam and p.sikap == "tak_jelas" and p.emosi == "netral"


def test_valid_kelas_asing_ditolak():
    assert _valid({"spam": False, "sikap": "marah", "emosi": "duka"}) is None  # sikap salah domain
