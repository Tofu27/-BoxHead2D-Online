package zconf

import (
	"encoding/json"
	"fmt"
	"os"
	"zinx/ziface"
)

/*
存储一切有关Zinx框架的全局参数，供其他模块使用
一些参数是可以通过zinx.json由用户进行配置
*/
type GlobalObj struct {
	/*
		Server
	*/
	TcpServer ziface.IServer // 当前zinx全局的Server对象
	Host      string         // 当前服务器主机监听的IP
	TcpPort   int            // 当前服务器主机监听的端口号
	Name      string         // 当前服务器的名称

	/*
		Zinx
	*/
	Version          string //当前Zinx的版本号
	MaxConn          int    //当前服务器主机允许的最大连接数
	MaxPackageSize   uint32 //当前zinx框架数据包的最大值
	WorkerPoolSize   uint32 //Worker工作池的队列个数
	MaxWorkerTaskLen uint32 //每个Worker对应的消息队列的任务的数量最大值
}

/*
定义一个全局的对外GlobalObj
*/
var GlobalObject *GlobalObj

/*
从 zinx.json 去加载用户自定义的参数
*/
func (g *GlobalObj) Reload() {
	data, err := os.ReadFile("conf/zinx.json")
	if err != nil {
		// 兼容性处理：文件不存在或无法读取时，不 panic，而是使用默认值并提示
		if os.IsNotExist(err) {
			fmt.Println("提示: conf/zinx.json 不存在，使用代码中的默认配置")
		} else {
			fmt.Printf("警告: 读取配置文件失败 (%v)，使用默认配置\n", err)
		}
		return
	}

	if len(data) == 0 {
		fmt.Println("提示: conf/zinx.json 为空文件，使用默认配置")
		return
	}

	// 将 json 文件数据解析到 struct 中
	err = json.Unmarshal(data, &GlobalObject)
	if err != nil {
		panic(fmt.Sprintf("错误: conf/zinx.json 格式解析失败: %v", err))
	}
}

/*
提供一个init方法，初始化当前的GlobalObject
*/
func init() {
	// 如果配置文件没有加载，使用默认的值
	GlobalObject = &GlobalObj{
		Name:             "ZinxServerApp",
		Version:          "v0.4",
		TcpPort:          8999,
		Host:             "0.0.0.0",
		MaxConn:          1000,
		MaxPackageSize:   4096,
		WorkerPoolSize:   10,
		MaxWorkerTaskLen: 1024,
	}

	// 尝试从conf/zinx.json 加载一些用户自定义的参数
	GlobalObject.Reload()
}
