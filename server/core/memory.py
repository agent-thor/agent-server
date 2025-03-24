from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
from ..utils.db_utils import DynamoDBClient
from dotenv import load_dotenv
import os
load_dotenv()
dyno= DynamoDBClient()
embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
DYNAMO_TABLE_NAME = "agent_tool_id"


# Function to chat and fetch relevant past interactions
def retrieve_relevant(user_input,dyno_list):
    vectorstore = FAISS.from_documents([Document(page_content="hello")], embedding_model)
    for dl in dyno_list:
        vectorstore.add_documents([Document(page_content=dl)])
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    retrieved_docs = retriever.get_relevant_documents(user_input)
    retrieved_text = "\n\n\n".join([doc.page_content for doc in retrieved_docs])
    
    return retrieved_text


if __name__=="__main__":
    pass
