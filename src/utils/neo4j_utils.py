from neo4j import GraphDatabase
import networkx as nx
from pyvis.network import Network
import streamlit as st
from datetime import datetime
import json
import ssl

class Neo4jConnection:
    def __init__(self, uri, username, password):
        try:
            # Initialize driver with secure connection
            self.driver = GraphDatabase.driver(
                uri,
                auth=(username, password),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,
                connection_timeout=30
            )
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
                
        except Exception as e:
            print(f"Error initializing Neo4j connection: {str(e)}")
            raise
        
    def close(self):
        if hasattr(self, 'driver'):
            self.driver.close()
        
    def create_chat_interaction(self, query, response, sources):
        """Create chat interaction nodes and relationships"""
        try:
            with self.driver.session() as session:
                # Create chat interaction node
                chat_id = f"chat_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Create chat node
                session.run("""
                    CREATE (c:Chat {
                        id: $chat_id,
                        query: $query,
                        response: $response,
                        timestamp: datetime()
                    })
                """, {
                    "chat_id": chat_id,
                    "query": query,
                    "response": response
                })
                
                # Create source nodes and relationships if sources exist
                if sources:
                    # Parse sources if it's a string
                    if isinstance(sources, str):
                        try:
                            sources = json.loads(sources)
                        except:
                            sources = [{"content": sources}]
                    
                    # Handle both list and single source
                    if not isinstance(sources, list):
                        sources = [sources]
                    
                    for i, source in enumerate(sources):
                        source_id = f"{chat_id}_source_{i}"
                        source_content = source.get("content", str(source))
                        
                        # Create source node
                        session.run("""
                            CREATE (s:Source {
                                id: $source_id,
                                content: $content
                            })
                        """, {
                            "source_id": source_id,
                            "content": source_content
                        })
                        
                        # Create relationship
                        session.run("""
                            MATCH (c:Chat {id: $chat_id})
                            MATCH (s:Source {id: $source_id})
                            CREATE (c)-[:REFERENCES]->(s)
                        """, {
                            "chat_id": chat_id,
                            "source_id": source_id
                        })
                
                return True
        except Exception as e:
            print(f"Error storing chat in Neo4j: {str(e)}")
            return False
            
    def get_chat_graph(self):
        """Retrieve chat interactions and sources"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Chat)-[r:REFERENCES]->(s:Source)
                    RETURN c, s
                    ORDER BY c.timestamp DESC
                    LIMIT 50
                """)
                
                chats = []
                for record in result:
                    chat = record["c"]
                    source = record["s"]
                    chats.append({
                        "chat": {
                            "id": chat["id"],
                            "query": chat["query"],
                            "response": chat["response"],
                            "timestamp": str(chat["timestamp"])
                        },
                        "source": {
                            "id": source["id"],
                            "content": source["content"]
                        }
                    })
                return chats
        except Exception as e:
            print(f"Error retrieving chat graph: {str(e)}")
            return []

def create_visualization(chat_data):
    """Create a NetworkX graph from chat data"""
    G = nx.Graph()
    
    # Add RBI Circulars central node
    G.add_node("rbi_circulars",
              label="RBI Circulars",
              title="RBI Circulars Database",
              group="rbi",
              size=40)
    
    # Add nodes and edges
    for item in chat_data:
        chat = item["chat"]
        source = item["source"]
        
        # Add chat node with more detailed information
        G.add_node(chat["id"], 
                  label=f"Q: {chat['query'][:30]}...",
                  title=f"""
                  <div style='font-family: Arial; padding: 10px;'>
                    <h3 style='color: #1f77b4;'>Query:</h3>
                    <p>{chat['query']}</p>
                    <h3 style='color: #1f77b4;'>Response:</h3>
                    <p>{chat['response']}</p>
                    <p style='color: #666; font-size: 0.8em;'>Time: {chat['timestamp']}</p>
                  </div>
                  """,
                  group="chat")
        
        # Add source node with more detailed information
        G.add_node(source["id"],
                  label=f"S: {source['content'][:30]}...",
                  title=f"""
                  <div style='font-family: Arial; padding: 10px;'>
                    <h3 style='color: #ff7f0e;'>Source:</h3>
                    <p>{source['content']}</p>
                  </div>
                  """,
                  group="source")
        
        # Add edges: RBI -> Query -> Source
        G.add_edge("rbi_circulars", chat["id"])
        G.add_edge(chat["id"], source["id"])
    
    return G

def visualize_chat_graph(chat_data):
    """Create and display an interactive visualization of the chat graph"""
    if not chat_data:
        st.info("No chat interactions to visualize yet.")
        return
        
    # Create NetworkX graph
    G = create_visualization(chat_data)
    
    # Create Pyvis network
    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # Add nodes and edges from NetworkX graph
    for node in G.nodes(data=True):
        node_id = node[0]
        node_data = node[1]
        
        # Set node colors based on group
        if node_data["group"] == "rbi":
            color = "#2ca02c"  # Green for RBI node
            size = 40
        elif node_data["group"] == "chat":
            color = "#1f77b4"  # Blue for chat nodes
            size = 25
        else:
            color = "#ff7f0e"  # Orange for source nodes
            size = 20
        
        net.add_node(node_id,
                    label=node_data["label"],
                    title=node_data["title"],
                    color=color,
                    size=size)
    
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Set physics layout and interaction options
    net.set_options("""
    {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -100,
                "centralGravity": 0.1,
                "springLength": 200,
                "springConstant": 0.1
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
                "enabled": true,
                "iterations": 1000
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "hideEdgesOnDrag": true,
            "navigationButtons": true
        },
        "nodes": {
            "font": {
                "size": 14,
                "face": "Arial",
                "strokeWidth": 2,
                "strokeColor": "#ffffff"
            },
            "shape": "dot",
            "borderWidth": 2,
            "shadow": true
        },
        "edges": {
            "width": 2,
            "shadow": true,
            "smooth": {
                "type": "continuous",
                "forceDirection": "none"
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            }
        }
    }
    """)
    
    # Save and display the graph
    net.save_graph("chat_graph.html")
    with open("chat_graph.html", "r", encoding="utf-8") as f:
        html = f.read()
    st.components.v1.html(html, height=600, scrolling=True) 