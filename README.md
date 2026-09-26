# AI-Powered Interview Bot

An MVP of an adaptive AI interviewer powered by Gemini and Streamlit.

## Setup Instructions

1.  **Clone or create the directory structure.**
2.  **Create a Virtual Environment (Optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up API Key:**
    *   Create a `.env` file in the root directory (copy from `.env.example`).
    *   Add your Gemini API key: `GEMINI_API_KEY=your_api_key_here`
    *   Alternatively, set it as an environment variable in your terminal.
5.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

## Demo Flow

1.  Open the Streamlit app in your browser (usually `http://localhost:8501`).
2.  In the sidebar, enter a **Target Role** (e.g., "Senior Python Engineer").
3.  Upload a **PDF Resume**.
4.  Click **Start Interview**. The bot will analyze the resume and ask the first customized question.
5.  Reply to the questions in the chat interface. The bot will adaptively decide whether to probe deeper, clarify, move on, or finish based on your answers. You can view its reasoning in the expandable debug section.
6.  Once the bot decides to finish (or after enough questions), the interview concludes.
7.  Click **Generate Final Evaluation Report** to see the detailed assessment.
