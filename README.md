# CS261 Group Project: Media Monitoring System

In the modern era, public figures and companies face constant scrutiny from the media and social platforms, which can significantly impact their public image and financial performance. This project aims to address this challenge by developing a Media Monitoring System that allows users to track publicly traded companies, receive updates about relevant news articles, and analyze the potential impact of these stories on public opinion and financial trends.

## Setting Up the Virtual Environment

1. **Initialize the Virtual Environment:**
   - Ensure that you have the latest version of python installed on your machine.
   - Run the following command to create a virtual environment named `venv`:
     ```
     python3 -m venv venv
     ```

2. **Activate the Virtual Environment:**

   - On Windows, use:
     ```
     .venv\Scripts\activate
     ```
   - On Unix or MacOS, use:
     ```
     source .venv/bin/activate
     ```

3. **Install Required Dependencies:**

   - Run the command:
     ```
     pip install -r requirements.txt
     ```

4. **Update `requirements.txt` After Installing New Libraries:**
   - If you install new libraries, update the `requirements.txt` file:
     ```
     pip freeze > requirements.txt
     ```

## Running the Website

- Execute `flask run` to run the website.

- Access the site at [http://localhost:5000/](http://localhost:5000/)

- Use the username and password 'person' for testing purposes.
