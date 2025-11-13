import os
from dotenv import load_dotenv
from getpass import getpass
from camel.storages import Neo4jGraph

# Load environment variables from .env file
load_dotenv()
from camel.agents import KnowledgeGraphAgent
from camel.loaders import UnstructuredIO
from dataloader import load_high
import argparse
# Import data_chunk only when needed (not in simple mode)
try:
    from data_chunk import run_chunk
except ImportError:
    run_chunk = None
try:
    from creat_graph import creat_metagraph
except ImportError:
    creat_metagraph = None
from summerize import process_chunks
try:
    from retrieve import seq_ret
except ImportError:
    seq_ret = None
from utils import *
from nano_graphrag import GraphRAG, QueryParam

# %% set up parser
parser = argparse.ArgumentParser()
parser.add_argument('-simple', action='store_true')
parser.add_argument('-construct_graph', action='store_true')
parser.add_argument('-inference',  action='store_true')
parser.add_argument('-grained_chunk',  action='store_true')
parser.add_argument('-trinity', action='store_true')
parser.add_argument('-trinity_gid1', type=str)
parser.add_argument('-trinity_gid2', type=str)
parser.add_argument('-ingraphmerge',  action='store_true')
parser.add_argument('-crossgraphmerge', action='store_true')
parser.add_argument('-dataset', type=str, default='mimic_ex')
parser.add_argument('-data_path', type=str, default='./dataset_test')
parser.add_argument('-test_data_path', type=str, default='./dataset_ex/report_0.txt')
args = parser.parse_args()

if args.simple:
    from nano_graphrag._storage_numpy import NumpyVectorStorage
    from nano_graphrag._llm import gpt_4o_mini_complete
    graph_func = GraphRAG(
        working_dir="./nanotest",
        vector_db_storage_cls=NumpyVectorStorage,  # Use NumPy storage for Windows compatibility
        best_model_func=gpt_4o_mini_complete,  # Use Gemini Flash for higher rate limits (15 RPM vs 2 RPM)
        cheap_model_func=gpt_4o_mini_complete,  # Use Gemini Flash for all operations
        best_model_max_async=2,  # Limit concurrent requests to stay within rate limits
        cheap_model_max_async=2,
        enable_local=False  # Disable local mode to avoid embedding API quota issues
    )

    with open("./dataset/mimic_ex/dataset/report_0.txt") as f:
        graph_func.insert(f.read())

    # Perform global graphrag search (local mode disabled due to embedding quota)
    print(graph_func.query("What cardiac procedures or treatments were performed?", param=QueryParam(mode="global")))

else:

    url=os.getenv("NEO4J_URL")
    username=os.getenv("NEO4J_USERNAME")
    password=os.getenv("NEO4J_PASSWORD")

    # Set Neo4j instance
    n4j = Neo4jGraph(
        url=url,
        username=username,             # Default username
        password=password     # Replace 'yourpassword' with your actual password
    )

    if args.construct_graph: 
        if args.dataset == 'mimic_ex':
            files = [file for file in os.listdir(args.data_path) if os.path.isfile(os.path.join(args.data_path, file))]
            
            # Read and print the contents of each file
            for file_name in files:
                file_path = os.path.join(args.data_path, file_name)
                content = load_high(file_path)
                gid = str_uuid()
                n4j = creat_metagraph(args, content, gid, n4j)

                if args.trinity:
                    link_context(n4j, args.trinity_gid1)
            if args.crossgraphmerge:
                merge_similar_nodes(n4j, None)

    if args.inference:
        question = load_high("./prompt.txt")
        sum = process_chunks(question)
        gid = seq_ret(n4j, sum)
        response = get_response(n4j, gid, question)
        print(response)
