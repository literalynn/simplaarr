# SimplAarr — Transcodeur GPU simple et pro (Tdarr killer)

**Port par défaut : 8000** — UI web et API REST.

## Ce que fait SimplAarr
- Encode HEVC/H264/AV1 GPU (NVENC), Main10 si HDR, SDR en 8-bit, bitrates cibles par résolution (4K HDR ~18 Mb/s, 4K SDR ~16 Mb/s, 1080p ~8 Mb/s, etc.).
- Supprime Dolby Vision, conserve toutes les pistes de sous-titres.
- Audio : AAC adaptatif (2.0 → 384 kb/s, ≥5.1 → 640 kb/s).
- Mirroring : `/media/Films/x.mkv` → `/media-encoded/Films/x.mkv`.
- Base SQLite (pending/processing/done/failed) optimisée (WAL), re-scan toutes les 6h.
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
Tout via l’onglet **Settings** (ou JSON dans `config/`). Si `config/app.json` et `config/bitrates.json` sont absents, ils sont créés avec des valeurs par défaut.

## API rapide
- `GET /api/stats`, `POST /api/scan`, `GET /api/gpus`, `GET /api/settings`…
## GPU / NVENC
Docker compose est configuré avec `gpus: all`. Assurez-vous d’avoir le runtime NVIDIA installé. L’image de base peut nécessiter un FFmpeg compilé avec NVENC si vous ciblez l’encodage GPU.

---
