from groq import Groq
import json
import os

# ---------------- GROQ CLIENT ----------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

if not client.api_key:
    raise RuntimeError("GROQ_API_KEY not found in environment variables")

SUPPORTED_MODELS = [
    "llama-3.3-70b-specdec",
    "llama-3.3-70b-versatile",
    "llama-3.2-3b-preview",
    "llama-3.2-1b-preview"
]

# ---------------- CORE FUNCTION ----------------
def generate_learning_content(user_input, diagram_type="None"):
    prompt = f"""
You are StudyLM, an expert teacher for students.

Analyze the input carefully and return:

1. Topic (short and clear)
2. A simple, student-friendly explanation (200–300 words)
3. Best learning resources for beginners
4. If a diagram is requested, generate clear step-by-step points
   that visually explain the concept (NO code, NO Mermaid).

Return STRICT JSON ONLY in this exact format:

{{
  "topic": "",
  "explanation": "",
  "resources": {{
    "youtube": {{
      "title": "",
      "url": ""
    }},
    "website": {{
      "title": "",
      "url": ""
    }},
    "article": {{
      "title": "",
      "url": ""
    }}
  }},
  "diagram": {{
    "type": "{diagram_type}",
    "steps": []
  }}
}}

Guidelines:
- Explanation should be easy for school/college students
- Resources must be real, popular, and beginner-friendly
- Diagram steps should be short, clear, and ordered



Input:
{user_input}
"""

    last_error = None

    for model in SUPPORTED_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            raw = response.choices[0].message.content

            # Extract JSON safely
            start = raw.find("{")
            end = raw.rfind("}") + 1

            if start == -1 or end == -1:
                raise ValueError("Invalid JSON structure")

            return json.loads(raw[start:end])

        except Exception as e:
            last_error = e

    raise RuntimeError(f"All Groq models failed. Last error: {last_error}")
