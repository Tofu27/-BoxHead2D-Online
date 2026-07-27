package main

import (
	"fmt"
	"io"
	"net"
	"time"
	"zinx/znet"
)

func main() {
	fmt.Println("客户端启动...")

	conn, err := net.Dial("tcp", "127.0.0.1:8999")
	if err != nil {
		fmt.Println("客户端启动失败")
		return
	}

	for {
		// 发送封包的Message消息
		dp := znet.NewDataPack()
		binaryMsg, err := dp.Pack(znet.NewMsgPackage(1, []byte("Zinxv0.5 client Test Message")))
		if err != nil {
			fmt.Println("消息包装错误: ", err)
			return
		}

		if _, err := conn.Write(binaryMsg); err != nil {
			fmt.Println("数据写入失败: ", err)
			return
		}

		binaryHead := make([]byte, dp.GetHeadLen())
		if _, err := io.ReadFull(conn, binaryHead); err != nil {
			fmt.Println("read head error: ", err)
			break
		}

		msgHead, err := dp.Unpack(binaryHead)
		if err != nil {
			fmt.Println("客户端解包失败: ", err)
			break
		}

		if msgHead.GetMsgLen() > 0 {
			msg := msgHead.(*znet.Message)

			msg.Data = make([]byte, msg.GetMsgLen())
			if _, err := io.ReadFull(conn, msg.Data); err != nil {
				fmt.Println("read data error: ", err)
				break
			}

			fmt.Println("接收到服务信息: ID = ", msg.Id, " Len = ", msg.DataLen, " data = ", string(msg.Data))
		}

		time.Sleep(time.Second * 1)
	}

}
