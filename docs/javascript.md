# electron 中模块加载
electron 28.0.0 开始支持 ESM，这个的具体含义是指该版本使用的node.js才是支持ESM的版本？

electron中，main process由 node.js 运行，node.js 支持 CommonJS ，也支持 ESM，
只是需要通过 package.json 或是通过文件扩展名设置，详细信息在以下链接有说明：
https://nodejs.org/api/packages.html#determining-module-system

electron中，render processes由chromium负责运行，浏览器中默认就是使用ESM。

需要理清楚的问题：
1. 在main process中可以require任意通过npm安装的包，因为main process运行在nodejs中
2. 在render process中，正常是无法import通过npm安装的包，这些包安装在node_modules目录下，
   运行中浏览器的页面无法访问这些文件，并且搜索规则也不同，在网页中只能import通过url可以指定
   的js文件。如果需要import通过npm安装的包，则可以通过webpack这样的工具进行打包，本质是将
   入口js依赖的内容都打包在一起，所以浏览器引用单个文件就可以运行。
3. 在render process中如果启用nodeIntegration，则在render process中也可以使用require语句，
   require本质上是一个函数，render process可以require任意nodejs包和electron包，此时如果通过
   webpack打包render process的js脚本，需要正确设置target类型，即renderProcess。

如果设置webpack的target为web，则在render process如果import fs，则在打包阶段就会报错，因为无法
找到fs模块。如果将target改为render process，但是electron的main process不打开node integration
使能，则在运行阶段会报错，因为webpack在打包时将import fs翻译成了require，此时require函数不存在。

总结：
1. main process干脆仍然使用 CommonJS ，这样避免很多麻烦，比如webpack的配置文件默认都是CommonJS
2. render process使用ESM，如果需要使用无特权的本地npm包，则可以通过webpack打包
3. 如果开启NodeIntegration，则使用CommonJS来引用 nodejs和electron的包，此时通过import也可以引用nodejs的包
   只是webpack可能会打包


如果不打开nodeIntegration，那么render process只能访问通过preload脚本暴露给其的本地接口，其中最重要的作用是
建立render process与main process通信的IPC接口。
preload脚本运行既可以访问HTML DOM，也可以访问NodeJS和Electron API一个子集的环境中，一般是CommonJS的，web
pack也可以对其进行打包。