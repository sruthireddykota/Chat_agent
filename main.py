import streamlit as st
import uuid
import bcrypt
from PIL import Image

chatbot_icon=Image.open("assets/robot.png")
knowledge_icon = Image.open("assets/learning-support.png")
metrics_icon = Image.open("assets/metrics.png")

st.set_page_config(
    page_title="Multi Agent Chatbot",
    page_icon=chatbot_icon,
    layout="wide",
    initial_sidebar_state="collapsed"
    )

if "mongodb" not in st.session_state:
    from Mongodb.mongodb_server import MongoStore
    st.session_state.mongodb=MongoStore()
    
if "authenticated" not in st.session_state:
    st.session_state.authenticated='home'

if "user_id" not in st.session_state:
    st.session_state.user_id=None
    
if st.session_state.authenticated=='home':
    
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            
            # /* Sidebar background color */
            # [data-testid="stSidebar"] {
            #     background-color: #0E1117;
            # }
        </style>
        """,
        unsafe_allow_html=True
    )

        
    def user_signup(user_data):
        response=st.session_state.mongodb.create_user(user_data)
        return response

    def user_login(email_id,password):
        response=st.session_state.mongodb.get_user_details(email_id=email_id)
        if response.get("logged_in"):
            st.write("User already Logged In")
        else :
            password_bytes = password.encode('utf-8')
            
            if bcrypt.checkpw(password_bytes, response.get("password")):
                user_id=response.get("user_id")
                st.session_state.user_id=user_id
                st.session_state.mongodb.update_user_status(user_id,True)
                st.success("Logged In successfully")
                return True
            else:
                st.error("Incorrect Password")
                return False
                    
                    
    @st.dialog("Sign Up")
    def signup():
        with st.empty().container(border=True):
            username=st.text_input("User Name",key="signup_username")
            password=st.text_input("Password",type='password',key="signup_password")
            email=st.text_input("Email",key="signup_email")
            
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt)
            
            data={
                "username":username,
                "user_id":str(uuid.uuid4()),
                "password":hashed_password,
                "email_id":email,
                "logged_in":False,
                "last_logged_in":None
            }
            
            if st.button("Sign Up",key="signup_button"):
                if len(username)<=6:
                    st.error("Username should be greater than 6 Characters")
                elif len(password)<=8:
                    st.error("password should be greater than 8 Characters")
                elif len(email)<=10:
                    st.error("Email ID should be greater than 10 Characters")
                else:
                    response=user_signup(data)
                    if response.get("status")=="success":
                        st.success("Sign Up Successful")
                    else:
                        st.error(response.get("message"))
            
                            
    with st.empty().container(border=True):
        col1,col2 = st.columns([5,5])
        with col1:
            st.image("assets/login_page_logo.png")
        with col2:
            st.header("Multi Agent Chatbot",text_alignment="center")
            st.write("")
            email_id=st.text_input("Email ID",key="user_name")
            password=st.text_input("Password",type='password',key="User_password")
            _,login_col1,signup_col2=st.columns([1,2,2])
            with login_col1:
                login=st.button("Log in",key='user_login')
                if login:
                    if len(email_id)<=10 :
                        st.error("Email ID Should be greater than 10 Characters")
                    
                    elif len(password)<=8:
                        st.error("Password Should be greater than 8 Characters")
                    else:
                        response=user_login(email_id=email_id,password=password)
                        if response:
                            st.session_state.authenticated='landing'
                            st.rerun()
                                             
            with signup_col2:
                signup=st.button("Sign Up",key="user_signup_button",on_click=signup)
                
    
elif st.session_state.authenticated=='landing':
    def user_logout():
        try:
            st.session_state.mongodb.update_user_status(user_id=st.session_state.user_id,logged_in=False)
            st.session_state.authenticated='home'
            st.session_state.user_id=None
            st.rerun()
        except Exception as e:
            st.error("Log out failed")

    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] { display: none; }
            .login-container {
                max-width: 900px;
                margin: 0 auto;
                padding: 1rem 2rem;
                border-radius: 8px;
            }
            .login-left { text-align: center; }
        </style>
        """,
        unsafe_allow_html=True
    )
            
    st.title(":blue[Dashboard]",text_alignment="center",anchor=False)
    with st.sidebar:
        logout=st.button(":orange[Log Out]",key="logout_button")
        if logout:
            user_logout()
            
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.image(chatbot_icon, use_container_width=True)
            st.write("Interact with our intelligent multi-agent chatbot system")
            st.write("")
            if st.button("Launch Chatbot", key="launch_chatbot", use_container_width=True, type="primary"):
                st.switch_page("pages/chatbot.py")
        
    with col2:
        with st.container(border=True):
            st.image(knowledge_icon, use_container_width=True)
            st.write("Manage and organize your knowledge base")
            st.write("")
            if st.button("Launch Knowledge Management", key="launch_km", use_container_width=True, type="primary"):
                st.switch_page("pages/knowledge_management.py")

    with col3:
        with st.container(border=True):
            st.image(metrics_icon, use_container_width=True)
            st.write("Evaluate your RAG pipeline performance")
            st.write("")
            if st.button("Launch RAG Evaluation", key="launch_rag", use_container_width=True, type="primary"):
                st.switch_page("pages/rag_evaluation.py")

            
        
        
    
            
            
    
