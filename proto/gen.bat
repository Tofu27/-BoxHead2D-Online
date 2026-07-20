@echo off
protoc -I="." --go_out="../server" "*.proto"
protoc -I="." --python_out="../client/core/proto" "*.proto"
echo Done