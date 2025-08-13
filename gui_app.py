# gui_app.py

import streamlit as st
import pandas as pd
from datetime import datetime
from codebase_manager import CodebaseManager
from config import AVAILABLE_MODELS, DEFAULT_MODEL, STORAGE_MODE_LOCAL, STORAGE_MODE_TEMP
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Codebase Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'manager' not in st.session_state:
    st.session_state.manager = CodebaseManager()

if 'current_codebase_id' not in st.session_state:
    st.session_state.current_codebase_id = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'selected_model' not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL

def main():
    st.title("🤖 Codebase Assistant")
    st.markdown("*Analyze and chat with your codebases using AI*")
    
    # Sidebar for codebase management
    with st.sidebar:
        st.header("📚 Codebase Management")
        
        # Current codebase display
        current_codebase = st.session_state.manager.get_current_codebase()
        if current_codebase:
            st.success(f"**Current:** {current_codebase['name']}")
        else:
            st.info("No codebase selected")
        
        st.markdown("---")
        
        # AI Model Selection
        st.subheader("🧠 AI Model")
        
        # Create options for selectbox
        model_options = []
        model_labels = {}
        
        for model_id, model_info in AVAILABLE_MODELS.items():
            label = f"{model_info['name']} ({model_info['provider']})"
            model_options.append(model_id)
            model_labels[model_id] = label
        
        # Model selection dropdown
        selected_model = st.selectbox(
            "Choose AI Model:",
            options=model_options,
            format_func=lambda x: model_labels[x],
            index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
            help="Different models have different capabilities and costs"
        )
        
        # Update session state if changed
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
            st.rerun()
        
        # Show model description
        if selected_model in AVAILABLE_MODELS:
            st.caption(f"💡 {AVAILABLE_MODELS[selected_model]['description']}")
        
        # Model testing button
        col_test1, col_test2 = st.columns([1, 1])
        with col_test1:
            if st.button("🧪 Test Models", help="Test all models to see which ones work"):
                with st.spinner("Testing models..."):
                    available_models = st.session_state.manager.get_available_models()
                    st.session_state.model_test_results = available_models
                    st.rerun()
        
        with col_test2:
            if st.button("🔄 Reset", help="Clear model test results"):
                if hasattr(st.session_state, 'model_test_results'):
                    del st.session_state.model_test_results
                st.rerun()
        
        # Show model test results if available
        if hasattr(st.session_state, 'model_test_results'):
            st.markdown("**Model Status:**")
            for model_id, model_info in st.session_state.model_test_results.items():
                if model_info.get('status') == 'available':
                    st.success(f"✅ {model_info['name']}")
                else:
                    st.error(f"❌ {model_info['name']}")
                    if 'error' in model_info:
                        st.caption(f"Error: {model_info['error'][:50]}...")
        
        st.markdown("---")
        
        # Tabs for different actions
        tab1, tab2, tab3 = st.tabs(["📋 List", "➕ Add", "⚙️ Manage"])
        
        with tab1:
            show_codebase_list()
        
        with tab2:
            show_add_codebase()
        
        with tab3:
            show_manage_codebases()
    
    # Main content area
    if current_codebase:
        show_chat_interface(current_codebase)
    else:
        show_welcome_screen()

def show_codebase_list():
    """Show list of available codebases."""
    codebases = st.session_state.manager.list_codebases()
    
    if not codebases:
        st.info("No codebases available. Add one using the 'Add' tab.")
        return
    
    st.subheader("Available Codebases")
    
    for codebase in codebases:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            is_current = st.session_state.current_codebase_id == codebase['id']
            status = "🟢 Active" if is_current else "⚪ Inactive"
            
            storage_mode = codebase.get('storage_mode', 'local')
            storage_icon = "🗂️" if storage_mode == 'local' else "⚡"
            
            st.markdown(f"""
            **{codebase['name']}** {status}  
            *{codebase['description'] or 'No description'}*  
            📁 {codebase['file_count']} files • 📄 {codebase['chunk_count']} chunks • {storage_icon} {storage_mode.title()}
            """)
            
            # Show commit hash for temporary storage
            if storage_mode == 'temporary' and codebase.get('commit_hash'):
                st.caption(f"🔄 Latest commit: {codebase['commit_hash'][:8]}")
        
        with col2:
            if st.button(f"Select", key=f"select_{codebase['id']}"):
                st.session_state.manager.switch_codebase(codebase['id'])
                st.session_state.current_codebase_id = codebase['id']
                st.session_state.chat_history = []  # Clear chat history
                st.rerun()

