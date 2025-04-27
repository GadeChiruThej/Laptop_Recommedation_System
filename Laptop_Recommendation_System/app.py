from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Load dataset
df = pd.read_csv("DAVLaptopDatasets.csv")

# Convert necessary columns to numeric
cols_to_convert = [
    'Price', 'Rating', 'num_cores', 'num_threads', 'ram_memory',
    'primary_storage_capacity', 'display_size', 'resolution_width',
    'year_of_warranty'
]
for col in cols_to_convert:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with missing important values
df.dropna(subset=cols_to_convert + ['Model'], inplace=True)

# Create static directory if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

# Route for Home Page
@app.route('/')
def home():
    return render_template('home.html')  # home page with a button to go to index

# Route for Laptop Comparison Input Page
@app.route('/compare-laptops')
def index():
    return render_template('index.html')

# Auto-suggestions for laptop models
@app.route('/search_models')
def search_models():
    query = request.args.get('q', '').strip().lower()
    matched = df[df['Model'].str.lower().str.contains(query, na=False)]
    suggestions = matched['Model'].unique().tolist()
    return jsonify(suggestions)

# Laptop Comparison Logic
@app.route('/compare', methods=['POST'])
def compare():
    model1_input = request.form['laptop1'].strip().lower()
    model2_input = request.form['laptop2'].strip().lower()

    laptop1 = df[df['Model'].str.lower() == model1_input]
    laptop2 = df[df['Model'].str.lower() == model2_input]

    if laptop1.empty or laptop2.empty:
        return render_template('index.html', error="One or both laptops not found. Please make sure to choose from the suggestions.")

    laptop1 = laptop1.iloc[0]
    laptop2 = laptop2.iloc[0]

    def normalize(value, max_value):
        return float(value) / float(max_value) if pd.notna(value) and max_value != 0 else 0

    # Get max values for normalization
    max_price = df['Price'].max()
    max_cores = df['num_cores'].max()
    max_threads = df['num_threads'].max()
    max_ram = df['ram_memory'].max()
    max_storage = df['primary_storage_capacity'].max()
    max_display = df['display_size'].max()
    max_resolution = df['resolution_width'].max()
    max_warranty = df['year_of_warranty'].max()
    max_rating = df['Rating'].max()

    score1 = (
        normalize(laptop1['num_cores'], max_cores) +
        normalize(laptop1['num_threads'], max_threads) +
        normalize(laptop1['ram_memory'], max_ram) +
        normalize(laptop1['primary_storage_capacity'], max_storage) +
        normalize(laptop1['display_size'], max_display) +
        normalize(laptop1['resolution_width'], max_resolution) +
        normalize(laptop1['year_of_warranty'], max_warranty) +
        normalize(laptop1['Rating'], max_rating) -
        normalize(laptop1['Price'], max_price)
    )

    score2 = (
        normalize(laptop2['num_cores'], max_cores) +
        normalize(laptop2['num_threads'], max_threads) +
        normalize(laptop2['ram_memory'], max_ram) +
        normalize(laptop2['primary_storage_capacity'], max_storage) +
        normalize(laptop2['display_size'], max_display) +
        normalize(laptop2['resolution_width'], max_resolution) +
        normalize(laptop2['year_of_warranty'], max_warranty) +
        normalize(laptop2['Rating'], max_rating) -
        normalize(laptop2['Price'], max_price)
    )

    recommendation = laptop1['Model'] if score1 > score2 else laptop2['Model']

    # Attributes for visualization
    attributes = ['ram_memory', 'num_cores', 'num_threads', 'Price', 'display_size', 'resolution_width']
    laptop1_values = [laptop1[attr] for attr in attributes]
    laptop2_values = [laptop2[attr] for attr in attributes]

    # Create comparison visualizations (bar plots for attributes)
    visualization_paths = []
    for i, attribute in enumerate(attributes):
        fig, ax = plt.subplots(figsize=(8, 6))

        laptops = ['Laptop 1', 'Laptop 2']
        values = [laptop1_values[i], laptop2_values[i]]

        ax.bar(laptops, values, color=['red', 'blue'], edgecolor='black')

        ax.set_title(f'Comparison of {attribute.replace("_", " ").title()}', fontsize=16)
        ax.set_ylabel(attribute.replace("_", " ").title(), fontsize=14)
        ax.grid(axis='y')

        visualization_path = os.path.join('static', f'{attribute}_comparison_barplot.png')
        fig.savefig(visualization_path)
        plt.close(fig)

        visualization_paths.append(visualization_path)

    # Create Pie Chart for overall comparison of scores
    fig, ax = plt.subplots(figsize=(6, 6))
    colors = ['red', 'blue']
    labels = ['Laptop 1', 'Laptop 2']
    ax.pie([score1, score2], labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax.set_title('Overall Score Comparison', fontsize=16)

    pie_chart_path = os.path.join('static', 'overall_score_comparison_pie_chart.png')
    fig.savefig(pie_chart_path)
    plt.close(fig)

    return render_template('compare.html',
                           laptop1=laptop1,
                           laptop2=laptop2,
                           recommendation=recommendation,
                           visualization_paths=visualization_paths,
                           pie_chart_path=pie_chart_path)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
