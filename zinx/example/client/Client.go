package main

import (
	"fmt"
	"net"
	"time"
)

func main() {
	fmt.Println("客户端启动...")

	conn, err := net.Dial("tcp", "127.0.0.1:8999")
	if err != nil {
		fmt.Println("客户端启动失败")
		return
	}

	for {
		_, err := conn.Write([]byte("你好zinx"))
		if err != nil {
			fmt.Println("写入失败:", err)
			return
		}

		buf := make([]byte, 512)
		cnt, err := conn.Read(buf)
		if err != nil {
			fmt.Println("读取buff失败:", err)
			return
		}

		fmt.Printf("服务回调: %s, cnt = %d\n", buf, cnt)

		time.Sleep(time.Second * 1)
	}

}
