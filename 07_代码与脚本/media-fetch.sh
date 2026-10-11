#!/usr/bin/env bash
# ============================================================
# ZONGYUAN-ROOT 生成即下载机制 V1.1
# 策略：下载到临时文件 → file 检测真实类型 → 按类型归档
#       aka CDN 不回标准 Content-Type，故不依赖 HEAD
# 用法：
#   ./media-fetch.sh <aka_url> [aka_url2 ...]
#   cat links.txt | ./media-fetch.sh -
# ============================================================
set -u

MEDIA_ROOT="/home/user/ZONGYUAN-ROOT/02_数字媒体资产"
DATE=$(date +%Y%m%d)
VIDEO_DIR="$MEDIA_ROOT/视频/云端产物恢复-$DATE"
IMAGE_DIR="$MEDIA_ROOT/图片/云端产物恢复-$DATE"
OTHER_DIR="$MEDIA_ROOT/其他产物恢复-$DATE"
LOG_FILE="$MEDIA_ROOT/媒体下载台账.csv"
UA="Mozilla/5.0 ZR-MEDIA-FETCH/1.1"
TMP=$(mktemp -d)

mkdir -p "$VIDEO_DIR" "$IMAGE_DIR" "$OTHER_DIR"
[ -f "$LOG_FILE" ] || echo "timestamp,aka_id,kind,size_bytes,source_url,save_path,status" > "$LOG_FILE"

# 已存在则返回已有路径
find_existing() {
    local id="$1"
    find "$MEDIA_ROOT" -name "aka_${id}.*" -type f 2>/dev/null | head -1
}

fetch_one() {
    local url="$1"
    local id=$(echo "$url" | grep -oE 's/[A-Za-z0-9_-]+' | head -1 | sed 's|s/||')
    [ -z "$id" ] && { echo "  ⚠ 无法解析 aka id: $url"; return; }

    local existing=$(find_existing "$id")
    if [ -n "$existing" ]; then
        echo "  ⏭ 已存在跳过: $(basename "$existing")"
        echo "$(date -Iseconds),$id,existing,-,$url,$existing,skipped" >> "$LOG_FILE"
        return
    fi

    local tmpf="$TMP/${id}.bin"
    local http=$(curl -sL -m 120 -A "$UA" -w "%{http_code}" -o "$tmpf" "$url")
    if [ "$http" != "200" ] || [ ! -s "$tmpf" ]; then
        echo "  ❌ 不可用 http=$http: $url"
        echo "$(date -Iseconds),$id,-,-,$url,-,fail_$http" >> "$LOG_FILE"
        rm -f "$tmpf"; return
    fi

    local ft=$(file -b "$tmpf")
    local dest kind ext
    case "$ft" in
        *"WebM"*|*"Matroska"*|*"MPEG"*"Movie"*|*"MP4"*|*"ISO Media"*)
            kind="video"; dest="$VIDEO_DIR/aka_${id}.mp4"; ext=".mp4" ;;
        *"JPEG"*|*"PNG"*|*"WebP"*|*"GIF"*|*"bitmap"*|*"image"*)
            kind="image"; dest="$IMAGE_DIR/aka_${id}.jpg" ;;
        *"HTML"*|*"HTML document"*)
            kind="html"; dest="$OTHER_DIR/aka_${id}.html" ;;
        *)
            kind="other"; dest="$OTHER_DIR/aka_${id}.bin" ;;
    esac

    mv "$tmpf" "$dest"
    local sz=$(stat -c%s "$dest")
    echo "  ✅ 落盘 [$kind] $(basename "$dest")  ($((sz/1024))KB)"
    echo "$(date -Iseconds),$id,$kind,$sz,$url,$dest,ok" >> "$LOG_FILE"
}

main() {
    if [ "${1:-}" = "-" ]; then
        while read -r u; do [ -n "$u" ] && fetch_one "$u"; done
    else
        for u in "$@"; do fetch_one "$u"; done
    fi
    rm -rf "$TMP"
    echo "---"
    echo "视频: $VIDEO_DIR"
    echo "图片: $IMAGE_DIR"
    echo "台账: $LOG_FILE"
}
main "$@"
