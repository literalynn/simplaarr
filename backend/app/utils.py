
import subprocess, json

def run(cmd, cwd=None):
    p = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = []
    for line in p.stdout:
        output.append(line)
    code = p.wait()
    return code, "".join(output)

def ffprobe_info(path):
    cmd = f'ffprobe -v error -print_format json -show_streams -show_format "{path}"'
    code, out = run(cmd)
    if code != 0:
        return {}
    try:
        return json.loads(out)
    except Exception:
        return {}

def detect_props(info):
    streams = info.get("streams", [])
    vstreams = [s for s in streams if s.get("codec_type")=="video"]
    astreams = [s for s in streams if s.get("codec_type")=="audio"]
    if not vstreams:
        # Même si aucune vidéo détectée, on renvoie au moins des infos audio
        channels = 0
        for a in astreams:
            try:
                channels = max(channels, int(a.get("channels") or 0))
            except Exception:
                pass
        return {"audio_channels": channels or 0}
    v = vstreams[0]
    width = v.get("width")
    height = v.get("height")
    codec = v.get("codec_name")
    pix = v.get("pix_fmt")
    bs = v.get("bit_rate") or info.get("format",{}).get("bit_rate") or 0
    try:
        br_kbps = int(int(bs)/1000) if bs else 0
    except Exception:
        br_kbps = 0
    color_primaries = v.get("color_primaries","")
    transfer = v.get("color_transfer","")
    matrix = v.get("color_space","")
    hdr = color_primaries in ("bt2020","bt2020nc") or "smpte2084" in transfer or "2020" in (matrix or "")
    text = json.dumps(info).lower()
    dovi = ("dolby vision" in text) or ("dovi" in text) or ("dv_profile" in text) or ("com.apple.proapps.dovi" in text)
    channels = 0
    for a in astreams:
        try:
            channels = max(channels, int(a.get("channels") or 0))
        except Exception:
            pass
    return {
        "width": width, "height": height, "bitrate_kbps": br_kbps,
        "codec": codec, "pix_fmt": pix, "hdr": hdr, "dovi": dovi,
        "audio_channels": channels or 0
    }
