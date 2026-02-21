
import streamlit as st
import uuid
from datetime import datetime
import base64

def streamlit_executor():
    st.set_page_config(
        page_title="ChatAgent",
        page_icon="💬",
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
            
    if "mongodb" not in st.session_state:
        from Mongodb.mongodb_server import MongoStore
        st.session_state.mongodb=MongoStore()
        
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent="Generic"
        
    if "current_session" not in st.session_state:
        existing_sessions = st.session_state.mongodb.get_sessions(user_id="admin", limit=1)
        if existing_sessions and len(existing_sessions) > 0:
            st.session_state.current_session = existing_sessions[0].get("session_id")
        else:    
            sid=str(uuid.uuid4())
            MongoStore().create_session(session_id=sid, user_id="admin")
            st.session_state.current_session=sid
        
    def new_chat():
        sid=str(uuid.uuid4())
        result=st.session_state.mongodb.create_session(session_id=sid,user_id="admin")
        if result:
            st.session_state.current_session=sid
    
    def clear_chat(session_id):
        result=st.session_state.mongodb.clear_chatmessages(session_id=session_id)
    
    def get_chat_messages(session_id):
        result=st.session_state.mongodb.get_chat_history(session_id=session_id,limit=30)
        return result
    
    def save_message(message):
        try:
            st.session_state.mongodb.save_message(message=message)
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
        result=st.session_state.mongodb.get_sessions(user_id="admin",limit=20)
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
        st.session_state.selected_agent = agent_selection
        
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
                    result=st.session_state.mongodb.delete_session(session_id=ids)
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
                 "user_id":"admin"}
        
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
                
        message={"session_id":current_sessionID,
                 "role":"assistant",
                 "content":output,
                 "timestamp":datetime.utcnow().isoformat(),
                 "agent_name":st.session_state.selected_agent,
                 "user_id":"admin"}
        
        save_message(message=message)
        
        st.rerun()
streamlit_executor()
    
    
        
