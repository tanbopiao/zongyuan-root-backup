#!/usr/bin/env python3
# ffmpeg 合成工具（免费，本地）
import subprocess, os
OUT="/home/user/Doubao/chats/38438491307070978/media_assets/output"
def compose(segments, out_name="final.mp4"):
    # segments: [file.mp4,...] 拼接
    listf=OUT+"/list.txt"
    open(listf,"w").write("\n".join(f"file '{s}'" for s in segments))
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",listf,"-c","copy",OUT+"/"+out_name],check=True)
    return OUT+"/"+out_name
print("[compose] ffmpeg合成工具就绪")
