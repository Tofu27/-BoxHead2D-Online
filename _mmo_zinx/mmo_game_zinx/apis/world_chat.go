package apis

import (
	"fmt"
	"game/core"
	"game/pb"
	"zinx/ziface"
	"zinx/znet"

	"google.golang.org/protobuf/proto"
)

// 世界聊天 路由业务
type WorldChatApi struct {
	znet.BaseRouter
}

func (wc *WorldChatApi) Handle(request ziface.IRequest) {
	// 解析客户端传递进来的proto协议
	proto_msg := &pb.Talk{}
	if err := proto.Unmarshal(request.GetMsgData(), proto_msg); err != nil {
		fmt.Println("Talk Unmarshal error: ", err)
		return
	}

	// 当前的聊天数据是属于哪个玩家发送的
	pid, _ := request.GetConnection().GetProperty("pid")

	// 根据Pid得到对应的player对象
	player := core.WorldMgrObj.GetPlayerByPid(pid.(int32))

	// 将这个消息广播给其他全部在线的玩家
	player.Talk(proto_msg.Content)

}
