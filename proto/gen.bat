@echo off
protoc -I="proto" --go_out="server" "proto/packets.proto"
protoc -I="proto" --python_out="client/core/proto" "proto/packets.proto"
echo Done