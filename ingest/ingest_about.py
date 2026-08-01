from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import MarkdownTextSplitter
from langchain_voyageai import VoyageAIEmbeddings
from langchain_chroma import Chroma
import dotenv

dotenv.load_dotenv()

docs = DirectoryLoader("data/markdown", glob="**/*.md").load()
chunks = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=200).split_documents(docs)

embeddings = VoyageAIEmbeddings(model="voyage-4-lite")
db = Chroma.from_documents(chunks, embeddings, persist_directory="vectorstore", collection_name="about")

print(f"Added {db._collection.count()} chunks")