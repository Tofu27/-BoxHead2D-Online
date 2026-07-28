package znet

import (
	"fmt"
	"zinx/zconf"
	"zinx/ziface"
)

/*
消息处理模块的实现
*/
type MsgHandler struct {
	// 存放每一个MsgId对应的处理方法
	Apis map[uint32]ziface.IRouter
	// 负责Worker取任务的消息队列
	TaskQueue []chan ziface.IRequest
	// 业务工作Worker池的worker数量
	WorkerPoolSize uint32
}

// 创建MsgHandler
func NewMsgHandler() *MsgHandler {
	mh := &MsgHandler{
		Apis:           make(map[uint32]ziface.IRouter),
		WorkerPoolSize: zconf.GlobalObject.WorkerPoolSize, // 从全局配置中获取
	}

	mh.TaskQueue = make([]chan ziface.IRequest, zconf.GlobalObject.WorkerPoolSize)

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
		msgErr := fmt.Sprintf("重复注册的API , msgID = %+v\n", msgId)
		panic(msgErr)
	}
	// 添加msg与API的绑定关系
	mh.Apis[msgId] = router

	fmt.Println("添加api MsgID = ", msgId, " 成功")
}

// 启动一个Worker工作池 (开启工作池的动作只能发生一次，一个框架只能有一个工作池)
func (mh *MsgHandler) StartWorkerPool() {
	// 根据 WorkerPoolSize 分别开启Worker，每一个worker用一个go承载
	for i := 0; i < int(mh.WorkerPoolSize); i++ {
		// 一个worker被启动
		// 当前的worker对应的channel消息队列 开辟空间 第0个worker就用第0个channel
		mh.TaskQueue[i] = make(chan ziface.IRequest, zconf.GlobalObject.MaxWorkerTaskLen)
		// 启动当前的Worker, 阻塞等待消息从channel传递进来
		go mh.StartOneWorker(i, mh.TaskQueue[i])
	}
}

// 启动一个Worker工作流程
func (mh *MsgHandler) StartOneWorker(workerID int, taskQueue chan ziface.IRequest) {
	fmt.Println("Worker ID = ", workerID, " 已经启动...")

	//阻塞等待消息对应消息队列的消息
	for {
		select {
		case request, ok := <-taskQueue:
			if !ok {
				fmt.Println("taskQueue 已经关闭, WOrkerID = ", workerID)
				return
			}

			// 如果有消息过来，出列的就是一个客户端的Request，执行当前Request所绑定的业务
			mh.DoMsgHandler(request)
		}
	}

}

// 将消息交给TaskQueue，由Worker进行处理
func (mh *MsgHandler) SendMsgToTaskQueue(request ziface.IRequest) {
	// 将消息平均分配给不同的worker
	// 根据客户端建立的ConnID来进行分配
	workerID := request.GetConnection().GetConnID() % mh.WorkerPoolSize
	fmt.Println("添加 ConnID = ", request.GetConnection().GetConnID(),
		" reqeust MsgID = ", request.GetMsgID(), " 到 WorkerID = ", workerID)

	// 将消息发送给对应的worker的TaskQueue
	mh.TaskQueue[workerID] <- request
}

// 占用workerID
func useWorker(conn ziface.IConnection) uint32 {
	var workerId uint32

	mh, _ := conn.GetMsgHandler().(*MsgHandler)
	if mh == nil {
		fmt.Println("useWorker 报错：获取消息处理器失败, 消息处理为空")
		return 0
	}

	workerId = uint32(conn.GetConnID() % mh.WorkerPoolSize)

	return workerId
}
