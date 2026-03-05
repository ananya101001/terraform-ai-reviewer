import streamlit as st
import sys
import os
import tempfile
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.graph import run_review

st.set_page_config(page_title="Cloud Architecture Reviewer", page_icon="☁️", layout="wide")
st.title("☁️ Cloud Architecture Reviewer")
st.markdown("*Multi-Agent AI system for reviewing Terraform infrastructure*")
st.divider()

with st.sidebar:
    st.header("⚙️ Agents")
    st.markdown("🔍 IaC Parser\n\n🔐 Security Agent\n\n💰 Cost Agent\n\n📋 Best Practices Agent\n\n✍️ Writer Agent")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 Upload Terraform Files")
    uploaded_files = st.file_uploader("Upload your .tf files", accept_multiple_files=True, type=["tf"])

with col2:
    st.subheader("📂 Or Use Sample")
    use_sample = st.button("🧪 Run on Sample Terraform", type="secondary", use_container_width=True)
    st.caption("Sample has intentional security + cost issues for demo")

terraform_path = None

if uploaded_files:
    tmp_dir = tempfile.mkdtemp()
    for uploaded_file in uploaded_files:
        file_path = os.path.join(tmp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
    terraform_path = tmp_dir
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

elif use_sample:
    terraform_path = "./sample_terraform"

if terraform_path:
    st.divider()
    with st.spinner("🤖 Running multi-agent review... (~30-60 seconds)"):
        try:
            result = run_review(terraform_path)

            if result.get("error"):
                st.error(f" Error: {result['error']}")
            else:
                parsed = result.get("parsed_iac", {})
                findings = result.get("security_findings", {})
                summary = findings.get("summary", {})

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Resources Found", parsed.get("resource_count", 0))
                m2.metric("Security Issues", summary.get("total_failed", "—"))
                m3.metric("Checks Passed", summary.get("total_passed", "—"))
                m4.metric("Resource Types", len(parsed.get("resource_types", [])))

                st.divider()
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Final Report", "🔐 Security", "💰 Cost", "⭐ Best Practices"])

                with tab1:
                    st.markdown(result.get("final_report", "No report generated"))
                with tab2:
                    st.markdown(result.get("security_review", "No security review"))
                with tab3:
                    st.markdown(result.get("cost_review", "No cost review"))
                with tab4:
                    st.markdown(result.get("best_practices_review", "No best practices review"))

                st.divider()
                report = f"# Architecture Review\n\n{result.get('final_report','')}"
                st.download_button("⬇️ Download Report", data=report, file_name="review.md", mime="text/markdown", type="primary")

        except Exception as e:
            st.error(f" Failed: {str(e)}")
            st.exception(e)