def show_add_codebase():
    """Show form to add new codebase."""
    st.subheader("Add New Codebase")
    
    with st.form("add_codebase_form"):
        name = st.text_input("Codebase Name", placeholder="My Awesome Project")
        repo_url = st.text_input("Repository URL", placeholder="https://github.com/user/repo")
        description = st.text_area("Description (optional)", placeholder="Brief description of the codebase")
        
        # Storage mode selection
        st.markdown("### 💾 Storage Mode")
        storage_mode = st.radio(
            "Choose how to store the repository:",
            options=[STORAGE_MODE_LOCAL, STORAGE_MODE_TEMP],
            format_func=lambda x: {
                STORAGE_MODE_LOCAL: "🗂️ Local Storage - Keep files on disk (traditional)",
                STORAGE_MODE_TEMP: "⚡ Temporary Processing - Process and delete files (saves space)"
            }[x],
            help="Local: Repository files are kept on your computer. Temporary: Files are processed and deleted immediately, only embeddings are stored.",
            index=0
        )
        
        # Show storage mode explanation
        if storage_mode == STORAGE_MODE_LOCAL:
            st.info("""
            **Local Storage Mode:**
            - ✅ Repository files saved to disk
            - ✅ Fast refresh/reprocess (no re-download)
            - ✅ Can browse files locally
            - ❌ Uses disk space
            - ❌ May cause file locking issues on Windows
            """)
        else:
            st.success("""
            **Temporary Processing Mode:**
            - ✅ No disk space used for repositories
            - ✅ No file locking issues
            - ✅ Always gets latest code on refresh
            - ❌ Slower refresh (re-downloads repository)
            - ❌ Cannot browse files locally
            """)
        
        submitted = st.form_submit_button("Add Codebase", type="primary")
        
        if submitted:
            if not name or not repo_url:
                st.error("Please provide both name and repository URL.")
                return
            
            try:
                with st.spinner(f"Adding codebase '{name}' ({storage_mode} mode)..."):
                    codebase_id = st.session_state.manager.add_codebase(name, repo_url, description, storage_mode)
                    st.success(f"Successfully added '{name}' using {storage_mode} storage!")
                    
                    # Auto-select the new codebase
                    st.session_state.manager.switch_codebase(codebase_id)
                    st.session_state.current_codebase_id = codebase_id
                    st.session_state.chat_history = []
                    
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error adding codebase: {e}")

def show_manage_codebases():
    """Show codebase management options."""
    st.subheader("Manage Codebases")
    
    codebases = st.session_state.manager.list_codebases()
    if not codebases:
        st.info("No codebases to manage.")
        return
    
    # Select codebase to manage
    codebase_names = [f"{cb['name']} (ID: {cb['id']})" for cb in codebases]
    selected_index = st.selectbox("Select codebase to manage:", range(len(codebase_names)), 
                                 format_func=lambda x: codebase_names[x])
    
    if selected_index is not None:
        selected_codebase = codebases[selected_index]
        
        # Show basic info about selected codebase
        st.markdown(f"**Selected:** {selected_codebase['name']}")
        st.markdown(f"📁 {selected_codebase['file_count']} files • 📄 {selected_codebase['chunk_count']} chunks")
        
        st.markdown("---")
        
        # Action buttons in a more organized layout
        st.markdown("**Available Actions:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 **Refresh**", key="refresh_btn", help="Full refresh: Re-clone repository and reprocess all files", use_container_width=True):
                with st.spinner("Refreshing codebase..."):
                    success = st.session_state.manager.refresh_codebase(selected_codebase['id'])
                    if success:
                        st.success("Codebase refreshed!")
                        st.rerun()
                    else:
                        st.error("Failed to refresh codebase.")
            st.caption("Re-clone repository")
        
        with col2:
            if st.button("⚡ **Reprocess**", key="reprocess_btn", help="Quick reprocess: Reprocess existing files without Git operations", use_container_width=True):
                with st.spinner("Reprocessing codebase..."):
                    success = st.session_state.manager.reprocess_codebase(selected_codebase['id'])
                    if success:
                        st.success("Codebase reprocessed!")
                        st.rerun()
                    else:
                        st.error("Failed to reprocess codebase.")
            st.caption("Reprocess files only")
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("📊 **View Statistics**", key="stats_btn", help="View detailed statistics and information", use_container_width=True):
                show_codebase_stats(selected_codebase)
            st.caption("Show detailed info")
        
        with col4:
            if st.button("🗑️ **Delete Codebase**", key="delete_btn", help="Permanently delete this codebase", use_container_width=True):
                st.session_state.show_delete_confirm = selected_codebase['id']
            st.caption("⚠️ Permanent deletion")
        
        # Delete confirmation
        if hasattr(st.session_state, 'show_delete_confirm') and st.session_state.show_delete_confirm == selected_codebase['id']:
            st.markdown("---")
            st.error(f"⚠️ **Confirm Deletion**")
            st.markdown(f"Are you sure you want to delete **'{selected_codebase['name']}'**?")
            st.markdown("*This action cannot be undone. All data and chat history will be permanently removed.*")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✅ Yes, Delete", key="confirm_delete", type="primary", use_container_width=True):
                    success = st.session_state.manager.delete_codebase(selected_codebase['id'])
                    if success:
                        st.success("Codebase deleted!")
                        if st.session_state.current_codebase_id == selected_codebase['id']:
                            st.session_state.current_codebase_id = None
                        delattr(st.session_state, 'show_delete_confirm')
                        st.rerun()
                    else:
                        st.error("Failed to delete codebase.")
            
            with col2:
                if st.button("❌ Cancel", key="cancel_delete", use_container_width=True):
                    delattr(st.session_state, 'show_delete_confirm')
                    st.rerun()

