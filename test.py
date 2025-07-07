import streamlit as st
import pandas as pd
from pyvis.network import Network
import tempfile
import os

st.set_page_config(layout="wide")
st.title("SD-WAN Flow Visualizer")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Excel Headers and Sample Data")
    st.write(df.head())

    # --- Column Selection ---
    columns = df.columns.tolist()
    destination_col = st.selectbox("Select Destination Application Column", columns)
    source_col = st.selectbox("Select Source Column", columns)
    overlay_col = st.selectbox("Select Overlay ID Column", columns)
    underlay_col = st.selectbox("Select Underlay ID Column", columns)
    policy_col = st.selectbox("Select SD-WAN Policy Column", columns)
    criteria_col = st.selectbox("Select Criteria Column", columns)
    forwarding_col = st.selectbox("Select SLA/Forwarding Profile Column", columns)

    query_value = st.text_input("Enter Destination Application to Visualize")

    if st.button("Generate Flow Diagram"):
        if query_value:
            filtered_df = df[df[destination_col].astype(str).str.contains(query_value, case=False, na=False)]

            if filtered_df.empty:
                st.warning("No matching destination found.")
            else:
                # Build graph
                G = Network(height="700px", width="100%", directed=True)
                G.barnes_hut()

                added_nodes = set()  # Track added nodes to avoid duplicates

                for _, row in filtered_df.iterrows():
                    overlay = str(row[overlay_col])
                    underlay = str(row[underlay_col])
                    source = str(row[source_col])
                    destination = str(row[destination_col])

                    details = f"SD-WAN Policy: {row.get(policy_col, '')}<br>"
                    details += f"Criteria: {row.get(criteria_col, '')}<br>"
                    details += f"Forwarding Profile: {row.get(forwarding_col, '')}"

                    # Add nodes if not already added
                    if overlay not in added_nodes:
                        G.add_node(overlay, label=f"Overlay ID: {overlay}", title=details, color='#0074D9')
                        added_nodes.add(overlay)

                    if underlay and underlay not in added_nodes:
                        G.add_node(underlay, label=f"Underlay ID: {underlay}", color='#1f77b4')
                        added_nodes.add(underlay)

                    if source and source not in added_nodes:
                        G.add_node(source, label=f"Source: {source}", color='#2ECC40')
                        added_nodes.add(source)

                    if destination and destination not in added_nodes:
                        G.add_node(destination, label=f"Destination: {destination}", color='#FF4136')
                        added_nodes.add(destination)

                    # Now add edges safely
                    if overlay and underlay:
                        G.add_edge(overlay, underlay, label="Underlay ID", color='#1f77b4')

                    if source and overlay:
                        G.add_edge(source, overlay, label="Source -> Overlay")

                    if underlay and destination:
                        G.add_edge(underlay, destination, label="Underlay -> Destination")

                # Save and render HTML (no show())
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                    G.write_html(tmp_file.name)

                    with open(tmp_file.name, "r", encoding="utf-8") as f:
                        html_content = f.read()

                    st.components.v1.html(html_content, height=750, scrolling=True)
                    os.unlink(tmp_file.name)
        else:
            st.warning("Please enter a destination to query.")
