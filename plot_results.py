import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_research_graphs(csv_file="real_network_data.csv"):
    print(f"Loading research data from {csv_file}...")
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: {csv_file} not found. Run generate_dataset.py first.")
        return

    # Set publication-style aesthetics (IEEE standard)
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    
    print("Generating Graph 1: Throughput vs Load...")
    plt.figure(figsize=(10, 6))
    # Seaborn's lineplot automatically aggregates our 3 random seeds and plots a 95% Confidence Interval shadow
    sns.lineplot(data=df, x='arrival_rate', y='throughput_value', hue='protocol_name', marker='o', errorbar=('ci', 95))
    plt.title('System Throughput vs. Traffic Load (95% CI)', fontsize=14, fontweight='bold')
    plt.xlabel('Arrival Rate (Packets/sec/Node)', fontsize=12)
    plt.ylabel('Throughput (Successful Deliveries/sec)', fontsize=12)
    plt.legend(title='MAC Protocol')
    plt.savefig('fig1_throughput_vs_load.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Generating Graph 2: Collision Rate vs Load...")
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='arrival_rate', y='collision_rate', hue='protocol_name', marker='s', errorbar=('ci', 95))
    plt.title('MAC Layer Collision Rate vs. Traffic Load', fontsize=14, fontweight='bold')
    plt.xlabel('Arrival Rate (Packets/sec/Node)', fontsize=12)
    plt.ylabel('Collision Probability', fontsize=12)
    # Format Y-axis as a percentage
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
    plt.legend(title='MAC Protocol')
    plt.savefig('fig2_collision_vs_load.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Generating Graph 3: Protocol Selection Heatmap...")
    plt.figure(figsize=(10, 8))
    
    # We pivot the data to create a grid: X-axis is Load, Y-axis is Nodes. 
    # The value inside the grid is the optimal protocol ID (1=ALOHA, 2=CSMA)
    heatmap_data = df.pivot_table(index='nodes', columns='arrival_rate', values='optimal_protocol_id', aggfunc='max')
    
    # Sort the Y-axis so 10 nodes is at the bottom and 50 nodes is at the top
    heatmap_data = heatmap_data.sort_index(ascending=False)

    # Use a distinct color palette to show the "decision boundary"
    cmap = sns.color_palette("viridis", as_cmap=True)
    sns.heatmap(heatmap_data, cmap=cmap, annot=True, cbar=False, fmt=".0f", 
                annot_kws={"size": 14, "weight": "bold"})
    
    plt.title('AI Decision Boundary: Optimal Protocol Selection\n(1 = Slotted ALOHA | 2 = CSMA/CA)', fontsize=14, fontweight='bold')
    plt.xlabel('Arrival Rate (Traffic Load)', fontsize=12)
    plt.ylabel('Number of Nodes (Network Density)', fontsize=12)
    plt.savefig('fig3_protocol_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("\n✅ Success! Research graphs saved as high-resolution PNGs.")

if __name__ == "__main__":
    generate_research_graphs()