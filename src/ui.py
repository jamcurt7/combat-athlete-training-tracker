import streamlit as st


def readiness_badge(category: str, score: float | int | None = None) -> None:
    label = category or "Unknown"

    if score is not None:
        text = f"{label} — {score}/10"
    else:
        text = label

    if label == "Green":
        st.success(text)
    elif label == "Yellow":
        st.info(text)
    elif label == "Orange":
        st.warning(text)
    elif label == "Red":
        st.error(text)
    else:
        st.write(text)


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)

    if subtitle:
        st.write(subtitle)

    st.divider()


def empty_state(message: str) -> None:
    st.info(message)


def app_storage_warning() -> None:
    st.warning(
        "This app uses local SQLite storage. On Streamlit Community Cloud, use the Export Center regularly as a backup."
    )
