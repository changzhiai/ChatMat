import axios from 'axios';

const GEMINI_API_KEY = "AIzaSyC2OrwSSymjjq2RVHxrKjvLkRYu7xFA2pw";
const GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent";

const geminiService = {

  async generateContent(prompt) {
    try {
      const response = await axios.post(
        GEMINI_URL,
        {
          contents: [
            {
              parts: [
                {
                  text: prompt,
                },
              ],
            },
          ],
        },
        {
          headers: {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY,
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error generating content with Gemini API:", error);
      throw error;
    }
  },
};

export default geminiService;