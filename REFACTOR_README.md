# RePKG GUI 模块化重构说明

## 项目结构

重构后的项目结构如下：

```
REPKG-GUI-PUBLIC/
├── main.py                 # 主程序入口
├── old.py                  # 原始单体文件（保留作为参考）
├── test_refactor.py        # 测试脚本
├── config.json             # 配置文件
├── requirements.txt        # 依赖文件
├── assets/                 # 资源文件夹
│   ├── app.ico
│   ├── ico.py
│   └── icon.png
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── config_manager.py   # 配置管理
│   ├── file_operations.py  # 文件操作
│   ├── version_checker.py  # 版本检查
│   └── workers.py          # 工作线程
└── ui/                     # 用户界面模块
    ├── __init__.py
    ├── main_window.py      # 主窗口类
    └── tabs.py             # 标签页创建
```

## 模块说明

### 1. utils/ - 工具模块

#### `workers.py` - 工作线程模块
- `ExtractWorker`: 文件提取工作线程
- `ImageLoadWorker`: 图片异步加载工作线程

#### `config_manager.py` - 配置管理模块
- `ConfigManager`: 配置管理器类
  - 配置文件读取和保存
  - Steam安装路径检测

#### `file_operations.py` - 文件操作模块
- `FileOperations`: 文件操作工具类
  - RePKG.exe查找
  - 文件提取命令生成
  - 提取后文件整理
  - 目标文件查找

#### `version_checker.py` - 版本检查模块
- `VersionChecker`: 版本检查器类
  - RePKG版本检查
  - GitHub版本获取
  - 版本比较
  - GitHub页面打开

### 2. ui/ - 用户界面模块

#### `main_window.py` - 主窗口模块
- `RePKGGUI`: 主窗口类
  - 界面初始化
  - 事件处理
  - 分页控制
  - 提取功能

#### `tabs.py` - 标签页模块
- `TabCreator`: 标签页创建器
  - PKG标签页
  - 手动提取标签页
  - 设置标签页
  - 关于标签页

### 3. main.py - 主程序入口
- 程序启动点
- QApplication初始化

## 运行方式

### 运行主程序
```bash
python main.py
```

### 运行测试
```bash
python test_refactor.py
```

## 重构优势

1. **模块化设计**: 每个功能模块独立，便于维护和扩展
2. **代码复用**: 工具类可以在不同地方重复使用
3. **职责分离**: 每个模块有明确的职责范围
4. **易于测试**: 可以单独测试每个模块的功能
5. **可维护性**: 修改某个功能时不会影响其他模块

## 功能保持

重构过程中保持了原有的所有功能：
- ✅ 缩略图预览和分页
- ✅ 文件提取和整理
- ✅ 手动提取和批量提取
- ✅ 配置管理
- ✅ 版本检查
- ✅ 自定义设置
- ✅ 拖拽功能
- ✅ 异步操作

## 注意事项

1. 确保`RePKG.exe`位于项目根目录下
2. 需要安装PyQt6依赖：`pip install PyQt6`
3. 配置文件会自动创建在项目目录下
4. 如需要requests功能（版本检查），请安装：`pip install requests`
