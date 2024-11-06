from flask import Flask, request, render_template
import requests
import os
import time

app = Flask(__name__)


API_KEY = 'a03sn6saSYbd5wiZaCk4dnTyDAoRUXSLhGM4K5F3'
API_URL= 'https://api.cohere.ai/v1/generate'

def get_weight_category(weight, height_cm):
    """Calculate BMI and determine the weight category and recommendation."""
    height_m = height_cm / 100  
    bmi = weight / (height_m ** 2)  # BMI formula
    if bmi < 18.5:
        return "underweight", "Focus on a balanced diet with a caloric surplus and strength training to promote healthy weight gain."
    elif 18.5 <= bmi < 24.9:
        return "normal weight", "Maintain your weight by continuing a balanced diet and regular exercise."
    elif 25 <= bmi < 29.9:
        return "overweight", "Consider a combination of cardio and a moderate caloric deficit to support healthy weight loss."
    else:
        return "obese", "Focus on low-impact cardio, strength training, and a controlled diet to support weight loss and improve health."

def get_ai_workout_plan(age, weight, height, fitness_goal, experience_level):
    """Generate a personalized workout plan using Cohere API with retry logic."""
    prompt = (f"Create a summarized workout plan in bullets  for a {age}-year-old who weighs {weight} kg, is {height} cm tall, "
              f"has a fitness goal of '{fitness_goal}', and has an experience level of '{experience_level}'. \n"
              f"Provide a weekly schedule with exercises, sets, reps, and basic nutrition advice.\n ")
    
    

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                'https://api.cohere.ai/v1/generate',
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": "command-xlarge-nightly",
                    "prompt": prompt,
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )

            response.raise_for_status()  
            response_data = response.json()

            if "generations" in response_data and len(response_data["generations"]) > 0:
                return response_data['generations'][0]['text'].strip()
            else:
                return "Unable to generate a workout plan at the moment. Please try again later."
        
        except requests.exceptions.RequestException as e:
            if response.status_code == 429 and attempt < max_retries - 1:
                print("Rate limit hit. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Error communicating with the API: {e}")
                return "Could not generate a workout plan. Please try again later."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    age = int(request.form['age'])
    weight = float(request.form['weight'])
    height_cm = float(request.form['height'])  
    goal = request.form['goal']
    experience_level = request.form.get('experience_level', 'beginner')  

    weight_category, weight_suggestion = get_weight_category(weight, height_cm)

    ai_fitness_plan = get_ai_workout_plan(age, weight, height_cm, goal, experience_level)

    return render_template('result.html', fitness_plan=ai_fitness_plan, weight_category=weight_category, weight_suggestion=weight_suggestion)

if __name__ == "__main__":
    app.run(debug=True)
