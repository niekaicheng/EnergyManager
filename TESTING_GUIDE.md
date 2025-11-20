# Energy Manager Web Interface 测试指南

## 服务器状态
✅ Flask服务器正在运行: **http://localhost:5000**

## 数据库状态
✅ Goals: 9条
✅ Events: 79条  
✅ Health Metrics: 1318条

---

## 修复内容

### 1. JavaScript文件修复
- ✅ 删除了损坏的代码块
- ✅ 修复了`createEvent`函数
- ✅ 添加了完整的`archiveGoalById`函数
- ✅ 实现了完整的数据导入功能（`showImportDataModal`, `previewFile`, `importData`）
- ✅ 改进了错误处理和用户反馈

### 2. 数据导入功能增强
- ✅ 添加了详细的错误信息展示
- ✅ 进度条重置在失败时
- ✅ 支持CSV文件上传到后端

---

## 测试步骤

### 测试1: 数据展示功能

1. **打开浏览器**: 访问 http://localhost:5000

2. **测试Dashboard页面**:
   - 检查是否显示能量平衡统计
   - 检查是否显示图表（能量状态分布、每日能量平衡）
   - 检查Recent Activity列表

3. **测试Goals页面**:
   - 点击左侧导航 "Goals"
   - 应该看到9个目标
   - 每个目标卡片应显示：名称、优先级、能量成本、事件数量、总时间

4. **测试Journal页面**:
   - 点击 "Journal"  
   - 应该看到最近3天的事件记录
   - 每天应显示总时间和能量净值
   - 每个事件应显示：时间、活动、时长、能量状态、关联目标、能量成本

5. **测试Trends页面**:
   - 点击 "Trends"
   - 应该看到一个表格，包含每天的汇总数据
   - 列包括：日期、睡眠分数、心率、压力、步数、事件数、总时间、能量净值

6. **测试Health页面**:
   - 点击 "Health"
   - 应该看到4个指标卡片：Sleep Quality, Heart Rate, Stress Level, Steps
   - 应该看到健康指标趋势图表

---

### 测试2: 数据导入功能

#### 准备测试CSV文件

您需要一个有效的CSV文件。文件名应包含以下之一：
- `aggregated_fitness_data` - 每日汇总数据
- `sport_record` - 运动记录

#### 导入步骤：

1. **打开Import Modal**:
   - 在Health页面，点击右上角的 "Import Data" 按钮
   - 应该弹出一个模态框

2. **选择文件**:
   - 点击 "Choose File" 按钮
   - 选择一个CSV文件
   - 应该看到文件预览（文件名和大小）

3. **上传文件**:
   - 点击 "Import Data" 按钮
   - 应该看到进度条：
     - 30%: "Uploading file..."
     - 70%: "Processing data..."  
     - 100%: "Success! Imported X records"

4. **验证导入**:
   - 2秒后modal自动关闭
   - 会显示成功通知
   - Health页面应该刷新并显示新数据

#### 预期错误情况：

- **没有选择文件**: 应显示 "Please select a file"
- **文件格式错误**: 应显示 "File must be CSV format"  
- **不支持的CSV类型**: 应显示 "Unsupported file. Please upload aggregated_fitness_data or sport_record CSV files."
- **CSV格式错误**: 应显示具体错误信息

---

## 常见问题排查

### 问题1: 数据无法显示

**检查项**:
1. 打开浏览器开发者工具 (F12)
2. 查看Console标签页是否有JavaScript错误
3. 查看Network标签页，检查API请求是否成功（状态码200）

**可能原因**:
- API请求失败
- 数据格式不匹配
- JavaScript错误

**解决方法**:
- 刷新页面 (Ctrl+R 或 F5)
- 检查服务器日志
- 清除浏览器缓存

### 问题2: 数据导入失败

**检查项**:
1. 查看浏览器Console是否有错误
2. 查看服务器终端输出是否有Python错误
3. 确认CSV文件格式正确

**常见错误**:
- 文件路径问题
- CSV编码问题（应为UTF-8）
- CSV格式不匹配

**解决方法**:
- 确保文件名包含 `aggregated_fitness_data` 或 `sport_record`
- 检查CSV文件是否包含正确的列
- 查看服务器日志获取详细错误信息

### 问题3: 图表不显示

**可能原因**:
- Chart.js未加载
- 数据不足
- JavaScript错误

**解决方法**:
- 检查网络连接（Chart.js从CDN加载）
- 确保有足够的数据（至少1天的数据）
- 查看Console错误

---

## API测试（可选）

您也可以直接测试API端点：

### 测试Goals API:
```bash
curl http://localhost:5000/api/goals
```

### 测试Events API:
```bash
curl http://localhost:5000/api/events/today
```

### 测试Health API:
```bash
curl http://localhost:5000/api/health/today
```

### 测试Trends API:
```bash
curl http://localhost:5000/api/trends?days=7
```

---

## 下一步

如果所有测试都通过：
✅ Web界面可以正常使用了！

如果遇到问题：
1. 记录具体的错误信息
2. 在浏览器Console查看JavaScript错误
3. 在服务器终端查看Python错误
4. 提供错误截图或日志

---

## 技术支持

如发现以下问题，请提供详细信息：
- 具体哪个页面/功能有问题
- 浏览器Console的错误信息（F12打开）
- 服务器终端的错误输出
- 操作步骤和预期结果vs实际结果
