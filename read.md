
安装 Protobuf 编译器 (protoc)
    Windows：下载 protoc-xxx-win64.zip 从 Releases，解压并将 bin 目录加入系统 PATH。

安装 Go 的 Protobuf 插件
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest

安装 Python 的 Protobuf 库和工具
    pip install protobuf grpcio-tools

随后可以使用 proto 下的 bat 生成对应 proto 文件




安装 sqlc
    Go 用户 (通用):  go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest
    安装完成后，在终端运行 sqlc version 来验证是否成功。

    推荐方案：直接下载预编译的 sqlc 二进制文件（无需编译）
    这是最快最省事的方法，因为 sqlc 官方提供了 Windows 可执行文件。
    访问 sqlc 的 GitHub Releases 页面：
    https://github.com/sqlc-dev/sqlc/releases
    找到最新版本（如 v1.28.0），在 Assets 中下载 sqlc_1.28.0_windows_amd64.zip（或类似名称）。
    解压得到 sqlc.exe，将它放到一个已经存在于 PATH 的目录，比如 C:\Windows\System32 或你的 Go 的 bin 目录（C:\Users\Administrator\go\bin），也可以新建一个文件夹并将路径加入 PATH。
    

    在包含 sqlc.yml 的目录下，打开终端执行以下命令：
    sqlc generate

    如果一切顺利，不会有任何输出。然后你会看到 sqlc 根据你的配置在 ../ (即上级目录) 下生成了 db 包，里面包含三个文件：

    db.go: 数据库连接和查询核心代码。
    models.go: 根据你的 schema.sql 生成的 Go 结构体（如 Author）。
    query.sql.go: 根据你的 queries.sql 生成的类型安全的 Go 方法。


在 Go 项目中使用生成的代码
    安装 SQLite 驱动：你需要先引入 Go 的 SQLite 驱动。
    go get github.com/mattn/go-sqlite3