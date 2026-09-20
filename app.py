"""Streamlit entry point for the RF + K-Means user segmentation dashboard."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.exporting import build_results_zip
from src.pipeline import AnalysisError, AnalysisResult, run_analysis
from src.visualization import build_figures, save_static_figures


OUTPUT_DIR = Path("outputs")
FIGURE_DIR = OUTPUT_DIR / "figures"


st.set_page_config(
    page_title="淘宝用户分群运营观测站",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --navy: #17324D;
        --signal: #1BB59A;
        --risk: #E58C4A;
        --paper: #F4F1EA;
        --surface: #FFFDF8;
        --ink: #17212B;
        --muted: #6D7882;
        --border: #D7D9D5;
    }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stSidebar"] { background: var(--navy); }
    [data-testid="stSidebar"] * { color: #F4F8F6; }
    [data-testid="stSidebar"] .stCaption { color: #B9C9D2; }
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 0.8rem;
        padding: 0.9rem 1rem;
        min-height: 7rem;
    }
    [data-testid="stMetricValue"] { color: var(--navy); font-family: 'Cascadia Mono', Consolas, monospace; }
    .hero {
        border-left: 5px solid var(--signal);
        padding: 0.25rem 0 0.25rem 1.1rem;
        margin: 0.25rem 0 1.6rem 0;
    }
    .eyebrow { color: var(--signal); font-size: 0.76rem; letter-spacing: 0.12em; text-transform: uppercase; font-weight: 700; }
    .hero h1 { color: var(--navy); margin: 0.2rem 0 0.35rem; font-size: clamp(1.7rem, 3vw, 2.65rem); }
    .hero p { color: var(--muted); margin: 0; max-width: 65rem; }
    .section-kicker { color: var(--navy); font-weight: 750; font-size: 1.05rem; margin-top: 1.4rem; }
    .source-badge { display: inline-block; border: 1px solid var(--border); border-radius: 999px; padding: 0.2rem 0.7rem; color: var(--muted); background: var(--surface); font-size: 0.8rem; }
    .boundary-note { border: 1px solid #D9C9AE; border-left: 4px solid var(--risk); background: #FFF7E9; border-radius: 0.65rem; padding: 0.75rem 0.9rem; color: #604B30; }
    .stButton > button, .stDownloadButton > button { border-radius: 0.55rem; min-height: 2.55rem; font-weight: 650; }
    button[data-testid="stBaseButton-primary"] { background: var(--signal) !important; border-color: var(--signal) !important; color: var(--navy) !important; }
    button[data-testid="stBaseButton-primary"] p { color: var(--navy) !important; }
    button:focus-visible, input:focus-visible, [role="button"]:focus-visible { outline: 2px solid var(--signal) !important; outline-offset: 2px !important; }
    @media (max-width: 800px) {
        .hero h1 { font-size: 1.65rem; }
        [data-testid="stMetric"] { min-height: 5.5rem; }
    }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def cached_analysis(
    source_bytes: bytes | None,
    selected_k: int,
    calculate_silhouette: bool,
    source_name: str,
) -> AnalysisResult:
    source = None if source_bytes is None else source_bytes
    return run_analysis(
        source,
        selected_k=selected_k,
        calculate_silhouette=calculate_silhouette,
        source_name=source_name,
    )


def _set_initial_result() -> None:
    if "analysis_result" in st.session_state:
        return
    try:
        st.session_state.analysis_result = cached_analysis(None, 4, True, "内置示例数据")
        st.session_state.source_name = "内置示例数据"
    except AnalysisError as exc:
        st.session_state.initial_error = str(exc)


def _render_overview(result: AnalysisResult) -> None:
    report = result.quality_report
    start = str(report.get("min_timestamp") or "—")[:10]
    end = str(report.get("max_timestamp") or "—")[:10]
    metrics = [
        ("原始记录数", report.get("input_rows", 0), "清洗前行为明细"),
        ("清洗后记录数", report.get("cleaned_rows", 0), "保留有效行为"),
        ("购买记录数", report.get("purchase_rows", 0), "behavior_type = 4"),
        ("用户总数", report.get("user_count", 0), "至少有一次购买"),
    ]
    columns = st.columns(4)
    for column, (label, value, help_text) in zip(columns, metrics):
        column.metric(label, value, help=help_text)
    date_columns = st.columns(2)
    compact_end = end[5:] if len(end) >= 10 else end
    date_columns[0].metric("数据时间范围", f"{start} → {compact_end}", help="有效行为时间；结束日期沿用起始日期年份")
    date_columns[1].metric("基准日期", result.metadata.get("reference_date", "—"), help="用于计算 R")


def _render_sidebar() -> tuple[bool, object | None, int, bool, bool]:
    with st.sidebar:
        st.markdown("## 运行控制台")
        st.caption("把购买行为转成可执行的人群策略")
        st.divider()
        use_sample = st.toggle("使用内置示例数据", value=True)
        uploaded_file = st.file_uploader(
            "上传淘宝行为 CSV",
            type=["csv"],
            disabled=use_sample,
            help="支持有表头或无表头文件，字段应为 user_id、item_id、category_id、behavior_type、timestamp。",
        )
        selected_k = st.slider("K 值", min_value=2, max_value=7, value=4, step=1)
        calculate_silhouette = st.toggle("计算轮廓系数", value=True)
        run_clicked = st.button("运行分析", type="primary", use_container_width=True)
        st.divider()
        st.caption("首次打开会自动加载示例数据；上传真实数据后，点击运行分析才会刷新结果。")
    return use_sample, uploaded_file, selected_k, calculate_silhouette, run_clicked


def _render_results(result: AnalysisResult) -> None:
    figures = build_figures(result)
    st.markdown('<div class="section-kicker">01 / 数据概览</div>', unsafe_allow_html=True)
    _render_overview(result)
    source_label = result.metadata.get("source_name", "当前数据")
    source_note = "示例数据，仅用于演示" if result.metadata.get("is_synthetic") else "真实上传数据"
    st.markdown(f'<span class="source-badge">{source_label} · {source_note}</span>', unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">02 / K 值评估</div>', unsafe_allow_html=True)
    metric_col, note_col = st.columns([2, 1])
    with metric_col:
        st.plotly_chart(figures["elbow"], use_container_width=True)
    with note_col:
        st.metric("推荐 K 值", result.recommend_k, help="优先参考轮廓系数；关闭轮廓系数时使用肘部法则。")
        st.metric("当前 K 值", result.metadata["selected_k"])
        if result.evaluation["silhouette"].notna().any():
            best_silhouette = result.evaluation["silhouette"].max()
            st.metric("最佳轮廓系数", f"{best_silhouette:.3f}")
        else:
            st.info("已关闭轮廓系数计算。")
    st.plotly_chart(figures["silhouette"], use_container_width=True)

    st.markdown('<div class="section-kicker">03 / 用户分群地图</div>', unsafe_allow_html=True)
    scatter_col, distribution_col = st.columns([1.65, 1])
    with scatter_col:
        st.plotly_chart(figures["scatter"], use_container_width=True)
        if len(result.user_features) > 10000:
            st.caption("用户数量较大，散点图仅抽样展示 10,000 个用户，聚类训练使用完整用户特征。")
    with distribution_col:
        st.plotly_chart(figures["distribution"], use_container_width=True)

    st.markdown('<div class="section-kicker">04 / 用户画像与运营策略</div>', unsafe_allow_html=True)
    summary = result.cluster_summary.copy()
    summary["user_ratio"] = (summary["user_ratio"] * 100).round(1).astype(str) + "%"
    summary = summary.rename(
        columns={
            "cluster_label": "人群标签",
            "user_count": "用户数",
            "user_ratio": "占比",
            "avg_R": "平均 R",
            "avg_F": "平均 F",
            "profile": "用户画像",
            "strategy": "运营策略",
        }
    )
    visible_summary = ["人群标签", "用户数", "占比", "平均 R", "平均 F", "用户画像", "运营策略"]
    st.dataframe(summary[visible_summary], hide_index=True, use_container_width=True)

    st.markdown('<div class="section-kicker">05 / 用户明细查询</div>', unsafe_allow_html=True)
    detail = result.user_features.copy()
    filter_col, r_col, f_col = st.columns([1.2, 1.2, 1.2])
    with filter_col:
        labels = ["全部"] + result.cluster_summary["cluster_label"].tolist()
        selected_label = st.selectbox("筛选分群", labels)
    with r_col:
        r_min, r_max = int(detail["R"].min()), int(detail["R"].max())
        r_range = st.slider("R 范围（天）", r_min, max(r_min, r_max), (r_min, r_max), step=1)
    with f_col:
        f_min, f_max = int(detail["F"].min()), int(detail["F"].max())
        f_range = st.slider("F 范围（次）", f_min, max(f_min, f_max), (f_min, f_max), step=1)
    if selected_label != "全部":
        detail = detail.loc[detail["cluster_label"] == selected_label]
    detail = detail.loc[
        detail["R"].between(r_range[0], r_range[1]) & detail["F"].between(f_range[0], f_range[1])
    ]
    detail_columns = [
        "user_id", "cluster_label", "R", "F", "browse_count", "favorite_count",
        "cart_count", "active_days", "last_buy_date",
    ]
    st.caption(f"当前显示 {len(detail):,} 位用户")
    st.dataframe(detail[detail_columns], hide_index=True, use_container_width=True)
    st.download_button(
        "下载当前筛选 CSV",
        data=detail.to_csv(index=False).encode("utf-8-sig"),
        file_name="filtered_user_segments.csv",
        mime="text/csv",
    )

    st.markdown(
        """
        <div class="boundary-note">
        <strong>数据边界：</strong>本项目不包含消费金额；F 表示购买行为记录次数，不等同于实际订单金额或收入贡献。
        K-Means 只负责数学分组，业务标签需要结合运营经验解释，策略效果还需要通过后续 A/B 测试验证。
        </div>
        """,
        unsafe_allow_html=True,
    )

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    save_static_figures(result, FIGURE_DIR)
    zip_bytes = build_results_zip(result, FIGURE_DIR)
    st.download_button(
        "下载全部结果 ZIP",
        data=zip_bytes,
        file_name="rf_kmeans_analysis_results.zip",
        mime="application/zip",
        type="primary",
    )


_set_initial_result()
use_sample, uploaded_file, selected_k, calculate_silhouette, run_clicked = _render_sidebar()

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">E-COMMERCE USER INTELLIGENCE / RF + K-MEANS</div>
      <h1>淘宝用户分群运营观测站</h1>
      <p>用最近购买间隔 R 和购买频次 F，把行为明细整理成可解释的人群画像与运营动作。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if run_clicked:
    if use_sample:
        source_bytes = None
        source_name = "内置示例数据"
    elif uploaded_file is None:
        st.error("请先上传 CSV 文件，或打开“使用内置示例数据”。")
        source_bytes = None
        source_name = ""
    else:
        source_bytes = uploaded_file.getvalue()
        source_name = uploaded_file.name
    if use_sample or uploaded_file is not None:
        try:
            with st.spinner("正在清洗数据、计算 RF 并训练 K-Means…"):
                st.session_state.analysis_result = cached_analysis(
                    source_bytes, selected_k, calculate_silhouette, source_name
                )
                st.session_state.source_name = source_name
            st.success("分析完成，结果已更新。")
        except AnalysisError as exc:
            st.error(str(exc))

if "initial_error" in st.session_state:
    st.error(st.session_state.initial_error)
elif "analysis_result" in st.session_state:
    _render_results(st.session_state.analysis_result)
else:
    st.info("准备数据后点击“运行分析”。")
