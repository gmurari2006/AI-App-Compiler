import streamlit as st
import json

from app.intent_extractor.extractor import extract_intent
from app.system_designer.designer import design_system
from app.schema_generator.generator import generate_schema
from app.validator.validator import validate_schema
from app.repair_engine.repair import repair_schema

# Page Config
st.set_page_config(
    page_title="AI App Compiler",
    page_icon="🚀",
    layout="wide"
)

# Header
st.title("🚀 AI App Compiler")
st.subheader("Convert App Ideas into Architecture & Schemas")

# Input Box
app_idea = st.text_area(
    "Enter App Idea",
    value="Build a CRM with login, contacts, dashboard and admin analytics",
    height=150
)

# Generate Button
if st.button("Generate"):

    with st.spinner("Generating application architecture..."):

        try:
            # Step 1 - Intent Extraction
            intent = extract_intent(app_idea)

            # Step 2 - System Design
            architecture = design_system(intent)

            # Step 3 - Schema Generation
            schema = generate_schema(architecture)

            # Step 4 - Validation
            validation = validate_schema(schema)

            # Step 5 - Repair
            repaired_schema = repair_schema(
                schema,
                validation
            )

        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    st.success("✅ Generation Complete!")

    # Dashboard Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "📄 Pages",
            len(architecture.get("pages", []))
        )

    with col2:
        st.metric(
            "🗄️ Entities",
            len(architecture.get("entities", []))
        )

    with col3:
        st.metric(
            "👥 Roles",
            len(architecture.get("roles", []))
        )

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Intent",
        "Architecture",
        "Schema",
        "Validation",
        "Repaired Schema"
    ])

    with tab1:
        st.subheader("Intent Extraction")
        st.json(intent)

    with tab2:
        st.subheader("System Design")
        st.json(architecture)

    with tab3:
        st.subheader("Generated Schema")
        st.json(schema)

    with tab4:
        st.subheader("Validation Result")
        st.json(validation)

    with tab5:
        st.subheader("Repaired Schema")
        st.json(repaired_schema)

    # Download Button
    st.download_button(
        label="📥 Download Repaired Schema",
        data=json.dumps(repaired_schema, indent=2),
        file_name="schema.json",
        mime="application/json"
    )