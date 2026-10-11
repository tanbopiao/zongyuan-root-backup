# 生成即下载机制 V1.1（media-fetch.sh）

## 目的
视频/图片 aka 短链一经出现，立即 curl 落盘权威媒体根，杜绝"只有链接没有实体"。

## 用法
```bash
# 单个链接（自动判定视频/图片/其他）
bash /home/user/ZONGYUAN-ROOT/07_代码与脚本/media-fetch.sh "https://aka.doubaocdn.com/s/XXXX"

# 批量
bash /home/user/ZONGYUAN-ROOT/07_代码与脚本/media-fetch.sh "链接1" "链接2" "链接3"

# 从文件批量
cat links.txt | bash /home/user/ZONGYUAN-ROOT/07_代码与脚本/media-fetch.sh -
```

## 工作原理
1. 提取 aka id → 全库查是否已存在（去重，已存跳过）
2. curl 下载到临时文件
3. `file` 命令按真实二进制类型判定（不依赖不可靠的 HTTP Content-Type）
4. 视频→`02_数字媒体资产/视频/云端产物恢复-YYYYMMDD/`
   图片→`02_数字媒体资产/图片/云端产物恢复-YYYYMMDD/`
   其他(HTML/bin)→`02_数字媒体资产/其他产物恢复-YYYYMMDD/`
5. 写台账 `02_数字媒体资产/媒体下载台账.csv`

## 接入约定（元法则）
每次视频/图片生成任务完成后，**必须**：
- 提取所有 aka.doubaocdn.com 链接
- 调用本脚本批量落盘
- 再进入下一步（如发布/锁档）

## 自测记录（2026-09-21）
- 已存在视频链接 → 跳过 ✅
- 图片链接 → 落图片目录 1.1MB ✅
- 失效/403 链接 → 容错不崩溃 ✅
