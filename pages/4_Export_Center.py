import streamlit as st

from src.database import init_db
from src.analytics import (
    calculate_readiness_summary,
    calculate_bodyweight_trend,
    calculate_estimated_1rm_trend,
    calculate_weekly_volume,
    calculate_average_rpe_by_exercise,
)
from src.charts import (
    plotly_to_matplotlib_png_bytes,
    grouped_line_png_bytes,
)
from src.export_utils import (
    build_excel_export,
    get_export_tables,
    dataframe_to_csv_bytes,
)


st.set_page_config(page_title="Export Center", page_icon="📥", layout="wide")

init_db()

st.title("Export Center")

st.write("Download your training data as Excel, CSV files, and PNG charts.")

st.warning(
    "This app uses local SQLite storage. On Streamlit Community Cloud, use exports regularly as backups."
)

st.divider()

st.subheader("Full Excel Backup")

excel_file = build_excel_export()

st.download_button(
    label="Download Full Excel Workbook",
    data=excel_file,
    file_name="combat_athlete_training_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

st.divider()

st.subheader("CSV Table Downloads")

tables = get_export_tables()

selected_table_name = st.selectbox(
    "Choose table to download",
    sorted(tables.keys()),
)

selected_table = tables[selected_table_name]

if selected_table.empty:
    st.info("Selected table has no data yet.")
else:
    st.dataframe(selected_table, use_container_width=True, hide_index=True)

    st.download_button(
        label=f"Download {selected_table_name}.csv",
        data=dataframe_to_csv_bytes(selected_table),
        file_name=f"{selected_table_name}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

st.subheader("PNG Chart Downloads")

readiness = calculate_readiness_summary()
bodyweight = calculate_bodyweight_trend()
e1rm = calculate_estimated_1rm_trend()
weekly_volume = calculate_weekly_volume()
avg_rpe = calculate_average_rpe_by_exercise()

col1, col2 = st.columns(2)

with col1:
    readiness_png = plotly_to_matplotlib_png_bytes(
        title="Readiness Score Over Time",
        df=readiness,
        x_col="date",
        y_col="readiness_score",
    )

    st.download_button(
        label="Download Readiness Chart PNG",
        data=readiness_png,
        file_name="readiness_score_trend.png",
        mime="image/png",
        use_container_width=True,
    )

    bodyweight_png = plotly_to_matplotlib_png_bytes(
        title="Bodyweight Over Time",
        df=bodyweight,
        x_col="date",
        y_col="bodyweight",
    )

    st.download_button(
        label="Download Bodyweight Chart PNG",
        data=bodyweight_png,
        file_name="bodyweight_trend.png",
        mime="image/png",
        use_container_width=True,
    )

    avg_rpe_png = plotly_to_matplotlib_png_bytes(
        title="Average RPE by Exercise",
        df=avg_rpe,
        x_col="exercise_name",
        y_col="avg_rpe",
    )

    st.download_button(
        label="Download Average RPE Chart PNG",
        data=avg_rpe_png,
        file_name="average_rpe_by_exercise.png",
        mime="image/png",
        use_container_width=True,
    )

with col2:
    e1rm_png = grouped_line_png_bytes(
        title="Estimated 1RM Over Time",
        df=e1rm,
        x_col="date",
        y_col="best_estimated_1rm",
        group_col="exercise_name",
    )

    st.download_button(
        label="Download Estimated 1RM Chart PNG",
        data=e1rm_png,
        file_name="estimated_1rm_trend.png",
        mime="image/png",
        use_container_width=True,
    )

    weekly_volume_png = grouped_line_png_bytes(
        title="Weekly Volume by Movement Pattern",
        df=weekly_volume,
        x_col="week",
        y_col="total_volume",
        group_col="movement_pattern",
    )

    st.download_button(
        label="Download Weekly Volume Chart PNG",
        data=weekly_volume_png,
        file_name="weekly_volume_by_movement_pattern.png",
        mime="image/png",
        use_container_width=True,
    )

st.divider()

st.info(
    "Excel export includes raw logs, progression state, summaries, readiness trends, estimated 1RM data, and weekly volume tables."
)
