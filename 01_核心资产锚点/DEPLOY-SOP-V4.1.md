# 仪表盘官网部署SOP V4.1

## 目标
将neural_dashboard.html部署到huodouai.com/kernel/，实现公网可访问。

## 部署步骤

### 1. 上传文件到服务器
```bash
# 本地执行
scp -i ~/.ssh/zr_cloud_ops neural_dashboard.html root@123.207.202.158:/www/wwwroot/huodouai.com/kernel/dashboard.html
```

### 2. 配置nginx（如果需要）
```nginx
location /kernel/ {
    root /www/wwwroot/huodouai.com;
    try_files $uri $uri/ =404;
}
```

### 3. 验证访问
```
https://www.huodouai.com/kernel/dashboard.html
```

## 当前状态
- ✅ 仪表盘HTML已生成
- ✅ 已上传飞书云盘归档
- ⏳ 待部署到官网（需要SSH密钥权限）
