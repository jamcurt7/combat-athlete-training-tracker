from io import BytesIO
from typing import Dict

import pandas as pd

from src.analytics import (
    get_all_data,
    calculate_summary_metrics,
    calculate_exercise_summary,
    calculate_readiness_summary,
    calculate_weekly_volume,
    calculate_bodyweight_trend,
    calculate_estimated_1rm_trend,
    calculate_average_rpe_by_exercise,
)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def build_excel_export() -> BytesIO:
    """
    Build a multi-sheet Excel export in memory.
    """
    output = BytesIO()

    all_data = get_all_data()

    summary_metrics = calculate_summary_metrics()
    summary_df = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in summary_metrics.items()]
    )

    exercise_summary = calculate_exercise_summary()
    readiness_summary = calculate_readiness_summary()
    weekly_volume = calculate_weekly_volume()
    bodyweight_trend = calculate_bodyweight_trend()
    e1rm_trend = calculate_estimated_1rm_trend()
    avg_rpe = calculate_average_rpe_by_exercise()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        for table_name, df in all_data.items():
            safe_sheet_name = table_name[:31]

            if df.empty:
                pd.DataFrame({"message": ["No data available"]}).to_excel(
                    writer,
                    sheet_name=safe_sheet_name,
                    index=False,
                )
            else:
                df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

        write_optional_sheet(writer, "Exercise Summary", exercise_summary)
        write_optional_sheet(writer, "Readiness Summary", readiness_summary)
        write_optional_sheet(writer, "Weekly Volume", weekly_volume)
        write_optional_sheet(writer, "Bodyweight Trend", bodyweight_trend)
        write_optional_sheet(writer, "Estimated 1RM", e1rm_trend)
        write_optional_sheet(writer, "Average RPE", avg_rpe)

        workbook = writer.book

        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes(1, 0)
            worksheet.set_column(0, 20, 18)

        summary_sheet = writer.sheets["Summary"]
        header_format = workbook.add_format({"bold": True})
        summary_sheet.set_row(0, None, header_format)

    output.seek(0)
    return output


def write_optional_sheet(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    if df.empty:
        pd.DataFrame({"message": ["No data available"]}).to_excel(
            writer,
            sheet_name=sheet_name[:31],
            index=False,
        )
    else:
        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)


def get_export_tables() -> Dict[str, pd.DataFrame]:
    tables = get_all_data()

    tables["exercise_summary"] = calculate_exercise_summary()
    tables["readiness_summary"] = calculate_readiness_summary()
    tables["weekly_volume"] = calculate_weekly_volume()
    tables["bodyweight_trend"] = calculate_bodyweight_trend()
    tables["estimated_1rm_trend"] = calculate_estimated_1rm_trend()
    tables["average_rpe_by_exercise"] = calculate_average_rpe_by_exercise()

    return tables
