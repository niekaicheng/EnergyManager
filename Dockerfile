# 1. 使用一个轻量级的 Python 3.12 官方镜像作为基础
FROM python:3.12-slim

# 2. 在容器内创建一个工作目录
WORKDIR /app

# 3. 复制依赖文件
# (我们先复制这个文件，以便 Docker 可以缓存已安装的包)
COPY requirements.txt .

# 4. 安装 Python 依赖
RUN pip install -r requirements.txt --break-system-packages

# 5. 复制你所有的项目代码到容器中
COPY . .

# 6. 设置默认的"入口点"，这样你就不必每次都输入 "python3 emanager.py"
ENTRYPOINT ["python3", "emanager.py"]

# 7. 设置一个默认命令 (例如，显示帮助信息)，如果用户没有提供任何命令
CMD ["--help"]


#docker-compose run --rm emanager import ./mifitdata/20251111_47675629_MiFitness_hlth_center_sport_record.csv
#docker-compose run --rm emanager import ./mifitdata/20251111_47675629_MiFitness_hlth_center_aggregated_fitness_data.csv


## 绘制过去30天（默认）的睡眠得分
#python3 emanager.py plot --metric sleep_score
#
## 绘制过去14天的步数
#python3 emanager.py plot --metric steps_total --days 14
#
## 绘制压力数据，并自定义输出文件名
#python3 emanager.py plot --metric stress_avg --output my_stress_chart.png