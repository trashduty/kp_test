def generate_post_content(betting_preview, model_predictions, enhanced_narrative):
    # Combine content sections
    content = betting_preview + '\n\n' + model_predictions + '\n\n' + enhanced_narrative
    return content

# Example usage
betting_preview = "Betting odds are as follows: ..."
model_predictions = "Model Predictions: ..."
enhanced_narrative = "Enhanced Narrative: ..."

post_content = generate_post_content(betting_preview, model_predictions, enhanced_narrative)
print(post_content)