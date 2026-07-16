

go protoc 使用工具

protoc：Protocol Buffers 编译器
下载地址：https://github.com/protocolbuffers/protobuf/releases
或者通过包管理器安装（如 apt install protobuf-compiler）

protoc-gen-go：Go 代码生成插件
安装命令：

bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
确保 $GOPATH/bin 在你的 PATH 环境变量中。