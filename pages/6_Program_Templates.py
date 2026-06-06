import streamlit as st

from src.database import init_db, get_setting, set_setting
from src.template_library import get_training_templates, get_template_by_key
from src.ui import page_header


st.set_page_config(page_title="Program Templates", page_icon="🧠", layout="wide")

init_db()

page_header(
    "Program Templates",
    "Choose the training style the workout generator should bias toward.",
)

templates = get_training_templates()

current_key = get_setting("selected_template_key", "balanced")
current_template = get_template_by_key(current_key)

st.subheader("Current Template Bias")

st.success(current_template["name"])
st.write(current_template["description"])
st.caption(f"Best for: {current_template['best_for']}")

st.divider()

st.subheader("Choose Template")

template_names = [template["name"] for template in templates]
template_name_to_key = {template["name"]: template["key"] for template in templates}

current_index = 0

for index, template in enumerate(templates):
    if template["key"] == current_key:
        current_index = index
        break

selected_name = st.selectbox(
    "Training template bias",
    template_names,
    index=current_index,
)

selected_key = template_name_to_key[selected_name]
selected_template = get_template_by_key(selected_key)

with st.container(border=True):
    st.markdown(f"### {selected_template['name']}")
    st.write(selected_template["description"])
    st.write(f"**Best for:** {selected_template['best_for']}")

    st.markdown("**This template emphasizes:**")
    for item in selected_template["influences"]:
        st.write(f"- {item}")

if st.button("Save Selected Template", use_container_width=True):
    set_setting("selected_template_key", selected_key)
    st.success(f"Template saved: {selected_template['name']}")

st.divider()

st.subheader("Template Library")

for template in templates:
    with st.expander(template["name"]):
        st.write(template["description"])
        st.write(f"**Best for:** {template['best_for']}")
        st.markdown("**Influences:**")
        for item in template["influences"]:
            st.write(f"- {item}")
