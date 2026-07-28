package ziface

/*
	路由抽象接口
	路由里的数据都是IRequest
*/

type IRouter interface {
	// 在处理Conn业务之前的钩子方法和Hook
	PreHandle(request IRequest)
	// 在处理Conn业务的主方法hook
	Handle(request IRequest)
	// 在处理Coon业务之后的钩子方法和Hook
	PostHandle(reqeust IRequest)
}
