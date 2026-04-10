import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# --- 1. PROTOCOL MAPPING ---
# We map strings to integers because ML models require numerical targets
PROTOCOL_MAP = {
    0: "PureALOHA",
    1: "SlottedALOHA",
    2: "CSMA/CA"
}

def generate_dummy_training_data(num_samples=1000):
    """
    Generates synthetic data to test the pipeline before Mayank's simulator finishes.
    This creates logical patterns for the model to learn.
    """
    print("Generating dummy dataset...")
    np.random.seed(42)
    
    # Randomly generate network conditions
    nodes = np.random.randint(10, 100, num_samples)
    arrival_rate = np.random.uniform(0.1, 1.0, num_samples)
    collision_rate = np.random.uniform(0.0, 0.8, num_samples)
    delay = np.random.uniform(0.01, 0.5, num_samples)
    queue_variance = np.random.uniform(0.0, 10.0, num_samples)
    
    # Calculate a rough "Load" metric to artificially determine the winner
    load = nodes * arrival_rate
    
    optimal_protocols = []
    for l in load:
        if l < 15:
            optimal_protocols.append(0) # Pure ALOHA wins at very low load
        elif l < 30:
            optimal_protocols.append(1) # Slotted ALOHA wins at medium load
        else:
            optimal_protocols.append(2) # CSMA wins at high load
            
    # Create the DataFrame
    df = pd.DataFrame({
        'nodes': nodes,
        'arrival_rate': arrival_rate,
        'collision_rate': collision_rate,
        'delay': delay,
        'queue_variance': queue_variance,
        'optimal_protocol_id': optimal_protocols
    })
    
    return df

def train_classifier_model(df):
    """
    Trains the Random Forest model and saves it to disk.
    """
    print("\n--- Training ML Classifier ---")
    
    # 1. Split features (X) and target (y)
    features = ['nodes', 'arrival_rate', 'collision_rate', 'delay', 'queue_variance']
    X = df[features]
    y = df['optimal_protocol_id']
    
    # 2. Split into Training and Testing sets (80/20 split)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Initialize the Random Forest (100 trees)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # 4. Train the model
    model.fit(X_train, y_train)
    
    # 5. Evaluate the model
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Model Accuracy on Test Set: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, predictions, target_names=["PureALOHA", "SlottedALOHA", "CSMA/CA"]))
    
    # 6. Save the trained model to disk so the simulator can use it later
    joblib.dump(model, 'mac_protocol_selector.pkl')
    print("Model saved as 'mac_protocol_selector.pkl'")
    
    return model

def predict_optimal_protocol(features_dict):
    """
    The inference function. This runs in REAL-TIME during the simulation.
    Loads the saved model and predicts the best protocol for current conditions.
    """
    # 1. Load the model from disk
    try:
        model = joblib.load('mac_protocol_selector.pkl')
    except FileNotFoundError:
        raise Exception("Model not found. Run train_classifier_model() first.")
        
    # 2. Format the incoming data into a DataFrame format the model expects
    input_data = pd.DataFrame([features_dict])
    
    # 3. Make the prediction
    predicted_id = model.predict(input_data)[0]
    
    # 4. Map the ID back to the human-readable string
    best_protocol = PROTOCOL_MAP[predicted_id]
    
    return best_protocol

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    # 1. Generate Fake Data (Replace this with real CSV loading later)
    dataset = generate_dummy_training_data()
    
    # 2. Train and Save
    trained_model = train_classifier_model(dataset)
    
    # 3. Test a Real-Time Prediction
    current_network_state = {
        'nodes': 50,
        'arrival_rate': 0.8,      # High load
        'collision_rate': 0.6,    # High collisions
        'delay': 0.2,
        'queue_variance': 5.5
    }
    
    print("\n--- Live Inference Test ---")
    print(f"Current Conditions: {current_network_state}")
    decision = predict_optimal_protocol(current_network_state)
    print(f"--> AI Decision Engine Selects: {decision}")