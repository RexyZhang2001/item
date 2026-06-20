# 3311 项目会话记录 — CCTV 仿真与 RTMP 截图

本文档整理了本次会话中的需求、结论与可用的命令备忘。开发目录已迁至 `E:\3311 AI`（全英文路径）。

---

## 1. 目标：用 MP4 在云端仿真 CCTV，多端拉流

- **思路**：在云（或内网 Linux）上用 **SRS** 接收 RTMP，用 **ffmpeg** 将本地 MP4 **循环**推流到 SRS。
- **协议**：可同时对外提供 RTMP / HLS / HTTP-FLV（由 SRS 根据配置生成）。

---

## 2. 已部署的服务器概要（会话内操作时）

| 项目 | 说明 |
|------|------|
| 示例 IP | `10.148.1.22`（**私网**，仅同局域网/VPN 可访问） |
| 系统 | TencentOS Server 4 |
| SRS | Docker 镜像 `registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5`，端口 `1935`、`8080`、`1985` |
| 视频 | 上传为 `/opt/videos/cctv.mp4`，由 systemd 服务 **`cctv-push`** 用 ffmpeg **copy**（无二次编码）推送 |
| 注意 | 该环境 ffmpeg **无 libx264**，故推流脚本使用 `-c:v copy -an`，与源 MP4（H.264、无音频）匹配 |

---

## 3. 拉流地址（与服务器同网时）

| 协议 | URL |
|------|-----|
| RTMP | `rtmp://10.148.1.22/live/test` |
| HLS | `http://10.148.1.22:8080/live/test.m3u8` |
| HTTP-FLV | `http://10.148.1.22:8080/live/test.flv` |
| SRS API | `http://10.148.1.22:1985/api/v1/streams/` |

**维护（SSH 登录服务器后）**：

```bash
systemctl status cctv-push
systemctl restart cctv-push
docker ps --filter name=srs
```

---

## 4. 公网网页工具测 `10.148.1.x` 为什么失败？

- `10.148.1.22` 是 **私有地址**，互联网上的站点（如 EZ 在线工具）无法路由到你内网主机。
- 现象：提示无法连接流媒体、码率 0。**不是** SRS 没在推流，而是**测试发起的网络不在同一内网**。
- **正确做法**：同网 VLC/ffplay/`rtmp_snapshot.py`；或对服务器做 **公网 IP / VPN / frp / 端口映射**后再用网页工具。

---

## 5. Python 脚本：从 RTMP 自动截图（本文件夹内）

文件：`rtmp_snapshot.py`、`requirements-rtmp-snapshot.txt`

**依赖**：

```bash
pip install -r requirements-rtmp-snapshot.txt
```

**示例**：

```bash
cd "E:\3311 AI"

# 默认连内网 CCTV 仿真流（可在脚本顶部改 DEFAULT_RTMP）
python rtmp_snapshot.py

# 单次截图
python rtmp_snapshot.py --once

# 连续多张，每张间隔 5 秒
python rtmp_snapshot.py -n 10 -i 5

# 连续 3 张，每张间隔约 1 秒（会话中用于避免时间戳只差 1s 却总像同一画面的问题）
python rtmp_snapshot.py -n 3 -i 1

# 指定 URL 与输出目录
python rtmp_snapshot.py "rtmp://10.148.1.22/live/test" -o "E:\3311 AI\shots"

# 其他 RTMP（若网络可达）
python rtmp_snapshot.py "rtmp://example.com/live/stream" --once
```

**实现要点**：

- JPEG 写入使用 `cv2.imencode` + `Path.write_bytes`，避免 **Windows + 中文路径** 下 `cv2.imwrite` 失败。
- 为避免连续截图拿到 **缓冲重复帧**：连接后短时 `grab()` 冲刷；间隔等待期间也用 `grab()` 消费缓冲区，而非单纯 `sleep()`。

默认错误提示仍会写「同一内网」——若在公网自建 RTMP，只要网络通即可类推使用。

---

## 6. 湖南卫视测试 RTMP（会话实测）

命令：

```text
python rtmp_snapshot.py "rtmp://58.200.131.2:1935/livetv/hunantv" --once
```

当前环境下 **握手失败**（如 `Cannot read RTMP handshake response` / Winsock `-10054`）。可能原因：源已下架、防火墙/运营商限制、需客户端鉴权、地域限制等。此类网上流传的卫视地址**不可靠**，会话中建议仍以 **自建仿真流** 或 **可自行验证的 VLC 可播放地址** 做功能测试。

---

## 7. 安全

- 会话中我曾按你提供的 root 口令协助部署；你提出 **不再需要保留该口令**。后续请使用 **密钥登录**、**轮换密码**，且勿在聊天记录中再次出现口令。

---

## 8. 文件清单（本文件夹）

| 文件 | 说明 |
|------|------|
| `SESSION_NOTES.md` | 本会话纪要（中文版） |
| `rtmp_snapshot.py` | RTMP 截图脚本 |
| `requirements-rtmp-snapshot.txt` | Python 依赖 |

可根据需要在此处继续放截图输出或配置文件。
