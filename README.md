# SimplAarr — Transcodeur GPU simple et pro (Tdarr killer)

**Port par défaut : 8000** — UI web et API REST.

## Ce que fait SimplAarr
- Encode HEVC/H264/AV1 GPU (NVENC), Main10 si HDR, bitrates cibles par résolution (4K HDR ~18 Mb/s, 4K SDR ~16 Mb/s, 1080p ~8 Mb/s, etc.).
- Supprime Dolby Vision, conserve toutes les pistes de sous-titres.
- Audio : toutes les pistes en AAC 640 kb/s.
- Mirroring : `/media/Films/x.mkv` → `/media-encoded/Films/x.mkv`.
- Base SQLite (pending/processing/done/failed), re-scan toutes les 6h.
- Multi-GPU & Workers, dashboard moderne, logs live.

## Installation (Docker)
```bash
docker compose up -d
```
UI : http://localhost:8000

Volumes :
- `./media` → `/media` (RO)
- `./media-encoded` → `/media-encoded`
- `./config` → `/config` (`app.json`, `bitrates.json`)
- `./logs` → `/logs`
- `./data` → `/data`
- `./cache` → `/cache`

## Configuration
Tout via l’onglet **Settings** (ou JSON dans `config/`).

## API rapide
- `GET /api/stats`, `POST /api/scan`, `GET /api/gpus`, `GET /api/settings`…

---
