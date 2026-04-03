
import streamlit as st
import uuid
from datetime import datetime
import base64
import requests
from config.settings import settings
from PIL import Image

chatbot_icon=Image.open("assets/robot.png")

API_BASE_URL = settings.API_BASE_URL


def create_session_api(session_id, user_id):
    url = f"{API_BASE_URL}/session/create"
    res = requests.post(url, json={"session_id": session_id, "user_id": user_id})
    return res.json()


def get_sessions_api(user_id, limit=20):
    url = f"{API_BASE_URL}/sessions/{user_id}"
    res = requests.get(url, params={"limit": limit})
    return res.json()


def get_chat_messages_api(session_id):
    url = f"{API_BASE_URL}/chat/{session_id}"
    res = requests.get(url, params={"limit": 30})
    return res.json()


def save_message_api(message):
    url = f"{API_BASE_URL}/message"
    requests.post(url, json=message)


def clear_chat_api(session_id):
    url = f"{API_BASE_URL}/chat/{session_id}"
    requests.delete(url)


def delete_session_api(session_id):
    url = f"{API_BASE_URL}/session/delete"
    res = requests.delete(url, params={"session_id": session_id})
    return res.json()

def streamlit_executor():
    st.set_page_config(
        page_title="ChatAgent",
        page_icon=chatbot_icon,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    user_id=st.session_state.get("user_id")
    
        
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent="Generic"
        
    if "current_session" not in st.session_state:
        existing_sessions = get_sessions_api(user_id, limit=1)
        if existing_sessions and len(existing_sessions) > 0:
            st.session_state.current_session = existing_sessions[0].get("session_id")
        else:
            sid = str(uuid.uuid4())
            create_session_api(sid, user_id)
            st.session_state.current_session=sid
        
    def new_chat():
        sid=str(uuid.uuid4())
        result = create_session_api(session_id=sid, user_id=user_id)
        if result:
            st.session_state.current_session=sid
    
    def clear_chat(session_id):
        result=clear_chat_api(session_id=session_id)
    
    def get_chat_messages(session_id):
        result=get_chat_messages_api(session_id=session_id)
        return result
    
    def save_message(message):
        try:
            save_message_api(message=message)
        except Exception as e:
            print(f"Error saving message: {e}")
            
    def agent_executor(query, session_id):
        """Route to appropriate agent executor."""
        selected_agent = st.session_state.selected_agent
        if selected_agent=='Coder':
            from agents.Coder import coder_executor
            return coder_executor(query=query,session_id=session_id)
        elif selected_agent=='Researcher':
            from agents.Researcher import researcher_executor
            return researcher_executor(query=query,session_id=session_id)
        elif selected_agent=="RAG":
            from agents.RAG_agent import rag_executor
            return rag_executor(query=query,session_id=session_id)
        else:
            from agents.Generic import generic_executor 
            return generic_executor(query=query,session_id=session_id)

    def get_session_list():
        result=get_sessions_api(user_id, limit=20)
        sessions_list=[]
        session_titles=[]
        
        for id in result:
            session_titles.append(id.get("title","New Chat"))
            sessions_list.append(id.get("session_id"))
        return sessions_list ,session_titles
        
    with st.sidebar:
        s_col1, c2, c3 = st.columns([5, 1, 1])
        with s_col1:
            if st.button("🏠︎Home", key="back_to_home", help="Back to Dashboard"):
                st.switch_page("main.py")
        
        agent_selection=st.pills("Select Agent",["Generic","Coder","Researcher","RAG"],
                                 default="Generic",selection_mode="single")
        
        prev_agent_key = "prev_selected_agent"
        if st.session_state.get(prev_agent_key) != agent_selection:
            # Wipe all fb_ keys so stale previews never bleed through
            for k in list(st.session_state.keys()):
                if k.startswith("fb_"):
                    del st.session_state[k]
            st.session_state[prev_agent_key] = agent_selection

        st.session_state.selected_agent = agent_selection

        if agent_selection == "Coder":
            st.markdown("---")
            if st.button("Workspace Explorer", use_container_width=True):
                st.switch_page("pages/workspace_explorer.py")
        
        #st.markdown("---")
        col1,col2=st.columns([4,4])
        with col1:
            st.button(":blue[New chat]",on_click=new_chat)
            
        with col2:
            st.button(":orange[Clear chat]",on_click=lambda: clear_chat(st.session_state.current_session))
        
        st.markdown("---")
        session_ids,session_titles=get_session_list()
        
        for idx,ids in enumerate(session_ids):        
            if ids==st.session_state.current_session:
                label=f"🔵  {session_titles[idx][:24]}"
            else:
                label=f"⚪  {session_titles[idx][:24]}"
            
            col1,col2=st.columns([5,2])
            with col1:
                if st.button(label=label,key=f"key_{ids}"):
                    st.session_state.current_session=ids
                    st.rerun()
            with col2:
                if st.button(label=":red[Delete]",key=f'delete_key{ids}'):
                    result = delete_session_api(ids)
                    if result:
                        current_session=st.session_state.current_session
                        if current_session==ids:
                            updated_sessions,_ = get_session_list()
                            if updated_sessions:
                                st.session_state.current_session = updated_sessions[0]
                            else:
                                new_chat()
                        st.rerun()
                    
    st.title(":blue[Chat Agent]",text_alignment ='center')
    
    current_session=st.session_state.current_session
    messages_list=get_chat_messages(current_session)
    for messages in messages_list:
        with st.chat_message(messages.get("role")):
            if messages.get("role")=='user':
                st.write(messages.get("content"))
                if messages.get("sources"):
                    try:
                        image_data = base64.b64decode(messages.get("sources"))
                        st.image(image_data)
                    except Exception as e:
                        print(f"Error displaying image: {e}")
                    
            if messages.get("role")=='assistant':
                st.markdown(messages.get("content"))
            
    
    query=st.chat_input(placeholder="Enter your query",accept_file=True)
    
    current_sessionID=st.session_state.current_session
    
    if query is not None and query.text.strip():
        message={"session_id":current_sessionID,
                 "role":"user",
                 "content":query.text,
                 "timestamp":datetime.utcnow().isoformat(),
                 "agent_name":st.session_state.selected_agent,
                 "user_id":user_id}

        image_source = None
        
        if len(query.files) > 0 and query.files[0].type.startswith('image/'):
            uploaded_file = query.files[0]
            image_bytes = uploaded_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            message["sources"] = image_base64
            image_source = uploaded_file

        with st.chat_message("user"):
            st.markdown(query.text)
            if image_source:
                st.image(image_source)
        
        save_message(message)
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            output = ""
            try:
                for chunk in agent_executor(query, st.session_state.current_session):
                    output += chunk
                    placeholder.markdown(output)
            except Exception as e:
                st.markdown(f"Unable to execute the query rightnow!, try again later,{e}")
                output=f"Unable to execute the query rightnow!, try again later,{e}"
        
        if st.session_state.selected_agent == "Coder":
            st.session_state[f"coder_done_{st.session_state.current_session}"] = True
            # Reset file selection so browser starts fresh after each response
            fb_sel_key = f"fb_sel_{st.session_state.current_session}"
            st.session_state[fb_sel_key] = None

        message={"session_id":current_sessionID,
                 "role":"assistant",
                 "content":output,
                 "timestamp":datetime.utcnow().isoformat(),
                 "agent_name":st.session_state.selected_agent,
                 "user_id":user_id}
        save_message(message=message)
        
        st.rerun()
    coder_done_key = f"coder_done_{st.session_state.current_session}"
    if (st.session_state.get("selected_agent") == "Coder"
        and st.session_state.get(coder_done_key, False)):

        from utils.file_browser import render_file_browser
        render_file_browser(
            workspace=f"{settings.CODER_BASE_PATH}/{st.session_state.current_session}",
            session_id=current_session,
        )
streamlit_executor()
    
    