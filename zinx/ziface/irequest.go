package ziface

/*
IRequest 接口：
实际上是把客户端请求的连接信息 和 请求的数据 包装到了一个Reqeuest中
*/

type IRequest interface {
	// 得到当前连接
	GetConnection() IConnection

	// 得到请求的消息数据
	GetMsgData() []byte

	GetMsgID() uint32
}
