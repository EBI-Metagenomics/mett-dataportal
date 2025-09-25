import pandas as pd
import numpy as np
import re
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
from adjustText import adjust_text

def load_gff_annotation(gff_path):
    """Load GFF file and extract relevant information."""
    gff_df = pd.read_csv(gff_path, sep='\t', comment='#', header=None,
                        names=['seqid', 'source', 'type', 'start', 'end', 'score', 'strand', 'phase', 'attributes'])
    # from GFF, get uniprot to gene mapping
    gff_df = gff_df[gff_df['type'] == 'gene']
    gff_df['gene_id'] = gff_df['attributes'].apply(lambda x: re.search(r'ID=(\S+?);', x).group(1))
    gff_df['locus_tag'] = gff_df['attributes'].apply(lambda x: re.search(r'locus_tag=(\S+?);', x).group(1) if re.search(r'locus_tag=(\S+?);', x) else None)
    gff_df['uniprot_id'] = gff_df['attributes'].apply(lambda x: re.search(r'UniProt:(\S+?);', x).group(1) if re.search(r'UniProt:(\S+?);', x) else None)
    gff_df['name'] = gff_df['attributes'].apply(lambda x: re.search(r'product=([^;]*);', x).group(1) if re.search(r'product=([^;]*);', x) else None)
    gff_df = gff_df[['gene_id', 'locus_tag', 'uniprot_id', 'name']].drop_duplicates()
    return gff_df

def load_interactions(interactions_path, gff_df):
    """Load interactions data."""
    interactions_df = pd.read_csv(interactions_path)

    int_cols = [
        'ds_score', 'tt_score',
        'perturb_score', 'gp_score', 'melt_score', 'sec_score', 'bn_score',
        'string_physical_score', 'operon_score', 'ecocyc_score',
        'xlms_peptides']

    # keep only rows where both protein_a and protein_b are in gff_df uniprot and at least one int_col > 0.5
    filt_df = interactions_df[
        (interactions_df['protein_a'].isin(gff_df['uniprot_id'])) &
        (interactions_df['protein_b'].isin(gff_df['uniprot_id'])) &
        (interactions_df[int_cols].max(axis=1) > 0.5)
    ].copy()
    return filt_df

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
    fig, ax = plt.subplots(figsize=(8, 6))
    nx.draw_networkx_nodes(G, pos=pos, ax=ax, node_size=500)
    nx.draw_networkx_edges(
        G,
        pos=pos,
        ax=ax,
        width=[d['weight'] * 2 for (_, _, d) in G.edges(data=True)]
    )
    label_artists = nx.draw_networkx_labels(G, pos=pos, ax=ax, font_size=8)

    texts = list(label_artists.values())
    if texts:
        adjust_text(
            texts,
            ax=ax,
            expand_text=(1.1, 1.1),
            expand_points=(1.1, 1.1),
            arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)
        )

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