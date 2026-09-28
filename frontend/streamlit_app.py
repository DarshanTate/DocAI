import time
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="DocAI - Chat with Documents",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# CUSTOM STYLING (MODERN UI ENHANCEMENTS)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    /* Clean metric card & tag styling */
    .doc-pill {
        display: inline-flex;
        align-items: center;
        background-color: #f0f2f6;
        border: 1px solid #e0e3e9;
        border-radius: 8px;
        padding: 4px 10px;
        margin: 3px 0;
        font-size: 0.85rem;
        font-weight: 500;
        color: #1f2937;
        width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .source-box {
        border-left: 3px solid #3b82f6;
        background: rgba(59, 130, 246, 0.05);
        padding: 8px 12px;
        border-radius: 4px;
        margin: 6px 0;
        font-size: 0.88rem;
    }
    /* Auth container wrapper */
    .auth-container {
        max-width: 440px;
        margin: 3rem auto;
        padding: 2.2rem;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_document_ids" not in st.session_state:
    st.session_state.active_document_ids = []
if "active_documents" not in st.session_state:
    st.session_state.active_documents = []


# ---------------------------------------------------------
# API CLIENT HELPER
# ---------------------------------------------------------
def api_request(method: str, endpoint: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.request(
        method,
        f"{API_URL}{endpoint}",
        headers=headers,
        **kwargs,
    )


# ---------------------------------------------------------
# AUTHENTICATION SCREEN
# ---------------------------------------------------------
if not st.session_state.token:
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 2rem;">
                <h1 style="margin-bottom: 0.2rem;">📄 DocAI</h1>
                <p style="color: #6b7280; font-size: 0.95rem;">
                    Conversational intelligence for your private documents
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        auth_tab_login, auth_tab_register = st.tabs(["Sign In", "Create Account"])

        with auth_tab_login:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Work Email", placeholder="name@company.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.warning("Please provide both email and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            response = api_request(
                                "POST",
                                "/auth/login",
                                json={"email": email, "password": password},
                            )
                        if response.ok:
                            data = response.json()
                            st.session_state.token = data.get("access_token")
                            st.toast("Signed in successfully!", icon="✅")
                            st.rerun()
                        else:
                            detail = response.json().get("detail", "Invalid email or password.")
                            st.error(detail)

        with auth_tab_register:
            with st.form("register_form", clear_on_submit=False):
                reg_email = st.text_input("Work Email", placeholder="name@company.com")
                reg_password = st.text_input("Password", type="password", placeholder="Minimum 8 characters")
                reg_submitted = st.form_submit_button("Register", use_container_width=True)

                if reg_submitted:
                    if not reg_email or not reg_password:
                        st.warning("Please fill in all fields.")
                    else:
                        with st.spinner("Creating account..."):
                            response = api_request(
                                "POST",
                                "/auth/register",
                                json={"email": reg_email, "password": reg_password},
                            )
                        if response.ok:
                            st.success("Account created successfully. You can now log in.")
                        else:
                            detail = response.json().get("detail", "Registration failed.")
                            st.error(detail)
    st.stop()


# ---------------------------------------------------------
# HELPER: SOURCE RENDERER
# ---------------------------------------------------------
def render_sources(sources):
    with st.expander(f"📚 View Citations & Sources ({len(sources)})"):
        for source in sources:
            metadata = source.get("metadata", {})
            page = metadata.get("page")
            slide = metadata.get("slide")

            loc_str = ""
            if page is not None:
                loc_str = f"Page {page}"
            elif slide is not None:
                loc_str = f"Slide {slide}"

            header_text = f"Citation [{source.get('source_number', '•')}]"
            if loc_str:
                header_text += f" — {loc_str}"

            st.markdown(
                f"""
                <div class="source-box">
                    <strong>{header_text}</strong>
                    <div style="margin-top: 4px; color: #4b5563;">{source.get('content', '')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------
# SIDEBAR: DOCUMENT & SESSION MANAGEMENT
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 📄 **DocAI Workspace**")

    col_new_chat, col_logout = st.columns([1, 1])
    with col_new_chat:
        if st.button("＋ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.active_document_ids = []
            st.session_state.active_documents = []
            st.rerun()
    with col_logout:
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.divider()

    st.markdown("#### 📂 **Upload Documents**")
    uploaded_files = st.file_uploader(
    "Supported formats: PDF, DOCX, XLSX, CSV, TXT, PPTX, Images",
    type=[
        "pdf",
        "docx",
        "xlsx",
        "csv",
        "txt",
        "pptx",
        "png",
        "jpg",
        "jpeg",
        "webp",
    ],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

    if uploaded_files:

        new_files = [
            file
            for file in uploaded_files
            if not any(
                doc["filename"] == file.name
                for doc in st.session_state.active_documents
            )
        ]

        if new_files:

            files_payload = [
                (
                    "files",
                    (
                        file.name,
                        file.getvalue(),
                        file.type,
                    ),
                )
                for file in new_files
            ]

            with st.status(
                f"Uploading {len(new_files)} document(s)...",
                expanded=True,
            ) as upload_status:

                response = api_request(
                    "POST",
                    "/documents/upload",
                    files=files_payload,
                )

                if not response.ok:
                    try:
                        error = response.json().get(
                            "detail",
                            "Upload failed.",
                        )
                    except Exception:
                        error = response.text or "Upload failed."

                    upload_status.update(
                        label="Upload failed",
                        state="error",
                    )
                    st.error(error)

                else:
                    documents = response.json()

                    upload_status.write(
                        f"Successfully uploaded {len(documents)} document(s)."
                    )

                    for document in documents:
                        doc_id = document["id"]
                        filename = document["original_filename"]

                        st.session_state.active_document_ids.append(
                            doc_id
                        )

                        st.session_state.active_documents.append(
                            {
                                "id": doc_id,
                                "filename": filename,
                            }
                        )

                        upload_status.write(
                            f"📄 {filename} → queued for processing"
                        )

                    upload_status.update(
                        label=f"{len(documents)} document(s) queued",
                        state="complete",
                        expanded=True,
                    )

            st.rerun()

    st.markdown("#### 📑 **Indexed Files**")
    if st.session_state.active_documents:
        for doc in st.session_state.active_documents:
            st.markdown(f'<div class="doc-pill">📄 {doc["filename"]}</div>', unsafe_allow_html=True)
    else:
        st.caption("No files added to this session yet.")


# ---------------------------------------------------------
# MAIN CONTENT / CHAT INTERFACE
# ---------------------------------------------------------
if not st.session_state.active_documents:
    st.markdown(
        """
        <div style="text-align: center; padding: 4rem 1rem; border: 2px dashed #e5e7eb; border-radius: 12px; margin: 2rem 0;">
            <h3>Start by uploading a document</h3>
            <p style="color: #6b7280; max-width: 480px; margin: 0 auto;">
                Add PDFs, spreadsheets, slides, or documents via the sidebar. DocAI reads through pages to answer your queries with citations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Render historical conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                render_sources(message["sources"])

    # Query Input Dock
    if prompt := st.chat_input("Ask a question about your uploaded documents..."):
        # Display user input immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            response = api_request(
                "POST",
                "/query/stream",
                json={
                    "question": prompt,
                    "top_k": 5,
                    "document_ids": st.session_state.active_document_ids,
                    "chat_history": [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.messages[-21:-1]
                    ],
                },
                stream=True,
            )

            if response.ok:
                answer = ""
                message_placeholder = st.empty()

                for chunk in response.iter_content(
                    chunk_size=None,
                    decode_unicode=True,
                ):
                    if chunk:
                        answer += chunk
                        message_placeholder.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            else:
                try:
                    error_msg = response.json().get(
                        "detail",
                        "Error retrieving an answer.",
                    )
                except Exception:
                    error_msg = response.text or "Error retrieving an answer."

                st.error(error_msg)