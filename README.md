# Gitea Runner 懒猫应用适配器

本仓库为 `cloud.lazycat.app.gitearunner` 跟踪上游
[Gitea Runner](https://gitea.com/gitea/runner) 稳定标签，并生成懒猫官方应用更新。

## 继承 `/opt/test/runner.lpk` 的定制

每次选中新的 Runner 标签后，工作流都会构建一个新的 amd64 定制镜像。镜像以相同
版本的官方 `gitea/runner:<version>-dind` 为基础，并内置懒猫网络初始化脚本。该脚本
保留旧 LPK 已验证的行为：

- 安装 Docker CLI 和 Buildx（基础镜像缺少时才安装）；
- 创建并复用 `gitea-build` Docker 网络；
- 使用 `/lzcsys/run/lzc-docker/docker.sock` 访问懒猫 Docker；
- 将 Buildx 配置持久化到 `/lzcsys/data/appvar/cloud.lazycat.app.gitearunner/data/docker-buildx`；
- 固定 `DOCKER_CONFIG`、`BUILDX_BUILDER`、`container.network` 和 `docker_host`；
- 配置只在 `/data/.gitearunner-lpk-config-v6` 不存在时写入，避免重启覆盖用户设置。

Runner 数据和注册配置继续绑定 `/lzcapp/var/data:/data`。升级会保留已经注册的 Runner
身份、配置、Docker Buildx 缓存和自定义环境变量。安装参数仍为 Runner 名称、Gitea 实例
URL、注册令牌和附加环境变量。

## 自动更新与送审

上游稳定 `vX.Y.Z` 标签由 Git 版本选择器发现，更新日志从本次标签与上一标签之间的
Gitea Git 提交范围提取。推送和默认手动运行只做检查，取消 `dry-run` 后才会构建定制镜像、
转存到懒猫官方仓库、生成 LPK 和提交审核。组织级 `LZC_API_TOKEN` 需要授权给本仓库，
工作流使用 `secrets: inherit`。正式流程成功后会创建带版本号的 GitHub Release，只上传
`.lpk` 文件。

## 本地检查

```bash
python3 -m unittest discover -s tests -v
mkdir -p dist
lzc-cli project build
lzc-cli lpk lint dist/cloud.lazycat.app.gitearunner-v1.0.3.lpk
```

## 来源

- 上游源码：https://gitea.com/gitea/runner
- 上游镜像：https://hub.docker.com/r/gitea/runner
- 原懒猫包：`/opt/test/runner.lpk`
