import asyncio, json, os, logging
from typing import List, Dict
from ..config import settings

logger = logging.getLogger("ffmpeg")

async def run_cmd(cmd: List[str]):
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        logger.error("FFmpeg error: %s", err.decode()[:500])
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return out, err

async def probe_media(path: str) -> Dict:
    cmd = ["ffprobe","-v","error","-print_format","json","-show_format","-show_streams", path]
    out, _ = await run_cmd(cmd)
    return json.loads(out.decode())

def filter_languages(streams: List[Dict], kind: str, allowed: List[str]) -> List[Dict]:
    result = []
    for s in streams:
        if s.get("codec_type") != kind: continue
        lang = (s.get("tags", {}) or {}).get("language", "und").lower()
        if lang in [a.lower() for a in allowed]:
            result.append(s)
    return result

async def apply_watermark_and_metadata(input_path: str, output_path: str, metadata: Dict, img: str = None, text: str = None):
    meta_args = []
    for k,v in metadata.items():
        meta_args += ["-metadata", f"{k}={v}"]
    filter_chain = []
    if img:
        filter_chain.append(f"movie={img}[wm];[in][wm]overlay=10:10[out]")
    if text:
        filter_chain.append(f"drawtext=text='{text}':x=20:y=50:fontsize=24:fontcolor=white")
    vf = ",".join(filter_chain) if filter_chain else None
    cmd = ["ffmpeg","-y","-i", input_path]
    if vf:
        cmd += ["-vf", vf]
    cmd += meta_args + ["-c","copy", output_path]
    await run_cmd(cmd)

async def transcode_variant(input_path: str, output_path: str, target_w: int, target_h: int, audio_langs: List[str], sub_langs: List[str]):
    probe = await probe_media(input_path)
    streams = probe.get("streams", [])
    audio_streams = filter_languages(streams, "audio", audio_langs)
    sub_streams = filter_languages(streams, "subtitle", sub_langs)
    map_args = ["-map", "0:v:0"]
    for a in audio_streams:
        map_args += ["-map", f"0:{a['index']}"]
    for s in sub_streams:
        map_args += ["-map", f"0:{s['index']}"]
    cmd = [
        "ffmpeg","-y","-i", input_path,
        *map_args,
        "-c:v","libx264","-preset","medium","-crf","20",
        "-vf", f"scale=w={target_w}:h={target_h}:force_original_aspect_ratio=decrease",
        "-c:a","aac","-b:a","128k",
        "-c:s","copy",
        output_path
    ]
    await run_cmd(cmd)

async def build_all_variants(original_input: str, work_dir: str, audio_langs: List[str], sub_langs: List[str]):
    outputs = {}
    for label, dims in settings.TARGET_RES_MAP.items():
        out_path = os.path.join(work_dir, f"{label}.mp4")
        await transcode_variant(original_input, out_path, dims["width"], dims["height"], audio_langs, sub_langs)
        outputs[label] = out_path
    outputs["original"] = original_input
    return outputs
