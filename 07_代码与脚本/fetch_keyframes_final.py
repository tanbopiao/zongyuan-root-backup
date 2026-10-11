#!/usr/bin/env python3
import requests, json, os, datetime

KEY = "ms-673547d6-508b-4242-a862-85de112a3ce7"
IMG_DIR = "/home/user/ZONGYUAN-ROOT/02_数字媒体资产/图片/S2E01"
os.makedirs(IMG_DIR, exist_ok=True)

pending = [
    (1, "昆仑虚・玄女殿", "d026f51f-b302-4a40-ac57-f8c36cd8ad10"),
    (5, "月神破封・天幕剧变", "5c815fcb-02ed-43a7-8d84-90a88b96ffbf"),
]
for num, scene, tid in pending:
    try:
        q = requests.get(f"https://api-inference.modelscope.cn/v1/tasks/{tid}",
            headers={"Authorization": f"Bearer {KEY}", "X-ModelScope-Task-Type": "image_generation"}, timeout=20)
        qd = q.json()
        st = qd.get("task_status")
        imgs = qd.get("output_images", [])
        print(f"镜{num} {scene}: {st} images={len(imgs)}")
        if st == "SUCCEED" and imgs:
            url = imgs[0]
            img_r = requests.get(url, timeout=60)
            fpath = os.path.join(IMG_DIR, f"S2E01-镜{num:02d}-{scene}.png")
            with open(fpath, "wb") as f:
                f.write(img_r.content)
            print(f"  OK 下载成功 {len(img_r.content)}字节 -> {fpath}")
    except Exception as e:
        print(f"镜{num} 异常: {str(e)[:100]}")
