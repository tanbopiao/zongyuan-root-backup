#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory_index_engine.py · AI 持久化记忆索引引擎 V1.0
====================================================
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | ZR-NODE-DC2E51C0

设计落地: 三层索引(标签倒排 + 语义向量 + 时效衰减)
  - 标签体系: tag_type / tag_topic / tag_entity / tag_attr 四类分层
  - 检索权重: Score = 0.4·TagScore + 0.4·VecScore + 0.2·FreshScore
  - 时效衰减: Decay(Δt)=1/(1+(Δt/T_half)^k)，被检索命中→Δt归零(热度刷新)
  - 生命周期: 写入建索引→检索刷新→老化降权→阈值+临时→归档冷存

纯标准库实现, 无第三方依赖。VecScore 默认用字符n-gram词袋余弦,
可替换为真实 embedding 接口(见 _vectorize 注释)。

用法:
  from memory_index_engine import MemoryIndexEngine
  eng = MemoryIndexEngine("index.json")
  eng.add_memory("mem-1", "用户偏好中文回复", {"type":"偏好","topic":"交流"}, half_life_days=365)
  eng.add_memory("mem-2", "昨日完成任务A", {"type":"任务","topic":"项目A"}, half_life_days=30)
  res = eng.search("用户喜欢什么语言", top_k=5)
