package znet

import (
	"fmt"
	"strconv"
	"zinx/ziface"
)

/*
消息处理模块的实现
*/
type MsgHandler struct {
	// 存放每一个MsgId对应的处理方法
	Apis map[uint32]ziface.IRouter
}

// 创建MsgHandler
func NewMsgHandler() *MsgHandler {
	mh := &MsgHandler{
		Apis: make(map[uint32]ziface.IRouter),
	}

	return mh
}

// 调度/执行 对应的Router消息处理方法
func (mh *MsgHandler) DoMsgHandler(request ziface.IRequest) {
	// 从Request中找到msgId
	handler, ok := mh.Apis[request.GetMsgID()]
	if !ok {
		fmt.Println("api msgId = ", request.GetMsgID(), " 没找到, 需要注册")
		return
	}

	// 根据msgId调度对应router业务
	handler.PreHandle(request)
	handler.Handle(request)
	handler.PostHandle(request)
}

// 为消息添加具体的处理逻辑
func (mh *MsgHandler) AddRouter(msgId uint32, router ziface.IRouter) {
	// 判断当前msg绑定的API处理方法是否已经存在
	if _, ok := mh.Apis[msgId]; ok {
		// Id已经注册
		panic("重复注册的api, msgID = " + strconv.Itoa(int(msgId)))
	}
	// 添加msg与API的绑定关系
	mh.Apis[msgId] = router

	fmt.Println("添加api MsgID = ", msgId, " 成功")
}
