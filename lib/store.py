import dotenv
from langchain_chroma import Chroma
from langchain_voyageai import VoyageAIEmbeddings

dotenv.load_dotenv()

embeddings = VoyageAIEmbeddings(model="voyage-4-lite")
vectorstore = Chroma(persist_directory="vectorstore", collection_name="about", embedding_function=embeddings)