def show_codebase_stats(codebase):
    """Show detailed statistics for a codebase."""
    st.subheader(f"Stats for {codebase['name']}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Files", codebase['file_count'])
    
    with col2:
        st.metric("Chunks", codebase['chunk_count'])
    
    with col3:
        created_date = datetime.fromisoformat(codebase['created_at'].replace('Z', '+00:00'))
        st.metric("Created", created_date.strftime('%Y-%m-%d'))
    
    with col4:
        updated_date = datetime.fromisoformat(codebase['updated_at'].replace('Z', '+00:00'))
        st.metric("Updated", updated_date.strftime('%Y-%m-%d'))
    
    st.markdown(f"**Repository URL:** {codebase['repo_url']}")
    st.markdown(f"**Local Path:** {codebase['local_path']}")
    if codebase['description']:
        st.markdown(f"**Description:** {codebase['description']}")

def show_welcome_screen():
    """Show welcome screen when no codebase is selected."""
    st.markdown("""
    ## Welcome to Codebase Assistant! 🚀
    
    Get started by:
    
    1. **Add a codebase** using the sidebar ➕ Add tab
    2. **Select a codebase** from the 📋 List tab
    3. **Start chatting** with your code!
    
    ### Features:
    - 🔍 **Semantic search** through your codebase
    - 💬 **AI-powered answers** to your questions
    - 📚 **Multiple codebase** management
    - 📝 **Chat history** for each codebase
    - 🔄 **Auto-refresh** repositories
    
    ### Supported Languages:
    Python • JavaScript • TypeScript • Java • C++ • Go • and more!
    """)

