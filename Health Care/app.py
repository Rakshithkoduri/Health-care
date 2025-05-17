from flask import Flask, render_template, request, redirect, url_for
import os
import pickle
import numpy as np
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'datasets')
MODEL_PATH = os.path.join(BASE_DIR, 'model\models', 'svc_new.pkl')

# Load datasets
try:
    description = pd.read_csv(os.path.join(DATA_DIR, 'description.csv'))
    precautions = pd.read_csv(os.path.join(DATA_DIR, 'precautions_df.csv'))
    medications = pd.read_csv(os.path.join(DATA_DIR, 'medications.csv'))
    diets = pd.read_csv(os.path.join(DATA_DIR, 'diets.csv'))
    workout = pd.read_csv(os.path.join(DATA_DIR, 'workout_df.csv'))
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    print("All datasets and model loaded successfully!")
except Exception as e:
    print(f"Error loading resources: {str(e)}")
    exit(1)

# Medical mappings (your existing mappings here)
SYMPTOMS_DICT = {'itching': 0, 'fever': 1}
DISEASES_MAP = {0: 'Fungal infection', 1: 'Allergy'}

@app.route('/', methods=['GET'])
def index():
    """Main page with symptom input form"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle symptom submission and return results"""
    if request.method == 'POST':
        symptoms = request.form.get('symptoms', '').strip()
        
        if not symptoms or symptoms.lower() == 'symptoms':
            return render_template('index.html', 
                                error="Please enter valid symptoms separated by commas")
        
        # Process symptoms
        user_symptoms = [s.strip().lower().replace(' ', '_') for s in symptoms.split(',')]
        valid_symptoms = [s for s in user_symptoms if s in SYMPTOMS_DICT]
        
        if not valid_symptoms:
            return render_template('index.html',
                                error="No valid symptoms recognized. Try: itching, fever, cough")
        
        # Create input vector
        input_vector = np.zeros(len(SYMPTOMS_DICT))
        for symptom in valid_symptoms:
            input_vector[SYMPTOMS_DICT[symptom]] = 1
        
        # Make prediction
        try:
            prediction = model.predict([input_vector])[0]
            predicted_disease = DISEASES_MAP.get(prediction, "Unknown Condition")
            
            # Get recommendations
            desc = description[description['Disease'] == predicted_disease]['Description'].values[0]
            prec = precautions[precautions['Disease'] == predicted_disease][
                ['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']
            ].values[0].tolist()
            meds = medications[medications['Disease'] == predicted_disease]['Medication'].tolist()
            diet = diets[diets['Disease'] == predicted_disease]['Diet'].tolist()
            workouts = workout[workout['disease'] == predicted_disease]['workout'].tolist()
            
            return render_template('results.html',
                                disease=predicted_disease,
                                symptoms=valid_symptoms,
                                description=desc,
                                precautions=prec,
                                medications=meds,
                                diets=diet,
                                workouts=workouts)
            
        except Exception as e:
            return render_template('index.html',
                                error=f"Prediction failed: {str(e)}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)