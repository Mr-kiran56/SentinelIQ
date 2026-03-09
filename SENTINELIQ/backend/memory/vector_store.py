import os
os.environ['OPENAI_API_KEY'] = ""
## Import some libraries
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import TextLoader
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

## Load data
loader = DirectoryLoader("/content/new_articles/", glob = "./*.txt", loader_cls= TextLoader)
document = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
text = text_splitter.split_documents(document)
persist_directory = 'db'
embedding = NVIDIAEmbeddings()
vectordb = Chroma.from_documents(documents=text,
                                 embedding=embedding,
                                 persist_directory=persist_directory)
# persiste the db to disk
vectordb.persist()
vectordb = None
# Now we can load the persisted database from disk, and use it as normal.
vectordb = Chroma(persist_directory=persist_directory,
                  embedding_function=embedding)

## Make a retriever

retriever = vectordb.as_retriever()

docs = retriever.get_relevant_documents("How much money did Microsoft raise?")

len(docs)

docs

retriever = vectordb.as_retriever(search_kwargs={"k": 2})

retriever.search_type

retriever.search_kwargs

## Make a chain



llm=OpenAI()

# create the chain to answer questions
qa_chain = RetrievalQA.from_chain_type(llm=OpenAI(),
                                  chain_type="stuff",
                                  retriever=retriever,
                                  return_source_documents=True)
## Cite sources
def process_llm_response(llm_response):
    print(llm_response['result'])
    print('\n\nSources:')
    for source in llm_response["source_documents"]:
        print(source.metadata['source'])
# full example
query = "How much money did Microsoft raise?"
llm_response = qa_chain(query)
process_llm_response(llm_response)
# break it down
query = "What is the news about Pando?"
llm_response = qa_chain(query)
process_llm_response(llm_response)
# ## Deleteing the DB
# # To cleanup, you can delete the collection
vectordb.delete_collection()
vectordb.persist()



