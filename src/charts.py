from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px


def plot_readiness_trend(checkins: pd.DataFrame):
    if checkins.empty:
        return None

    df = checkins.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    fig = px.line(
        df,
        x="date",
        y="readiness_score",
        markers=True,
        title="Readiness Score Over Time",
    )

    fig.update_layout(yaxis_title="Readiness Score", xaxis_title="Date")
    return fig


def plot_energy_sleep_soreness(checkins: pd.DataFrame):
    if checkins.empty:
        return None

    df = checkins.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    available_cols = [
        col for col in ["energy", "sleep_quality", "soreness", "mood", "stress"]
        if col in df.columns
    ]

    if not available_cols:
        return None

    melted = df.melt(
        id_vars="date",
        value_vars=available_cols,
        var_name="metric",
        value_name="value",
    )

    fig = px.line(
        melted,
        x="date",
        y="value",
        color="metric",
        markers=True,
        title="Daily Check-In Trends",
    )

    fig.update_layout(yaxis_title="Score", xaxis_title="Date")
    return fig


def plot_bodyweight(bodyweight_df: pd.DataFrame):
    if bodyweight_df.empty:
        return None

    df = bodyweight_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    fig = px.line(
        df,
        x="date",
        y="bodyweight",
        markers=True,
        title="Bodyweight Trend",
    )

    fig.update_layout(yaxis_title="Bodyweight", xaxis_title="Date")
    return fig


def plot_estimated_1rm(e1rm_df: pd.DataFrame):
    if e1rm_df.empty:
        return None

    df = e1rm_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    fig = px.line(
        df,
        x="date",
        y="best_estimated_1rm",
        color="exercise_name",
        markers=True,
        title="Estimated 1RM Trend",
    )

    fig.update_layout(yaxis_title="Estimated 1RM", xaxis_title="Date")
    return fig


def plot_weekly_volume(weekly_volume: pd.DataFrame):
    if weekly_volume.empty:
        return None

    fig = px.bar(
        weekly_volume,
        x="week",
        y="total_volume",
        color="movement_pattern",
        title="Weekly Volume by Movement Pattern",
    )

    fig.update_layout(yaxis_title="Volume Load", xaxis_title="Week")
    return fig


def plot_average_rpe(avg_rpe: pd.DataFrame):
    if avg_rpe.empty:
        return None

    fig = px.bar(
        avg_rpe,
        x="exercise_name",
        y="avg_rpe",
        title="Average RPE by Exercise",
    )

    fig.update_layout(yaxis_title="Average RPE", xaxis_title="Exercise")
    return fig


def plotly_to_matplotlib_png_bytes(title: str, df: pd.DataFrame, x_col: str, y_col: str) -> BytesIO:
    """
    Simple matplotlib PNG generator for download buttons.
    This avoids needing extra image export packages for Plotly.
    """
    buffer = BytesIO()

    fig, ax = plt.subplots(figsize=(10, 6))

    if df.empty or x_col not in df.columns or y_col not in df.columns:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.set_title(title)
    else:
        plot_df = df.copy()

        if "date" in x_col:
            plot_df[x_col] = pd.to_datetime(plot_df[x_col], errors="coerce")

        plot_df = plot_df.sort_values(x_col)
        ax.plot(plot_df[x_col], plot_df[y_col], marker="o")
        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)

    buffer.seek(0)
    return buffer


def grouped_line_png_bytes(
    title: str,
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    group_col: str,
) -> BytesIO:
    buffer = BytesIO()

    fig, ax = plt.subplots(figsize=(10, 6))

    if df.empty or x_col not in df.columns or y_col not in df.columns or group_col not in df.columns:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.set_title(title)
    else:
        plot_df = df.copy()

        if "date" in x_col:
            plot_df[x_col] = pd.to_datetime(plot_df[x_col], errors="coerce")

        for group_name, group_df in plot_df.groupby(group_col):
            group_df = group_df.sort_values(x_col)
            ax.plot(group_df[x_col], group_df[y_col], marker="o", label=str(group_name))

        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.legend()
        ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)

    buffer.seek(0)
    return buffer
