# Error Log

Tidak ada error indexing yang belum terselesaikan.

## Resolved events

1. Attempt awal berhenti sebelum insert batch karena nilai `ttl_days=NOT_APPLICABLE`
   tidak dapat dikonversi menjadi integer. Loader diperbaiki untuk mempertahankan nilai
   eksplisit tersebut sebagai metadata non-numerik, sementara TTL numerik tetap disimpan
   sebagai integer. Tidak ada input yang diubah.
2. Setelah batch selesai, pembuatan file resume-test berhenti karena import modul `math`
   belum tersedia. Import ditambahkan dan proses dijalankan kembali. Seluruh 10 batch
   COMPLETE terdeteksi lalu dilewati tanpa reinsertion.

Hasil akhir tetap 306 record, reload PASS, smoke test 7/7 PASS, dan QA 18/18 PASS.
Tindakan recovery database, jika ada, dicatat pada `05_qa/recovery_actions.json`.
