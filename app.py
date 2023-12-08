import os
from flask_cors import CORS
from flask import Flask, render_template, request, jsonify,send_file
from ingestion.ingest import (load_single_document,load_document_batch,load_documents,split_documents)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma,FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.chains import RetrievalQA,LLMChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from constants import (
    PERSIST_DIRECTORY,
    SOURCE_DIRECTORY,
)
import logging

logger = logging.getLogger(__name__)


app = Flask(__name__)

UPLOAD_FOLDER = SOURCE_DIRECTORY
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'md','ppt','pptx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app, support_credentials=True)
app.config['CORS_HEADERS'] = 'application/json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def document_to_dict(document):
    return {
        "page_content": document.page_content,
        "metadata": document.metadata
    }

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(SOURCE_DIRECTORY, filename)
        file.save(file_path)
        return jsonify({"message": "Your file is uploaded successfully"}), 201
    else:
        return jsonify({"error": "Invalid file format"}), 400



@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({"error": "Question not provided"}), 400
        
        documents = load_documents("source_documents")
        # if documents.length ==0:
        #     return jsonify({"message":"HII"})
        text_documents, python_documents = split_documents(documents)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=1000, chunk_overlap=200
        )
        texts = text_splitter.split_documents(text_documents)
        texts.extend(python_splitter.split_documents(python_documents))
        # if texts.length ==0:
        #     return jsonify({"message":"Unabl to extract text"})
        embedding=OpenAIEmbeddings(openai_api_key="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")

        vectordb = Chroma.from_documents(texts, embedding)
        retriever=vectordb.as_retriever()
        assistant_prompt_template = """
            # Chat roles
            SYSTEM = "system"
            USER = "user"
            ASSISTANT = "assistant"
 
            # Introduction
            system_message_chat_conversation = "Welcome! You are interacting with a knowledgeable assistant. This assistant will provide answers to questions based on the provided data sources. It strives to provide factual information, cite sources, and is interactive. Please feel free to ask any questions."
 
            # System Role
            system_chat_prompt = "You are an AI assistant equipped with information from various data sources. Your task is to answer questions based on the data provided by the user. Please ensure your responses are factual and cite the source. If you cannot provide an answer, respond with 'I don't know.If asking a clarifying question to the user would help, ask the question.'"
 
            # User Role
            user_prompt =\
                USER = "user"+\
                "You are a user seeking information from the AI assistant. Below is the history of our conversation and a new question. Please follow these steps before providing an answer:"+\
                "1. Greet the user and establish context."+\
                "2. Fully understand the user's question before responding. If the question is unclear, request clarification."+\
                "3.If the question is not in English, translate the question to English before generating the search."+\
                "4.For tabular information return it as an html table. Do not return markdown format. "  + \
                "5.All questions must be answered from the results from search or look up actions, only facts resulting from those can be used in an answer. "+\
                "6.Answer questions as truthfully as possible, and ONLY answer the questions using the information from observations, do not speculate or your own knowledge."+\
                "7.Don't provide different answers for the same question"+\
                "8.Conclusion:Conclude the conversation and offer further assistance."
           
                {context}
                #sample question would be like
                USER : 'What is the leave policy of DCSPL'
                ASSISTANT : "Here are multiple possible answers based on the provided content: [List of Answers with Citations]"
 
                # Additional user and assistant exchanges here.
 
                # Question: {question}
 
            # Assistant Conversation Template
            assistant_conversation_template = "ASSISTANT = 'assistant'\n"
 
            # AI Role
            ai_prompt =\
                AI = "ai"+\
                "You are an AI model trained to assist with accounting-related questions based on the provided content and have multilingual capabilities also. Your primary role is to generate multiple factual answers to the user's questions and cite the source of the information. After generating answers, you will ask the user to specify which answer they would like to explore in detail. Remember to consider the conversation history."+\
                "Example Scenario: The user has asked for the likelihood of a project with Amber status turning Red."+\
                "If multiple citations are found for the question, generate a single answer with citations and provide a meaningful result."+\
                "Generate single answers with citations if multiple citations are found for the question and do the same."+\
                "If the question is not in English, translate the question to English before generating the search"+\
                "Provide meaningful and concise answers with citations based on the context and available data."+\
                "You need to undesratnd the user question then only you need to answer the question, if you don't understand the question then ask the user to elaborate the question"
 
            # Prompt Template
            template =\
                'Use the following context to answer the question. If the question contains "hello," say "hi" and address yourself as Jarvis.'" If you find the question is incomplete, respond like an assistant and use the conversation history to answer if necessary. If you don't know the answer, respond with 'I don't know.' Do not merge different document data; ask every time about which data the person needs."+\
 
            {context}
 
            {history}
            Question: {question}
            Helpful Answer:
        """
        prompt=PromptTemplate(input_variables=["question","context","history"],template=assistant_prompt_template)
        # Initialize Conversation Memory
        memory = ConversationBufferMemory(input_key="question", memory_key="history")
        print("hii")

        qa = RetrievalQA.from_chain_type(OpenAI(openai_api_key="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"),retriever=retriever,chain_type="stuff", return_source_documents=True, chain_type_kwargs={"prompt": prompt, "memory": memory})
        # Sample text data for embedding (you need to modify this)
        re=qa(question)
        print(re)
        query = re.get('query', 'No query found')
        result = re.get('result', 'No result found')
        source_documents = [document_to_dict(doc) for doc in re.get('source_documents', [])]
        response_data = {
            "query": query,
            "result": result,
            "source_documents": source_documents
        }
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}")
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=80)

