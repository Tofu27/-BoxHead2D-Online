@echo off
protoc -I="." --go_out="../server" "packets.proto"
protoc -I="." --python_out="../client/core/proto" "packets.proto"
echo Done