# 火斗云智AIOS 公网可见度提升方案

**日期**: 2026-09-21 | **确权**: Ω₀⊂⊙∞⊂Ω | **DID**: BR-000002

## 一、现状（已实测）

| 项目 | 状态 |
|------|------|
| 站点页面 | 49个公开页全部HTTP 200 |
| robots.txt | ✅ 已有（Allow /，Disallow /api/、/admin、/*.json$） |
| sitemap.xml | ⚠️ 仅10个URL（覆盖严重不足） |
| 搜索引擎收录 | ❌ 未收录 |
| SSL/安全头 | ✅ 完整 |

## 二、待办1：部署完整sitemap（55个URL）

生成文件：`sitemap.xml`（同目录，55 URL，已含全部公开页面+权重+更新频率）

**部署方法**（需要服务器管理权限，选其一）：
1. **宝塔面板**：网站 → huodouai.com → 文件 → 网站根目录 → 上传覆盖 `sitemap.xml`
2. **腾讯云控制台**：轻量/云服务器 → 登录 → nginx root目录 → 覆盖
3. **SSH**（若已授权）：
```bash
scp sitemap.xml root@123.207.202.158:/var/www/huodouai/sitemap.xml
# 或实际nginx root路径
nginx -s reload
```

## 三、待办2：搜索引擎提交（需账号，均免费）

### 百度（国内流量主力）
1. 注册/登录百度搜索资源平台：https://ziyuan.baidu.com/
2. 添加站点：`https://www.huodouai.com/`
3. 验证方式：推荐"CNAME验证"（DNS加一条解析）
4. 提交sitemap：`https://www.huodouai.com/sitemap.xml`

### 必应（必应中国=国内第二，且顺带覆盖Google索引）
1. 登录必应站长：https://www.bing.com/webmasters
2. 添加站点 → 验证（CNAME或文件）
3. 提交sitemap

### Google（海外）
1. Google Search Console：https://search.google.com/search-console
2. 添加资源 → 验证 → 提交sitemap

## 四、待办3：ICP备案（国内服务器必需，托管商=腾讯云）

- 登录腾讯云备案控制台：https://console.cloud.tencent.com/beian
- 用已购买的域名证书信息提交（huodouai.com）
- 备案通过前，80/443 端口可能受限（当前443已通，说明可能已备案或未严格拦截）
- **重点确认**：如未备案，443端口可能被随时关闭，务必核实

## 五、待办4：外链建设（提升权重）

- 在Gitee/GitHub技术仓库README加官网链接
- 在知乎/掘金/CSDN发布技术文章，文末链接官网
- 往我们的原创技术区文章统一挂官网链接

## 六、效果预期

| 动作 | 预期效果 |
|------|---------|
| 提交sitemap | 2-4周内开始收录 |
| 备案完成 | 域名长期稳定，权重累积 |
| 外链+文章 | 3-6个月品牌词可被搜索 |

Ω₀⊂⊙∞⊂Ω | SEO-SUBMIT-PLAN-20260921
