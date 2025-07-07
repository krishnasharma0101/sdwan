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
    # Handle multi-row headers
    df_raw = pd.read_excel(uploaded_file, header=[0, 1])
    df_raw.columns = [
        '_'.join([str(i).strip() for i in col if pd.notna(i)]).replace(" ", "_")
        for col in df_raw.columns
    ]
    df = df_raw.copy()

    st.subheader("Sample Data Preview")
    st.dataframe(df.head())

    # Expected column names after flattening
    overlay_col = "Overlay_ID_Unnamed:_3_level_1"
    underlay_col = "Underlay_CID_Unnamed:4_level_1"
    source_col = "Applications_Source"
    destination_col = "Applications_Destination"
    policy_col = "SDWAN_policy_Unnamed:_10_level_1"
    forwarding_col = "Forwaridng_Profile_Unnamed:10_level_1"
    criteria_col = "Citeria_Unnamed:_19_level_1"
    next_hops = [
        "Next_Hop_Primary", "Next_Hop_Secondary", 
        "Next_Hop_Turtary", "Next_Hop_Quaternary"
    ]

    # Ensure all required columns exist
    required_cols = [
        overlay_col, underlay_col, source_col, destination_col, 
        policy_col, forwarding_col, criteria_col
    ] + next_hops

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Missing columns in uploaded file: {missing}")
        st.stop()

    # Destination filter
    unique_destinations = df[destination_col].dropna().unique().tolist()
    query_value = st.selectbox("Select Destination Application to Visualize", sorted(unique_destinations))

    if st.button("Generate Flow Diagram"):
        filtered_df = df[df[destination_col] == query_value]

        if filtered_df.empty:
            st.warning("No matching destination found.")
        else:
            G = Network(height="750px", width="100%", directed=True)
            G.barnes_hut()
            added_nodes = set()
            
            for _, row in filtered_df.iterrows():
                overlay = str(row[overlay_col])
                underlay = str(row[underlay_col])
                source = str(row[source_col])
                destination = str(row[destination_col])

                details = f"SD-WAN Policy: {row.get(policy_col, '')}<br>"
                details += f"Criteria: {row.get(criteria_col, '')}<br>"
                details += f"Forwarding Profile: {row.get(forwarding_col, '')}"

                if overlay not in added_nodes:
                    G.add_node(overlay, label=f"Overlay: {overlay}", title=details, color='#0074D9')
                    added_nodes.add(overlay)

                if source and source not in added_nodes:
                    G.add_node(source, label=f"Source: {source}", color='#2ECC40')
                    added_nodes.add(source)
                    G.add_edge(source, overlay, label="Source to Overlay")

                if underlay and underlay not in added_nodes:
                    G.add_node(underlay, label=f"Underlay: {underlay}", color='#1f77b4')
                    added_nodes.add(underlay)
                    G.add_edge(overlay, underlay, label="Overlay to Underlay")

                for priority, hop_col in zip(["Primary", "Secondary", "Tertiary", "Quarternary"], next_hops):
                    hop_val = row.get(hop_col)
                    if pd.notna(hop_val):
                        hop_val = str(hop_val)
                        if hop_val not in added_nodes:
                            G.add_node(hop_val, label=f"Next Hop ({priority}): {hop_val}", color='#FF851B')
                            added_nodes.add(hop_val)
                        G.add_edge(underlay, hop_val, label=f"To {priority}", color="#FF851B")

            # Save and render graph
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                G.write_html(tmp_file.name)
                with open(tmp_file.name, "r", encoding="utf-8") as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=750, scrolling=True)
                os.unlink(tmp_file.name)
