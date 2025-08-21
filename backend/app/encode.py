
import os, shutil
from .utils import run, ffprobe_info, detect_props
from .settings import load_app, load_bitrates, bitrate_for
from .logs import write as log

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def needs_reencode(src_info, cfg, target_codec, target_bitrate):
    codec = (src_info.get("codec") or "").lower()
    pix = (src_info.get("pix_fmt") or "").lower()
    dovi = bool(src_info.get("dovi"))
    br = int(src_info.get("bitrate_kbps") or 0)

    if dovi:
        return True

    if target_codec == "hevc":
        codec_ok = codec in ("hevc","h265")
    elif target_codec == "h264":
        codec_ok = codec in ("h264","avc1")
    else:
        codec_ok = codec in ("av1",)

    if codec_ok and (br == 0 or br <= target_bitrate + 500):
        return False
    return True

def build_ffmpeg_cmd(src, dst, cfg, props, target_bitrate_kbps, assigned_gpu, target_codec):
    gpu_list = cfg.get("gpu_indices") or []
    use_gpu = len(gpu_list) > 0

    # Choix encodeur + profil + profondeur (8-bit SDR, 10-bit HDR)
    is_hdr = bool(props.get("hdr"))
    if target_codec == "hevc":
        venc = "hevc_nvenc" if use_gpu else "libx265"
        pixfmt = "p010le" if is_hdr else "yuv420p"  # SDR 8-bit
        vprofile = "main10" if is_hdr else "main"
        nvenc_rc = "-rc vbr" if use_gpu else ""
    elif target_codec == "h264":
        venc = "h264_nvenc" if use_gpu else "libx264"
        pixfmt = "yuv420p"
        vprofile = "high"
        nvenc_rc = "-rc vbr" if use_gpu else ""
    else:
        venc = "av1_nvenc" if use_gpu else "libaom-av1"
        pixfmt = "p010le" if is_hdr else "yuv420p10le"  # AV1 10-bit recommandé
        vprofile = "main"
        nvenc_rc = "-rc vbr" if use_gpu and "nvenc" in venc else ""

    # HW accel lecture + sélection GPU
    hwaccel = f"-hwaccel cuda -hwaccel_output_format cuda -extra_hw_frames 8" if use_gpu else ""
    gpu_index = assigned_gpu if use_gpu else None
    devsel = f"-init_hw_device cuda=cu:{gpu_index} -filter_hw_device cu" if use_gpu and gpu_index is not None else ""

    # Audio adaptatif: stéréo → 2ch, sinon 6ch
    channels = 6 if int((props.get("audio_channels") or 0)) > 2 else 2
    aac_bitrate = 384 if channels == 2 else 640

    # Utiliser cache pour le fichier temporaire
    cache_dir = (cfg.get("cache_path") or os.path.dirname(dst))
    os.makedirs(cache_dir, exist_ok=True)
    tmp = os.path.join(cache_dir, os.path.basename(dst) + ".tmp.mkv")

    cmd = (
        f'ffmpeg -y {hwaccel} {devsel} -i "{src}" '
        f'-map 0:v:0 -map 0:a? -map 0:s? '
        f'-c:v {venc} -pix_fmt {pixfmt} -profile:v {vprofile} -b:v {target_bitrate_kbps}k {nvenc_rc} '
        f'-c:a aac -b:a {aac_bitrate}k -ac {channels} -c:s copy '
        f'-max_muxing_queue_size 1024 "{tmp}"'
    )
    return cmd, tmp

def health_check(path):
    info = ffprobe_info(path)
    v = [s for s in info.get("streams",[]) if s.get("codec_type")=="video"]
    a = [s for s in info.get("streams",[]) if s.get("codec_type")=="audio"]
    return bool(v) and bool(a)

def process_file(src_path, dst_path, assigned_gpu=None):
    cfg = load_app()
    bit = load_bitrates()
    info_raw = ffprobe_info(src_path)
    props = detect_props(info_raw)
    props["src_path"] = src_path

    target_codec = cfg.get("video_codec","hevc")
    target_bitrate = bitrate_for(props, cfg, bit)

    if not needs_reencode(props, cfg, target_codec, target_bitrate):
        log(f"[skip] {os.path.basename(src_path)} (already compliant)")
        ensure_dir(dst_path)
        shutil.copy2(src_path, dst_path)
        return True, "skipped"

    ensure_dir(dst_path)
    cmd, tmp = build_ffmpeg_cmd(src_path, dst_path, cfg, props, target_bitrate, assigned_gpu, target_codec)
    log(f"[encode] {os.path.basename(src_path)} -> {os.path.basename(dst_path)} "
        f"({props.get('codec','?')} {props.get('width')}x{props.get('height')} "
        f"{'HDR' if props.get('hdr') else 'SDR'} -> {target_codec.upper()} {target_bitrate}kbps) "
        f"{'(GPU '+str(assigned_gpu)+')' if assigned_gpu is not None else '(CPU)'}")
    code, out = run(cmd)
    if code != 0:
        log(f"[error] ffmpeg failed on {src_path}: {out[-1000:]}")
        return False, "ffmpeg_failed"

    if not health_check(tmp):
        log(f"[error] health check failed for {tmp}")
        return False, "health_check_failed"

    try:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        os.replace(tmp, dst_path)
    except Exception:
        shutil.move(tmp, dst_path)
    log(f"[done]  {os.path.basename(src_path)} -> {os.path.basename(dst_path)}")
    return True, "done"
