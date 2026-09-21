"""Interactive and static charts for the dashboard."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

from .pipeline import AnalysisResult


LABEL_COLORS = {
    "高价值用户": "#1BB59A",
    "潜力新用户": "#4F86C6",
    "流失老用户": "#E58C4A",
    "沉睡用户": "#8C7AA9",
}


def _color_map(labels: list[str]) -> dict[str, str]:
    fallback = ["#1BB59A", "#4F86C6", "#E58C4A", "#8C7AA9", "#6D7882", "#B94A48"]
    return {label: LABEL_COLORS.get(label, fallback[index % len(fallback)]) for index, label in enumerate(labels)}


def build_figures(result: AnalysisResult) -> dict[str, object]:
    """Build Plotly figures for Streamlit rendering."""

    evaluation = result.evaluation
    labels = result.cluster_summary["cluster_label"].tolist()
    colors = _color_map(labels)
    elbow = px.line(evaluation, x="k", y="inertia", markers=True, title="肘部法则：SSE 随 K 值变化")
    elbow.update_layout(xaxis_title="K 值", yaxis_title="SSE / 簇内平方和")

    silhouette = px.line(
        evaluation,
        x="k",
        y="silhouette",
        markers=True,
        title="轮廓系数：越接近 1 表示分群更清晰",
    )
    silhouette.update_layout(xaxis_title="K 值", yaxis_title="轮廓系数")

    display_data = result.user_features
    if len(display_data) > 10000:
        display_data = display_data.sample(10000, random_state=42)
    scatter = px.scatter(
        display_data,
        x="R",
        y="F",
        color="cluster_label",
        color_discrete_map=colors,
        hover_data=["user_id", "cluster"],
        title="用户分群散点图",
    )
    scatter.update_layout(xaxis_title="R｜最近购买间隔天数", yaxis_title="F｜购买频次")

    distribution = px.pie(
        result.cluster_summary,
        names="cluster_label",
        values="user_count",
        color="cluster_label",
        color_discrete_map=colors,
        hole=0.46,
        title="用户分群占比",
    )
    return {"elbow": elbow, "silhouette": silhouette, "scatter": scatter, "distribution": distribution}


def save_static_figures(result: AnalysisResult, output_dir: str | Path) -> dict[str, str]:
    """Save four PNG charts and return their filenames by chart key."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    labels = result.cluster_summary["cluster_label"].tolist()
    colors = _color_map(labels)
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    paths = {
        "elbow": "elbow_curve.png",
        "silhouette": "silhouette_curve.png",
        "scatter": "cluster_scatter.png",
        "distribution": "cluster_distribution.png",
    }

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(result.evaluation["k"], result.evaluation["inertia"], marker="o", color="#1BB59A")
    ax.set(title="肘部法则", xlabel="K 值", ylabel="SSE / 簇内平方和")
    fig.tight_layout()
    fig.savefig(directory / paths["elbow"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(result.evaluation["k"], result.evaluation["silhouette"], marker="o", color="#4F86C6")
    ax.set(title="轮廓系数", xlabel="K 值", ylabel="轮廓系数")
    fig.tight_layout()
    fig.savefig(directory / paths["silhouette"], dpi=160)
    plt.close(fig)

    display_data = result.user_features
    if len(display_data) > 10000:
        display_data = display_data.sample(10000, random_state=42)
    fig, ax = plt.subplots(figsize=(8, 5))
    for label, group in display_data.groupby("cluster_label", sort=False):
        ax.scatter(group["R"], group["F"], s=20, alpha=0.55, label=label, color=colors[label])
    ax.set(title="用户分群散点图", xlabel="R｜最近购买间隔天数", ylabel="F｜购买频次")
    ax.legend()
    fig.tight_layout()
    fig.savefig(directory / paths["scatter"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.pie(
        result.cluster_summary["user_count"],
        labels=result.cluster_summary["cluster_label"],
        autopct="%.1f%%",
        colors=[colors[label] for label in result.cluster_summary["cluster_label"]],
        startangle=90,
    )
    ax.set_title("用户分群占比")
    fig.tight_layout()
    fig.savefig(directory / paths["distribution"], dpi=160)
    plt.close(fig)
    return paths
