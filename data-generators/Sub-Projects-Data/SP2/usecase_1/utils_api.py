import pandas as pd
import numpy as np
import requests
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
from adjustText import adjust_text
from typing import Dict, List, Optional, Tuple

# Set matplotlib style for better readability
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['savefig.facecolor'] = 'white'

# API Configuration
API_BASE_URL = "http://localhost:8000/api"  

class PPIDataAPI:
    """API client for PPI data operations."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the API endpoint."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            raise
    
    def get_interactions(self, species_acronym: str = "PV", 
                        score_type: str = None, 
                        score_threshold: float = None,
                        page: int = 1, 
                        per_page: int = 1000) -> pd.DataFrame:
        """Get PPI interactions from the API."""
        params = {
            "species_acronym": species_acronym,
            "page": page,
            "per_page": per_page
        }
        
        if score_type and score_threshold is not None:
            params["score_type"] = score_type
            params["score_threshold"] = score_threshold
        
        response = self._make_request("/ppi/interactions", params)
        
        # Convert to DataFrame
        interactions = []
        for item in response["data"]:
            interactions.append({
                "protein_a": item["protein_a"],
                "protein_b": item["protein_b"],
                "ds_score": item.get("ds_score"),
                "tt_score": item.get("tt_score"),
                "perturb_score": item.get("perturbation_score"),
                "gp_score": item.get("abundance_score"),
                "melt_score": item.get("melt_score"),
                "sec_score": item.get("secondary_score"),
                "bn_score": item.get("bayesian_score"),
                "string_physical_score": item.get("string_score"),
                "operon_score": item.get("operon_score"),
                "ecocyc_score": item.get("ecocyc_score"),
                "xlms_peptides": item.get("xlms_peptides"),
                # Gene information for protein_a
                "protein_a_locus_tag": item.get("protein_a_locus_tag"),
                "protein_a_uniprot_id": item.get("protein_a_uniprot_id"),
                "protein_a_name": item.get("protein_a_name"),
                "protein_a_product": item.get("protein_a_product"),
                # Gene information for protein_b
                "protein_b_locus_tag": item.get("protein_b_locus_tag"),
                "protein_b_uniprot_id": item.get("protein_b_uniprot_id"),
                "protein_b_name": item.get("protein_b_name"),
                "protein_b_product": item.get("protein_b_product"),
            })
        
        return pd.DataFrame(interactions)
    
    def get_gene_annotations(self, species_acronym: str = "PV") -> pd.DataFrame:
        """Get gene annotations from PPI data."""
        # Get all interactions to extract unique gene information
        interactions_df = self.get_interactions(species_acronym=species_acronym, per_page=10000)
        
        # Debug: Check what columns are available in interactions_df
        print(f"Available columns in interactions_df: {interactions_df.columns.tolist()}")
        print(f"Shape of interactions_df: {interactions_df.shape}")
        
        # Extract unique gene information
        genes_a = interactions_df[["protein_a", "protein_a_locus_tag", "protein_a_uniprot_id", 
                                  "protein_a_name", "protein_a_product"]].copy()
        print(f"genes_a columns before rename: {genes_a.columns.tolist()}")
        print(f"genes_a shape: {genes_a.shape}")
        genes_a.columns = ["uniprot_id", "locus_tag", "uniprot_id_alt", "name", "product"]
        
        genes_b = interactions_df[["protein_b", "protein_b_locus_tag", "protein_b_uniprot_id", 
                                  "protein_b_name", "protein_b_product"]].copy()
        print(f"genes_b columns before rename: {genes_b.columns.tolist()}")
        print(f"genes_b shape: {genes_b.shape}")
        genes_b.columns = ["uniprot_id", "locus_tag", "uniprot_id_alt", "name", "product"]
        
        # Combine and deduplicate
        all_genes = pd.concat([genes_a, genes_b], ignore_index=True).drop_duplicates(subset=["uniprot_id"])
        
        # Debug: Check if there are duplicate column names
        if not all_genes.columns.is_unique:
            print(f"Warning: Duplicate column names detected: {all_genes.columns.tolist()}")
            # Remove duplicate columns by keeping only the first occurrence
            all_genes = all_genes.loc[:, ~all_genes.columns.duplicated()]
        
        # Debug: Check the structure of all_genes before adding gene_id
        print(f"all_genes columns: {all_genes.columns.tolist()}")
        print(f"all_genes shape: {all_genes.shape}")
        print(f"uniprot_id column type: {type(all_genes['uniprot_id'])}")
        if hasattr(all_genes['uniprot_id'], 'shape'):
            print(f"uniprot_id shape: {all_genes['uniprot_id'].shape}")
        
        # Add gene_id (using uniprot_id as gene_id for now)
        all_genes["gene_id"] = all_genes["uniprot_id"]
        
        return all_genes[["gene_id", "locus_tag", "uniprot_id", "name", "product"]]
    
    def get_network_properties(self, score_type: str, score_threshold: float, 
                             species_acronym: str = "PV") -> Dict:
        """Get network properties from the API."""
        params = {
            "score_type": score_type,
            "score_threshold": score_threshold,
            "species_acronym": species_acronym
        }
        
        response = self._make_request("/ppi/network-properties", params)
        return response["data"]
    
    def get_network_data(self, score_type: str, score_threshold: float, 
                        species_acronym: str = "PV") -> Tuple[List, List]:
        """Get network data (nodes and edges) from the API."""
        params = {
            "score_type": score_type,
            "score_threshold": score_threshold,
            "species_acronym": species_acronym
        }
        
        response = self._make_request("/ppi/network", params)
        network_data = response["data"]
        
        return network_data["nodes"], network_data["edges"]
    
    def search_interactions(self, params: Dict) -> List[Dict]:
        """Search for PPI interactions with various filtering options."""
        response = self._make_request("/ppi/interactions", params)
        return response["results"]

    def get_protein_interactions(self, protein_id: str, species_acronym: str = "PV") -> List[Dict]:
        """Get all interactions for a protein from the API."""
        params = {
            "species_acronym": species_acronym,
            "per_page": 10000
        }
        
        response = self._make_request(f"/ppi/interactions/{protein_id}", params)
        return response["data"]

    def get_protein_neighborhood(self, protein_id: str, n: int = 5, 
                               species_acronym: str = "PV") -> Dict:
        """Get protein neighborhood from the API."""
        params = {
            "n": n,
            "species_acronym": species_acronym
        }
        
        response = self._make_request(f"/ppi/neighborhood/{protein_id}", params)
        return response["data"]


# Initialize API client
ppi_api = PPIDataAPI()

def load_gff_annotation(species_acronym: str = "PV"):
    """Load gene annotations from API instead of GFF file."""
    return ppi_api.get_gene_annotations(species_acronym)


def load_interactions(species_acronym: str = "PV", score_filter: str = None, 
                     score_threshold: float = 0.5):
    """Load interactions data from API instead of CSV file."""
    interactions_df = ppi_api.get_interactions(species_acronym=species_acronym, per_page=10000)
    
    # Apply score filtering if specified
    if score_filter and score_threshold is not None:
        score_col = f"{score_filter}_score"
        if score_col in interactions_df.columns:
            interactions_df = interactions_df[interactions_df[score_col] >= score_threshold]
    
    return interactions_df


def interaction_network_from_df(interactions_df, score_col='ds_score', score_threshold=0.8):
    """Create a NetworkX graph from interactions DataFrame after filtering by score threshold."""
    filt_df = interactions_df[interactions_df[score_col] >= score_threshold]
    filt_df = filt_df[['protein_a', 'protein_b', score_col]].dropna().rename(columns={score_col: 'weight'})
    G = nx.from_pandas_edgelist(filt_df, 'protein_a', 'protein_b', edge_attr='weight')
    return G


def plot_network_properties(G):
    """Plot various network properties."""
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = nx.density(G)
    avg_clustering = nx.average_clustering(G)

    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")
    print(f"Density: {density:.4f}")
    print(f"Average clustering coefficient: {avg_clustering:.4f}")

    degrees = [d for n, d in G.degree()]
    plt.figure(figsize=(10, 6))
    sns.histplot(degrees, bins=30, kde=True)
    plt.title('Degree Distribution')
    plt.xlabel('Degree')
    plt.ylabel('Frequency')
    plt.show()


def plot_network(G):
    """General network plotting function with label collision avoidance."""
    pos = nx.spring_layout(G, seed=42)
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='white')
    
    # Set background to white
    ax.set_facecolor('white')
    
    # Draw nodes with blue color and white text
    nx.draw_networkx_nodes(
        G, 
        pos=pos, 
        ax=ax, 
        node_size=500,
        node_color='lightblue',
        edgecolors='black',
        linewidths=1
    )
    
    # Draw edges with simple black lines
    nx.draw_networkx_edges(
        G,
        pos=pos,
        ax=ax,
        width=1.0,  # Fixed width instead of variable
        edge_color='black',
        alpha=1.0,  # No transparency
        style='solid'  # Solid lines
    )
    
    # Draw labels with black text (smaller font for longer labels)
    label_artists = nx.draw_networkx_labels(
        G, 
        pos=pos, 
        ax=ax,
        font_size=6,  # Smaller font for multi-line labels
        font_color='black',
        font_weight='bold',
        verticalalignment='center',
        horizontalalignment='center'
    )

    # Simple text positioning without adjust_text to avoid shaded areas
    # texts = list(label_artists.values())
    # if texts:
    #     adjust_text(
    #         texts,
    #         ax=ax,
    #         expand_text=(1.1, 1.1),
    #         expand_points=(1.1, 1.1),
    #         arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)
    #     )

    ax.set_axis_off()
    plt.tight_layout()
    return fig, ax


def plot_neighborhood(G, node, n=5, gff_df=None):
    """Plot the ego network for `node` with label collision avoidance."""
    distances = nx.single_source_dijkstra_path_length(G, node, weight='weight')
    nearest_neighbors = sorted(distances, key=distances.get)[1:n + 1]
    subgraph = G.subgraph([node] + nearest_neighbors)

    if gff_df is not None:
        uniprot_to_gene = gff_df.set_index('uniprot_id')['gene_id'].to_dict()
        uniprot_to_name = gff_df.set_index('uniprot_id')['name'].to_dict()
        mapping = {n: f"{uniprot_to_gene.get(n, n)}\n{uniprot_to_name.get(n, '')}" for n in subgraph.nodes()}
        subgraph = nx.relabel_nodes(subgraph, mapping)

    fig, ax = plot_network(subgraph)
    plt.title(f'Neighborhood of {mapping.get(node, node)}', fontsize=14)
    plt.show()


def plot_connected_hits(G, nodes, gff_df=None):
    """Plot subgraph induced by a set of nodes with label collision avoidance."""
    subg = G.subgraph(nodes)
    # remove disconnected nodes
    subg = subg.subgraph([n for n in subg.nodes() if subg.degree(n) > 0])

    if gff_df is not None:
        uniprot_to_gene = gff_df.set_index('uniprot_id')['gene_id'].to_dict()
        uniprot_to_name = gff_df.set_index('uniprot_id')['name'].to_dict()
        mapping = {n: f"{uniprot_to_gene.get(n, n)}\n{uniprot_to_name.get(n, '')}" for n in subg.nodes()}
        subg = nx.relabel_nodes(subg, mapping)

    fig, ax = plot_network(subg)
    plt.title('Subgraph of Hit nodes', fontsize=14)
    plt.show()


def get_node_with_highest_clustering_coefficient(G):
    """Retrieve the node with the highest clustering coefficient."""
    clustering_coeffs = nx.clustering(G)
    top_cc_node = max(clustering_coeffs, key=clustering_coeffs.get)
    return top_cc_node


def get_available_proteins(species_acronym: str = "PV", limit: int = 20):
    """Get a list of available proteins from the API data."""
    try:
        interactions_df = load_interactions(species_acronym)
        all_proteins = set(interactions_df['protein_a'].unique()) | set(interactions_df['protein_b'].unique())
        return list(all_proteins)[:limit]
    except Exception as e:
        print(f"Error getting available proteins: {e}")
        return []


def plot_network_properties_from_api(score_type: str, score_threshold: float, 
                                   species_acronym: str = "PV"):
    """Plot network properties using API data."""
    try:
        properties = ppi_api.get_network_properties(score_type, score_threshold, species_acronym)
        
        print(f"Number of nodes: {properties['num_nodes']}")
        print(f"Number of edges: {properties['num_edges']}")
        print(f"Density: {properties['density']:.4f}")
        print(f"Average clustering coefficient: {properties['avg_clustering_coefficient']:.4f}")

        degrees = properties['degree_distribution']
        plt.figure(figsize=(10, 6))
        sns.histplot(degrees, bins=30, kde=True)
        plt.title('Degree Distribution')
        plt.xlabel('Degree')
        plt.ylabel('Frequency')
        plt.show()
        
    except Exception as e:
        print(f"Error getting network properties from API: {e}")
        # Fallback to local calculation
        interactions_df = load_interactions(species_acronym)
        G = interaction_network_from_df(interactions_df, score_type, score_threshold)
        plot_network_properties(G)


def plot_neighborhood_from_api(protein_id: str, n: int = 5, species_acronym: str = "PV"):
    """Plot protein neighborhood using the same approach as old implementation."""
    try:
        # Build complete graph from all interactions (like old implementation)
        interactions_df = load_interactions(species_acronym)
        print(f"Loaded {len(interactions_df)} interactions from API")
        
        G = interaction_network_from_df(interactions_df, score_col='ds_score', score_threshold=0.1)
        print(f"Built complete graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Check if protein exists in the graph
        if protein_id not in G:
            print(f"Protein {protein_id} not found in the complete graph")
            print(f"Available proteins: {list(G.nodes())[:10]}...")
            return
        
        # Use Dijkstra's algorithm to find nearest neighbors (exactly like old implementation)
        distances = nx.single_source_dijkstra_path_length(G, protein_id, weight='weight')
        nearest_neighbors = sorted(distances, key=distances.get)[1:n + 1]
        
        # Create neighborhood subgraph exactly like old implementation
        neighborhood_nodes = [protein_id] + nearest_neighbors
        subgraph = G.subgraph(neighborhood_nodes)
        
        print(f"Neighborhood subgraph has {subgraph.number_of_nodes()} nodes and {subgraph.number_of_edges()} edges")
        print(f"Neighborhood nodes: {neighborhood_nodes}")
        
        # Check if we have dense connections (neighbors connected to each other)
        neighbor_connections = 0
        for neighbor in nearest_neighbors:
            for other_neighbor in nearest_neighbors:
                if neighbor != other_neighbor and subgraph.has_edge(neighbor, other_neighbor):
                    neighbor_connections += 1
        
        print(f"Connections between neighbors: {neighbor_connections}")
        if neighbor_connections == 0:
            print("Note: Neighbors are not connected to each other - this creates a star-like structure")
            print("This might be because neighbors don't interact directly in the available data")
        
        # Get gene annotations (like old implementation)
        gff_df = load_gff_annotation(species_acronym)
        
        # Create node mapping exactly like old implementation
        if gff_df is not None:
            uniprot_to_gene = gff_df.set_index('uniprot_id')['gene_id'].to_dict()
            uniprot_to_name = gff_df.set_index('uniprot_id')['name'].to_dict()
            uniprot_to_locus = gff_df.set_index('uniprot_id')['locus_tag'].to_dict()
            
            # Format: "protein_id\nlocus_tag\nproduct" (matching user's request)
            mapping = {}
            for n in subgraph.nodes():
                locus_tag = uniprot_to_locus.get(n, n)
                product = uniprot_to_name.get(n, '')
                if locus_tag and product:
                    mapping[n] = f"{n}\n{locus_tag}\n{product}"
                elif locus_tag:
                    mapping[n] = f"{n}\n{locus_tag}"
                else:
                    mapping[n] = n
        else:
            mapping = {n: n for n in subgraph.nodes()}
        
        subgraph = nx.relabel_nodes(subgraph, mapping)
        
        # Plot using the same function as old implementation
        fig, ax = plot_network(subgraph)
        plt.title(f'Neighborhood of {mapping.get(protein_id, protein_id)}', fontsize=14)
        plt.show()
        
    except Exception as e:
        print(f"Error getting neighborhood from API: {e}")
        print("Falling back to local calculation...")
        try:
            # Fallback to local calculation
            interactions_df = load_interactions(species_acronym)
            G = interaction_network_from_df(interactions_df)
            
            # Check if protein exists in the graph
            if protein_id not in G:
                print(f"Protein {protein_id} not found in local data. Available proteins: {list(G.nodes())[:10]}...")
                return
            
            plot_neighborhood(G, protein_id, n)
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            print("Please check if the protein ID exists in the data.")
