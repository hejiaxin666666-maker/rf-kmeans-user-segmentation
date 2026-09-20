# 淘宝用户 RF + K-Means 用户分群运营观测站

这是一个基于淘宝用户行为数据的用户分群 Demo。项目使用最近购买间隔 R 和购买频次 F 构建 RF 特征，使用 K-Means 将用户划分为不同人群，并通过 Streamlit 提供可交互的分析仪表盘。

## 项目目标

- 识别近期活跃、高频复购和长期沉默用户。
- 通过肘部法则和轮廓系数辅助选择 K 值。
- 输出用户级分群结果、用户画像和差异化运营策略。
- 用一个可运行的网页仪表盘展示数据、模型和业务解释。

## 数据说明

数据集为阿里云天池淘宝用户行为数据集，常见字段如下：

| 字段 | 含义 |
| --- | --- |
| `user_id` | 用户 ID |
| `item_id` | 商品 ID |
| `category_id` | 品类 ID |
| `behavior_type` | 1 浏览、2 收藏、3 加购、4 购买 |
| `timestamp` | 秒级 Unix 时间戳 |

原始数据没有消费金额字段，因此本项目不计算完整 RFM。F 表示购买行为记录次数，不等同于真实订单数、消费金额或利润贡献。

## RF 指标

- **R（Recency）**：数据集中最后购买日期减去用户最后一次购买日期的天数。R 越小，用户越新、越活跃。
- **F（Frequency）**：用户在数据周期内的购买行为记录次数。F 越大，说明购买频次越高。

K-Means 只使用 R、F 两个标准化特征。浏览、收藏、加购次数、活跃天数和品类数量用于补充用户画像。

## 数据处理流程

1. 读取有表头或无表头的 CSV，支持 UTF-8 BOM 和分块读取。
2. 转换 Unix 时间戳，删除无效时间、空用户、非法行为类型和重复记录。
3. 筛选购买行为计算 RF。
4. 使用 `StandardScaler` 统一 R、F 量纲。
5. 评估 K=2 到 K=7 的 SSE 和轮廓系数。
6. 使用 K-Means 聚类，并基于每个分群的 R/F 均值动态生成业务标签。
7. 输出用户特征、分群汇总、图表和运行元数据。

## 四类用户画像

| 人群 | R 特征 | F 特征 | 运营策略 |
| --- | --- | --- | --- |
| 高价值用户 | 近期购买 | 高频购买 | 会员权益、新品优先体验、专属客服，重点做留存 |
| 潜力新用户 | 近期购买 | 低频购买 | 小额复购券、搭配推荐和二次购买提醒 |
| 流失老用户 | 长期未购买 | 历史高频 | 召回活动、限时优惠和历史品类推荐 |
| 沉睡用户 | 长期未购买 | 低频购买 | 低成本内容触达，控制高额补贴投入 |

cluster 编号没有固定业务含义。项目会根据聚类后的统计结果动态匹配标签，避免把 `cluster=0` 永远误认为高价值用户。

## 运行项目

建议使用 Python 3.10 或更高版本。

```bash
python -m venv .venv
```

Windows：

```powershell
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开：<http://localhost:8501>

首次打开会自动加载内置合成示例数据。使用真实数据时，在左侧关闭“使用内置示例数据”，上传 CSV 后点击“运行分析”。

## Docker 部署

```bash
docker build -t rf-kmeans-dashboard .
docker run --rm -p 8501:8501 rf-kmeans-dashboard
```

然后访问 <http://localhost:8501>。大型原始 CSV 不会被打包进 Docker 镜像，可以通过网页上传或挂载数据目录使用。

## 项目结构

```text
app.py                         Streamlit 页面入口
src/data_loader.py             CSV 读取、表头识别和分块加载
src/preprocessing.py           数据清洗和质量报告
src/feature_engineering.py     RF 与行为画像特征
src/clustering.py              K 值评估、K-Means、业务标签
src/visualization.py           Plotly 和静态 Matplotlib 图表
src/exporting.py               ZIP 下载结果
src/pipeline.py                端到端分析管线
notebooks/                     中文分析 Notebook
tests/                         单元测试和 Streamlit AppTest
outputs/                       CSV、JSON、PNG 输出目录
```

## 输出文件

运行分析后可以下载：

- `user_rf_features.csv`：用户级 R/F、行为画像和分群标签。
- `cluster_summary.csv`：每类用户数量、占比、R/F 均值和运营策略。
- `run_metadata.json`：数据范围、参考日期、K 值和质量统计。
- `figures/`：肘部法则、轮廓系数、用户分群散点图和占比图。

## 测试

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q
```

测试覆盖：

- 有表头/无表头 CSV。
- 时间转换、非法行为和重复数据处理。
- R/F 计算和行为画像。
- K 值边界和轮廓系数开关。
- cluster 编号打乱后的动态业务标签。
- 无购买行为数据的错误处理。
- 完整样例分析、图表、ZIP 输出。
- Streamlit 首屏示例数据加载。

## 面试项目描述

基于淘宝用户行为数据，构建 RF 用户特征体系，使用 StandardScaler 对最近购买间隔和购买频次进行标准化，并通过肘部法则、轮廓系数评估 K 值，使用 K-Means 完成用户分群。结合浏览、收藏、加购行为补充用户画像，将用户划分为高价值用户、潜力新用户、流失老用户和沉睡用户，并针对不同人群设计会员权益、复购激励、用户召回和低成本内容触达策略，最终通过 Streamlit 搭建可交互分析页面，实现分群结果和运营策略的可视化展示。

## 局限性和业务边界

- 没有金额字段，无法评估 GMV、客单价和利润贡献。
- F 是购买行为记录次数，不必然等于真实订单数量。
- K-Means 是无监督数学模型，业务标签需要人工解释。
- 聚类结果受数据周期、清洗规则和 K 值影响，建议按月重新运行。
- 运营策略需要通过 A/B 测试评估真实增量效果，不能直接把分群结果当成因果结论。
