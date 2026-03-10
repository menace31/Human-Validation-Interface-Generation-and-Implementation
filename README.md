# Human-Validation-Interface-Generation-and-Implementation

This project is a Streamlit app that extracts customer update requests with OpenAI, then lets a human approve or reject each proposed action before sending the final result.

To run the program:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Before launching the app, create a `.streamlit/secrets.toml` file and add your OpenAI key inside it, otherwise the program will not work:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
```

The application will then open in Streamlit, where you can paste a customer message, generate the validation proposal, review each extracted tool, and approve or reject the final output.