import json
import argparse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse

def generate_mask():
    """Generate an elliptical mask for the word cloud"""
    x, y = np.ogrid[:800, :800]
    center = (400, 400)
    a, b = 350, 250  # Semi-major and semi-minor axes
    
    # Create elliptical mask
    mask = ((x - center[0])**2 / a**2 + (y - center[1])**2 / b**2) <= 1
    return mask

def get_top_20_entries(data, bubble_metric):
    """Get the top 20 entries based on the specified metric"""
    metric_dict = {
        key: value['total_log_entries'] if bubble_metric == 'log_entries' else len(value['ips'])
        for key, value in data.items()
    }
    sorted_items = sorted(metric_dict.items(), key=lambda x: x[1], reverse=True)[:20]
    top_20_data = {key: data[key] for key, _ in sorted_items}
    return top_20_data

def get_title(bubble_metric):
    """Generate appropriate title based on the metric"""
    if bubble_metric == 'log_entries':
        return 'Top 20 BGP ASN - Total Log Entries'
    else:
        return 'Top 20 BGP ASN - Unique IP Addresses'

def create_table(ax, data, bubble_metric):
    """Create a table showing the metrics for each item"""
    table_data = []
    headers = ['ASN/BGP Description', 'Value']
    
    sorted_items = sorted(
        data.items(),
        key=lambda x: x[1]['total_log_entries'] if bubble_metric == 'log_entries' else len(x[1]['ips']),
        reverse=True
    )
    
    for key, value in sorted_items:
        metric_value = value['total_log_entries'] if bubble_metric == 'log_entries' else len(value['ips'])
        table_data.append([key, f"{metric_value:,}"])
    
    table = ax.table(
        cellText=table_data,
        colLabels=headers,
        loc='right',
        cellLoc='left',
        bbox=[1.1, 0, 0.5, 0.95]
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.auto_set_column_width([0, 1])
    
    for i in range(len(headers)):
        table[(0, i)].set_text_props(weight='bold')
        table[(0, i)].set_facecolor('#E6E6E6')
    
    return table

def generate_wordcloud(data, bubble_metric, output_file):
    """
    Generates a word cloud in an elliptical shape with an accompanying table.
    Args:
        data (dict): Parsed JSON data.
        bubble_metric (str): Metric to size bubbles ('log_entries' or 'ip_count').
        output_file (str): Output PNG file name.
    """
    # Get top 20 entries
    top_20_data = get_top_20_entries(data, bubble_metric)
    
    # Create word frequency dictionary
    word_freq = {}
    for key, value in top_20_data.items():
        size_metric = value['total_log_entries'] if bubble_metric == 'log_entries' else len(value['ips'])
        word_freq[key] = size_metric
    
    # Create mask for elliptical shape
    mask = generate_mask()
    
    # Generate word cloud with adjusted spacing parameters
    wordcloud = WordCloud(
        width=800,
        height=800,
        background_color='white',
        colormap='viridis',
        prefer_horizontal=0.7,
        min_font_size=10,
        max_font_size=100,
        relative_scaling=0.3,  # Reduce this to make words more similarly sized
        mask=mask,
        contour_width=1,
        contour_color='lightgray',
        collocations=False,    # Prevent duplicate words
        margin=5             # Increase margin between words
    ).generate_from_frequencies(word_freq)
    
    # Create figure with extra space for table
    fig = plt.figure(figsize=(15, 10))
    
    # Get the title
    title = get_title(bubble_metric)
    
    # Create main subplot for word cloud
    ax_cloud = plt.subplot(111)
    
    # Add title as a text object with centering based on figure coordinates
    fig.text(0.5, 0.95, title, 
             horizontalalignment='center',
             verticalalignment='center',
             fontsize=16,
             fontweight='bold')
    
    ax_cloud.imshow(wordcloud, interpolation='bilinear')
    ax_cloud.axis('off')
    
    # Add table
    create_table(ax_cloud, top_20_data, bubble_metric)
    
    # Adjust layout
    plt.subplots_adjust(right=0.7, top=0.85)
    
    # Save the figure
    plt.savefig(output_file, bbox_inches='tight', dpi=300)
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Generate a word cloud from JSON data.")
    parser.add_argument('--input', '-i', required=True, help="Path to the input JSON file.")
    parser.add_argument('--output', '-o', required=True, help="Path to the output PNG file.")
    parser.add_argument('--metric', '-m', choices=['log_entries', 'ip_count'], default='log_entries',
                      help="Metric to size bubbles ('log_entries' or 'ip_count'). Default is 'log_entries'.")
    
    args = parser.parse_args()
    
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    generate_wordcloud(data, args.metric, args.output)

if __name__ == "__main__":
    main()
