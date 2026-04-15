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
    sns.lineplot(data=df, x='arrival_rate', y='throughput_value', hue='protocol_name', marker='o', errorbar=('ci', 95))
    plt.title('System Throughput vs. Traffic Load (95% CI)', fontsize=14, fontweight='bold')
    plt.xlabel('Arrival Rate (Packets/sec/Node)', fontsize=12)
    plt.ylabel('Throughput (Successful Deliveries/sec)', fontsize=12)
    plt.ylim(bottom=0) # Prevents shadows from bleeding into negative numbers
    plt.legend(title='MAC Protocol')
    plt.savefig('fig1_throughput_vs_load.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Generating Graph 2: Collision Rate vs Load...")
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='arrival_rate', y='collision_rate', hue='protocol_name', marker='s', errorbar=('ci', 95))
    plt.title('MAC Layer Collision Rate vs. Traffic Load', fontsize=14, fontweight='bold')
    plt.xlabel('Arrival Rate (Packets/sec/Node)', fontsize=12)
    plt.ylabel('Collision Probability', fontsize=12)
    plt.ylim(bottom=0, top=1.1) # Locks Y-axis cleanly between 0% and 110%
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
    plt.legend(title='MAC Protocol')
    plt.savefig('fig2_collision_vs_load.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Generating Graph 3: Protocol Selection Heatmap...")
    plt.figure(figsize=(10, 8))
    
    heatmap_data = df.pivot_table(index='nodes', columns='arrival_rate', values='optimal_protocol_id', aggfunc='max')
    heatmap_data = heatmap_data.sort_index(ascending=False)

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