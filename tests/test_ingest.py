import textwrap
from pathlib import Path

import pytest

from nadiem_sentimen.ingest import muat_dataset, parse_csv

DATASET_ASLI = Path(__file__).resolve().parents[1] / "dataset"


def _tulis(tmp_path: Path, nama: str, isi: str) -> Path:
    path = tmp_path / nama
    path.write_text(textwrap.dedent(isi), encoding="utf-8")
    return path


def test_timestamp_pecah_dua_field(tmp_path):
    path = _tulis(
        tmp_path,
        "ABC123.csv",
        '''\
        username,timestamp,likes,komentar
        budi,30/6/2026, 21.43.41,4,"Gak ikhlas banget gw. Gaji dinaikin, kerjanya begini"
        ''',
    )
    hasil = parse_csv(path)
    assert not hasil.anomali
    (k,) = hasil.komentar
    assert k.post == "ABC123"
    assert k.waktu.isoformat() == "2026-06-30T21:43:41"
    assert k.likes == 4
    assert k.teks.startswith("Gak ikhlas")


def test_kutip_ganda_dan_koma_dalam_komentar(tmp_path):
    path = _tulis(
        tmp_path,
        "X.csv",
        '''\
        username,timestamp,likes,komentar
        ani,1/7/2026, 08.53.58,67,"BURU"" BGT, NIH"
        ''',
    )
    (k,) = parse_csv(path).komentar
    assert k.teks == 'BURU" BGT, NIH'


def test_komentar_multibaris(tmp_path):
    path = _tulis(
        tmp_path,
        "X.csv",
        '''\
        username,timestamp,likes,komentar
        cak,2/7/2026, 10.00.00,0,"baris satu
        baris dua"
        ''',
    )
    (k,) = parse_csv(path).komentar
    assert "baris satu\nbaris dua" in k.teks


def test_skema_threaded(tmp_path):
    path = _tulis(
        tmp_path,
        "T.csv",
        '''\
        type,parent_id,username,timestamp,likes,komentar
        PARENT,NONE,vko,14/5/2026, 17.24.00,216,"heartbroken"
        REPLY,abc,dwi,14/5/2026, 18.00.00,2,"iya bener"
        ''',
    )
    hasil = parse_csv(path)
    assert [k.is_reply for k in hasil.komentar] == [False, True]
    assert hasil.komentar[0].username == "vko"


def test_timestamp_terkutip_utuh(tmp_path):
    path = _tulis(
        tmp_path,
        "Q.csv",
        '''\
        username,timestamp,likes,komentar
        edo,"3/7/2026, 09.15.02",12,"oke"
        ''',
    )
    hasil = parse_csv(path)
    assert not hasil.anomali
    assert hasil.komentar[0].waktu.isoformat() == "2026-07-03T09:15:02"


def test_baris_rusak_jadi_anomali_bukan_tebakan(tmp_path):
    path = _tulis(
        tmp_path,
        "R.csv",
        '''\
        username,timestamp,likes,komentar
        fia,bukan-tanggal,4,"halo"
        gus,4/7/2026, 11.00.00,xx,"likes bukan angka"
        ''',
    )
    hasil = parse_csv(path)
    assert not hasil.komentar
    assert len(hasil.anomali) == 2


@pytest.mark.skipif(not DATASET_ASLI.exists(), reason="folder dataset/ tidak ada")
def test_dataset_asli_utuh():
    hasil = muat_dataset(DATASET_ASLI)
    assert len(hasil.komentar) == 38845
    assert hasil.anomali == []
    assert all(k.likes >= 0 for k in hasil.komentar)
    assert {k.post for k in hasil.komentar} == {p.stem for p in DATASET_ASLI.glob("*.csv")}