"""
import json, os, time, math, re, hashlib
from collections import defaultdict

# ===================== 默认权重与衰减参数 =====================
ALPHA = 0.4   # 标签相关度权重
BETA  = 0.4   # 语义相似度权重
GAMMA = 0.2   # 时效衰减权重
K_DECAY = 1.0 # 衰减陡度
EPSILON_ARCHIVE = 0.05  # 归档阈值

DEFAULT_HALF_LIFE = {"临时": 7, "任务": 30, "偏好": 365, "事实": 180}

# ===================== 记忆索引引擎 =====================
class MemoryIndexEngine:
    """AI 持久化记忆索引引擎: 标签倒排 + 向量 + 时效衰减 三层融合检索"""

    def __init__(self, store_path="memory_index.json"):
        self.store_path = store_path
        self.memories = {}       # mem_id -> memory record
        self.tag_inverted = defaultdict(set)  # tag -> {mem_id,...} 倒排索引
        self.tag_weight = defaultdict(float)  # tag -> 累积权重(标签自身生命周期)
        self.df = defaultdict(int)   # 特征 -> 出现文档数 (TF-IDF语义向量)
        self.doc_count = 0           # 文档总数
        self._load()

    # ---------- 持久化 ----------
    def _load(self):
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.memories = data.get("memories", {})
            self.tag_inverted = {k: set(v) for k, v in data.get("inverted", {}).items()}
            self.tag_weight = defaultdict(float, data.get("tag_weight", {}))
            self.df = defaultdict(int, data.get("df", {}))
            self.doc_count = data.get("doc_count", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self):
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump({
                "memories": self.memories,
                "inverted": {k: list(v) for k, v in self.tag_inverted.items()},
                "tag_weight": dict(self.tag_weight),
                "df": dict(self.df),
                "doc_count": self.doc_count,
            }, f, ensure_ascii=False, indent=2)

    # ---------- 写入 ----------
    def add_memory(self, mem_id, content, tags, half_life_days=None,
                   tag_type=None, importance=1.0):
        """写入一条记忆并建索引. tags: 四类标签dict或list.
        half_life_days 缺省按 tag_attr 类型推断."""
        now = time.time()
        # 归一化标签: 支持 {类:值} 或 [值,...]
        tag_list = []
        tag_attr = []
        if isinstance(tags, dict):
            for cls, val in tags.items():
                vals = val if isinstance(val, list) else [val]
                for v in vals:
                    t = f"{cls}:{v}"
                    tag_list.append(t)
                    if cls == "attr":
                        tag_attr.append(v)
        else:
            tag_list = [str(t) for t in tags]

        if half_life_days is None:
            # 按属性推断半衰期
            half_life_days = max(
                (DEFAULT_HALF_LIFE.get(a, 180) for a in tag_attr), default=180
            )

        self.memories[mem_id] = {
            "content": content,
            "tags": tag_list,
            "half_life_days": half_life_days,
            "created_at": now,
            "last_access": now,
            "access_count": 0,
            "importance": importance,
            "archived": False,
        }
        # 更新倒排索引 + 标签权重 + 文档频率(TF-IDF)
        self.doc_count += 1
        for feat in set(self._analyze(content)):
            self.df[feat] += 1
        for t in tag_list:
            self.tag_inverted[t].add(mem_id)
            self.tag_weight[t] += 1.0
        self.save()

    # ---------- 向量化(TF-IDF 语义向量, 本地无监督零额度) ----------
    def _analyze(self, text):
        """特征提取: 英文单词 + 中文2-gram."""
        s = str(text).lower()
        feats = []
        for w in re.findall(r"[a-z0-9]+", s):
            if len(w) >= 2:
                feats.append("w:" + w)
        # 中文连续串切2-gram
        for seg in re.findall(r"[\u4e00-\u9fa5]{2,}", s):
            for i in range(len(seg) - 1):
                feats.append("c:" + seg[i:i+2])
        return feats

    def _vectorize(self, text):
        """TF-IDF 加权向量. 区别于纯n-gram: 罕见特征权重大, 常见词被抑制."""
        feats = self._analyze(text)
        tf = defaultdict(int)
        for f in feats:
            tf[f] += 1
        total = len(feats) or 1
        vec = {}
        N = max(self.doc_count, 1)
        for f, c in tf.items():
            tfidf = (c / total) * math.log((N + 1) / (self.df.get(f, 0) + 1) + 1)
            vec[f] = tfidf
        return vec

    def _cosine(self, v1, v2):
        if not v1 or not v2:
            return 0.0
        inter = sum(min(v1.get(g, 0), v2.get(g, 0)) for g in v1 if g in v2)
        n1 = math.sqrt(sum(x*x for x in v1.values()))
        n2 = math.sqrt(sum(x*x for x in v2.values()))
        return inter / (n1 * n2) if n1 and n2 else 0.0

    # ---------- 时效衰减 ----------
    def _fresh_score(self, mem):
        dt = time.time() - mem["last_access"]
        th = mem["half_life_days"] * 86400
        return 1.0 / (1.0 + (dt / th) ** K_DECAY)

    # ---------- 检索 ----------
    def search(self, query, top_k=5, refresh=True):
        """三层融合检索: TagScore + VecScore + FreshScore."""
        q_vec = self._vectorize(query)
        q_tags = self._parse_query_tags(query)
        scored = []
        for mem_id, mem in self.memories.items():
            if mem["archived"]:
                continue
            # 1) 标签相关度: 命中标签权重 × 记忆内标签占比
            tag_hit = 0.0
            for t in mem["tags"]:
                if q_tags and t in q_tags:
                    tag_hit += self.tag_weight.get(t, 1.0)
                elif q_tags:
                    # 标签名子串模糊命中
                    for qt in q_tags:
                        if qt in t or t in qt:
                            tag_hit += 0.5 * self.tag_weight.get(t, 1.0)
            tag_score = tag_hit / max(len(mem["tags"]), 1) if mem["tags"] else 0.0
            # 2) 语义相似
            vec_score = self._cosine(q_vec, self._vectorize(mem["content"]))
            # 3) 时效
            fresh_score = self._fresh_score(mem)
            # 融合(importance 放大)
            score = (ALPHA*tag_score + BETA*vec_score + GAMMA*fresh_score) * mem["importance"]
            scored.append((score, mem_id))

        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]

        # 热度刷新: 检索命中重置时效(该忘的淡, 该留的稳)
        if refresh:
            now = time.time()
            for _, mem_id in top:
                self.memories[mem_id]["last_access"] = now
                self.memories[mem_id]["access_count"] += 1
            self.save()
        return [(mid, self.memories[mid], round(s, 4)) for s, mid in top]

    def _parse_query_tags(self, query):
        """从查询中提取疑似标签(匹配已知标签, 前缀型)."""
        hits = set()
        for t in self.tag_weight:
            # 精确或类型前缀命中(如 query 含 "项目A" 命中 "topic:项目A")
            tag_val = t.split(":", 1)[-1] if ":" in t else t
            if tag_val and len(tag_val) >= 2 and tag_val in query:
                hits.add(t)
        return hits

    # ---------- 生命周期管理 ----------
    def archive_expired(self, epsilon=EPSILON_ARCHIVE):
        """衰减到阈值且属性含'临时'的进入归档冷存. 返回归档数."""
        archived = 0
        now = time.time()
        for mem_id, mem in self.memories.items():
            if mem["archived"]:
                continue
            if self._fresh_score(mem) < epsilon:
                tags_joined = " ".join(mem["tags"])
                if "临时" in tags_joined or "attr:临时" in tags_joined:
                    mem["archived"] = True
                    archived += 1
                # 非临时记忆: 老化降权保留, 不误删
        if archived:
            self.save()
        return archived

    def stats(self):
        return {
            "total": len(self.memories),
            "active": sum(1 for m in self.memories.values() if not m["archived"]),
            "archived": sum(1 for m in self.memories.values() if m["archived"]),
            "tags": len(self.tag_weight),
            "features": len(self.df),
            "half_life_map": DEFAULT_HALF_LIFE,
        }

    # ---------- 从本地真值库批量接入 ----------
    def ingest_truth_library(self, dir_path, pattern="truths_batch_*.json", limit=None):
        """读取 06_云端中枢同步/cloud_truths_pull 的真值库文件, 批量建索引.
        返回 接入条数. 每条取 truth_key/content 提炼为记忆."""
        import glob
        n = 0
        files = sorted(glob.glob(os.path.join(dir_path, pattern)))
        for fp in files:
            try:
                data = json.load(open(fp, encoding="utf-8"))
            except Exception:
                continue
            records = data
            if isinstance(data, dict):
                records = data.get("results") or data.get("data") or (data.get("truths") or [])
            if not isinstance(records, list):
                records = []
            for rec in (records if isinstance(records, list) else []):
                if limit and n >= limit:
                    break
                content = (rec.get("value") if isinstance(rec.get("value"), str) else
                           json.dumps(rec.get("value", ""), ensure_ascii=False)) or rec.get("content") or ""
                key = rec.get("key") or rec.get("truth_id") or f"mem-{n}"
                if not content:
                    continue
                tags = {"type": "事实", "topic": rec.get("truth_type") or "云端真值", "attr": "重要"}
                self.add_memory(f"zr-{key[:20]}-{n}", content[:500], tags, half_life_days=180)
                n += 1
            if limit and n >= limit:
                break
        return n


# ===================== 自测 =====================
if __name__ == "__main__":
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "memory_index_demo.json")
    eng = MemoryIndexEngine(tmp)

    # 写入三类记忆(不同半衰期)
    eng.add_memory("m1", "用户偏好用简体中文交流", {"type": "偏好", "topic": "交流", "attr": ["重要"]}, half_life_days=365)
    eng.add_memory("m2", "昨天完成了定时上报脚本", {"type": "任务", "topic": "项目A", "attr": "临时"}, half_life_days=30)
    eng.add_memory("m3", "五层约束栈V1.3仿真指标", {"type": "事实", "topic": "元极恒一"}, half_life_days=180)

    print("=== 写入后统计 ===")
    print(json.dumps(eng.stats(), ensure_ascii=False, indent=2))
    print("\n=== 检索: '用户喜欢什么语言' ===")
    for mid, mem, score in eng.search("用户喜欢什么语言", top_k=3):
        print(f"  {mid} score={score} tags={mem['tags']} 访问{mem['access_count']}次")
    print("\n=== 检索: '定时上报' ===")
    for mid, mem, score in eng.search("定时上报", top_k=3):
        print(f"  {mid} score={score} tags={mem['tags']}")

    # 生命周期: 把临时记忆时间拨老
    old = time.time() - 60 * 86400  # 60天前
    eng.memories["m2"]["last_access"] = old
    n = eng.archive_expired()
    print(f"\n=== 归档(60天前临时记忆) ===\n  归档数={n}")
    print(json.dumps(eng.stats(), ensure_ascii=False))
    os.remove(tmp)
