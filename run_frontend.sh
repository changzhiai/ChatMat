#!/bin/bash
# Run the ChatMat frontend

cd "$(dirname "$0")/chatmat"
streamlit run app.py