def show_chat_interface(codebase):
    """Show the main chat interface."""
    st.header(f"💬 Chat with {codebase['name']}")
    
    # Load chat history
    if not st.session_state.chat_history:
        history = st.session_state.manager.get_chat_history(codebase['id'])
        st.session_state.chat_history = history
    
    # Display codebase info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files", codebase['file_count'])
    with col2:
        st.metric("Chunks", codebase['chunk_count'])
    with col3:
        if codebase['chunk_count'] == 0:
            col3a, col3b = st.columns([2, 1])
            with col3a:
                st.error("⚠️ No processable files")
            with col3b:
                if st.button("⚡ Fix", key="reprocess_current_codebase", help="Reprocess this codebase (no Git issues)"):
                    with st.spinner("Reprocessing..."):
                        success = st.session_state.manager.reprocess_codebase(codebase['id'])
                        if success:
                            st.success("Fixed!")
                            st.rerun()
                        else:
                            st.error("Fix failed")
        else:
            st.success("✅ Ready")
        
        # Emergency cleanup tools
        if codebase:
            with st.expander("🆘 Emergency Tools", expanded=False):
                st.markdown("Use these tools if refresh/reprocess keeps failing:")
                
                col_emergency1, col_emergency2 = st.columns(2)
                
                with col_emergency1:
                    if st.button("🧹 Force Cleanup", key="force_cleanup", 
                                help="Force cleanup ChromaDB files if locked", use_container_width=True):
                        with st.spinner("Force cleaning ChromaDB files..."):
                            # Try to force cleanup the embedding store
                            try:
                                import time
                                import gc
                                
                                # Remove from memory
                                if hasattr(st.session_state.manager.embedding_store, 'clients'):
                                    if codebase['id'] in st.session_state.manager.embedding_store.clients:
                                        del st.session_state.manager.embedding_store.clients[codebase['id']]
                                if hasattr(st.session_state.manager.embedding_store, 'collections'):
                                    if codebase['id'] in st.session_state.manager.embedding_store.collections:
                                        del st.session_state.manager.embedding_store.collections[codebase['id']]
                                
                                # Force garbage collection
                                gc.collect()
                                time.sleep(2)
                                
                                st.success("✅ Memory cleanup completed! Try reprocessing now.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Memory cleanup failed: {e}")
                
                with col_emergency2:
                    if st.button("📋 Manual Cleanup", key="manual_cleanup_info", 
                                help="Show manual cleanup instructions", use_container_width=True):
                        st.info("""
                        **Manual Cleanup Instructions:**
                        
                        1. **Stop the GUI** (Ctrl+C in terminal)
                        2. **Run cleanup script**: `python cleanup_chromadb.py`
                        3. **Select your codebase** to clean
                        4. **Restart GUI**: `python run_gui.py`
                        5. **Try reprocessing** again
                        
                        This fixes Windows file locking issues permanently.
                        """)
                        
                st.markdown("---")
    
    # Chat history display
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.chat_history:
            for entry in st.session_state.chat_history:
                # User question
                with st.chat_message("user"):
                    st.write(entry['question'])
                
                # AI answer
                with st.chat_message("assistant"):
                    st.write(entry['answer'])
                    
                    # Show model indicator if available
                    if 'model' in entry and entry['model']:
                        model_info = AVAILABLE_MODELS.get(entry['model'], {})
                        model_name = model_info.get('name', entry['model'])
                        model_provider = model_info.get('provider', 'Unknown')
                        st.caption(f"🤖 **{model_name}** ({model_provider})")
                    else:
                        # For legacy entries without model info, try to extract from answer
                        if entry['answer'].startswith('['):
                            # Extract model from answer format: [model] actual_answer
                            import re
                            match = re.match(r'\[([^\]]+)\]\s*(.*)', entry['answer'], re.DOTALL)
                            if match:
                                model_id = match.group(1)
                                model_info = AVAILABLE_MODELS.get(model_id, {})
                                model_name = model_info.get('name', model_id)
                                model_provider = model_info.get('provider', 'Unknown')
                                st.caption(f"🤖 **{model_name}** ({model_provider})")
        else:
            st.info("💬 No chat history yet. Ask a question to get started!")
    
    # Question input
    st.markdown("---")
    
    # Show current model info
    current_model_info = AVAILABLE_MODELS.get(st.session_state.selected_model, {})
    st.info(f"🧠 **Current AI Model:** {current_model_info.get('name', 'Unknown')} ({current_model_info.get('provider', 'Unknown')})")
    
    with st.form("question_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            question = st.text_input("Ask a question about the codebase:", 
                                   placeholder="What does this code do?")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some space
            submitted = st.form_submit_button("Send", use_container_width=True)
        
        if submitted and question:
            with st.spinner(f"Thinking with {AVAILABLE_MODELS.get(st.session_state.selected_model, {}).get('name', 'AI')}..."):
                # Use the selected model from session state
                answer = st.session_state.manager.query_codebase(
                    codebase['id'], 
                    question, 
                    model=st.session_state.selected_model
                )
                
                # Add to session chat history
                new_entry = {
                    'question': question,
                    'answer': answer,
                    'model': st.session_state.selected_model,
                    'created_at': datetime.now().isoformat()
                }
                st.session_state.chat_history.append(new_entry)
                
                st.rerun()

if __name__ == "__main__":
    main()
