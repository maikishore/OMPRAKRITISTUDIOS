import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.config import settings
from core.modal_service import ModalService

st.set_page_config(page_title="Studio Settings & Modal GPU Control | MicroDrama Studio", page_icon="⚙️", layout="wide")

st.title("⚙️ Studio Settings & Cloud GPU Control Center")
st.caption("Manage Modal GPU serverless deployments, test live model connections, stop active GPU workers to save costs, and configure AI providers.")

tab_modal, tab_llm, tab_storage = st.tabs([
    "🚀 Modal Serverless GPU Cluster",
    "🧠 LLM & Story Engine Settings",
    "💾 Storage & Database Settings"
])

# -------------------------------------------------------------
# TAB 1: MODAL SERVERLESS GPU CLUSTER CONTROL
# -------------------------------------------------------------
with tab_modal:
    st.subheader("⚡ Modal GPU Cluster Status & Model Manager")

    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        profile = ModalService.get_current_profile()
        if profile:
            st.success(f"🟢 **Connected to Modal Workspace:** `{profile}`")
        else:
            st.warning("⚠️ Modal CLI not authenticated or profile not detected. Run `modal setup` in terminal if needed.")

    with top_c2:
        if st.button("🔄 Refresh Cluster Status", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Fetch currently deployed apps
    deployed_apps = ModalService.list_deployed_apps()

    st.markdown("#### 📦 Active Deployed Modal Apps")
    if not deployed_apps:
        st.info("ℹ️ No Modal apps are currently deployed or running in your workspace.")
    else:
        app_rows = []
        for a in deployed_apps:
            app_rows.append({
                "App Name / Description": a.get("description", "N/A"),
                "App ID": a.get("app_id", "N/A"),
                "State": a.get("state", "N/A").upper(),
                "Active Tasks / Containers": a.get("tasks", "0"),
                "Created At": a.get("created_at", "N/A")
            })
        st.dataframe(app_rows, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🎛️ Individual GPU Model Control & Deployment")
    st.caption("Deploy, test, or terminate individual GPU model pipelines on Modal to optimize cost and performance.")

    for model_info in ModalService.AVAILABLE_MODELS:
        m_id = model_info["id"]
        app_name = model_info["app_name"]
        cls_name = model_info["class_name"]
        worker_file = model_info["worker_file"]
        is_dep, dep_data = ModalService.is_app_deployed(app_name)

        with st.container(border=True):
            hdr_col1, hdr_col2 = st.columns([3, 1])
            with hdr_col1:
                st.markdown(f"### {model_info['name']}")
                st.caption(f"**App Name:** `{app_name}` | **Target GPU:** `{model_info['gpu']}` | **Phase:** `{model_info['phase']}`")
                st.write(model_info["description"])
            with hdr_col2:
                if is_dep:
                    st.success("🟢 **DEPLOYED & READY**")
                    if dep_data and dep_data.get("app_id"):
                        st.caption(f"ID: `{dep_data['app_id'][:12]}...`")
                else:
                    st.info("⚪ **STOPPED / NOT DEPLOYED**")

            # Inactivity Timeout Setting
            set_c1, set_c2 = st.columns([1, 2])
            with set_c1:
                idle_timeout_m = st.selectbox(
                    "⏳ Auto-Shutdown Idle Window",
                    options=[5, 10, 15, 30, 60],
                    index=2,
                    key=f"idle_to_{m_id}",
                    help="Modal automatically shuts down the GPU worker if no generation requests are received within this time window."
                )

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                deploy_btn_label = "🚀 Redeploy Model" if is_dep else "🚀 Deploy to Modal GPU"
                if st.button(deploy_btn_label, key=f"dep_btn_{m_id}", use_container_width=True, type="primary" if not is_dep else "secondary"):
                    with st.spinner(f"Deploying {model_info['name']} ({worker_file}) with {idle_timeout_m}m auto-shutdown window..."):
                        success, out = ModalService.deploy_worker(
                            worker_file,
                            root_dir=ROOT_DIR,
                            inactivity_timeout_minutes=idle_timeout_m
                        )
                        if success:
                            st.success(f"Successfully deployed `{app_name}` (Auto-shutdown: {idle_timeout_m}m)!")
                            with st.expander("📄 Deployment Output Logs", expanded=True):
                                st.code(out)
                            st.rerun()
                        else:
                            st.error(f"Deployment failed for `{app_name}`.")
                            st.code(out)

            with btn_col2:
                if st.button("🔌 Test Connection & Health", key=f"test_btn_{m_id}", use_container_width=True):
                    with st.spinner(f"Pinging `{app_name}.{cls_name}` on Modal..."):
                        ok, msg = ModalService.test_connection(app_name, cls_name)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

            with btn_col3:
                if st.button("🛑 Stop Model (Save GPU Credits)", key=f"stop_btn_{m_id}", use_container_width=True, disabled=not is_dep):
                    with st.spinner(f"Stopping App `{app_name}` and terminating GPU containers..."):
                        ok, msg = ModalService.stop_app(app_name)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

# -------------------------------------------------------------
# TAB 2: LLM & STORY ENGINE SETTINGS
# -------------------------------------------------------------
with tab_llm:
    st.subheader("🧠 Large Language Model (Story & Shot Engine)")
    st.caption("Configure the primary AI model used for narrative bible compilation, scene breakdown, and shot compilation.")

    llm_col1, llm_col2 = st.columns(2)
    with llm_col1:
        st.text_input("Active LLM Provider", value=settings.LLM_PROVIDER, disabled=True)
        st.text_input("Primary Model Name", value=settings.LLM_MODEL, disabled=True)
    llm_key_present = bool(getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "LLM_API_KEY", None) or getattr(settings, "CLOUDFLARE_AUTH_TOKEN", None))
    with llm_col2:
        st.text_input("LLM API Key / Token Status", value="✅ Configured via environment" if llm_key_present else "❌ Missing", disabled=True)
        st.text_input("Temperature", value="0.7 (Cinematic Creative)", disabled=True)

    st.info("💡 To change the LLM model or switch to another provider, update the `.env` configuration file in the project root.")

# -------------------------------------------------------------
# TAB 3: STORAGE & DATABASE SETTINGS
# -------------------------------------------------------------
with tab_storage:
    st.subheader("💾 Database & Media Storage")
    st.text_input("Database Connection URI", value=settings.DATABASE_URL, disabled=True)
    st.text_input("Local Media Storage Directory", value=str(settings.STORAGE_ROOT), disabled=True)
    st.caption("Supports local SQLite and Supabase PostgreSQL with local or cloud S3/R2 storage.")
