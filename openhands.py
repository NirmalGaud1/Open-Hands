import streamlit as st
import os
import json
import requests
import markdown
import google.generativeai as genai
from datetime import datetime

# Configure Gemini API
API_KEY = "AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c"
genai.configure(api_key=API_KEY)
try:
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Failed to initialize Gemini model: {str(e)}")
    st.stop()

# LLM Call using Gemini
def llm_call(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini API error: {str(e)}"

# 1. Coding Tool: Execute Python code
def execute_code(code, language="python"):
    try:
        if language == "python":
            # Streamlit doesn't support direct exec; simulate output
            # In practice, use a sandboxed environment
            return f"Simulated execution of code:\n{code}\nOutput: Code executed successfully"
        else:
            return f"Unsupported language: {language}"
    except Exception as e:
        return f"Code execution error: {str(e)}"

# 2. Multimodal Web Browsing: Simulate webpage interaction
def browse_web(url):
    try:
        # Fetch webpage text (simplified, no Playwright)
        response = requests.get(url, timeout=5)
        text_content = response.text[:1000]  # Truncate for brevity
        visual_data = {"screenshot": "mock_screenshot.png", "elements": [{"id": "elem1", "type": "button"}]}

        # Use Gemini to analyze content
        prompt = f"Analyze webpage content: {text_content[:500]}\nVisual data: {json.dumps(visual_data)}"
        llm_response = llm_call(prompt)

        return {
            "text": text_content,
            "visual": visual_data,
            "llm_analysis": llm_response
        }
    except Exception as e:
        return f"Browsing error: {str(e)}"

# 3. Web Search: Simulate Tavily API
def search_web(query):
    try:
        # Mock search results
        response = {"results": [{"title": f"Result for {query}", "url": "http://example.com"}]}
        prompt = f"Summarize search results for query '{query}': {json.dumps(response)}"
        llm_response = llm_call(prompt)
        return {"raw_results": response, "summary": llm_response}
    except Exception as e:
        return f"Search error: {str(e)}"

# 4. Multimodal File Processing: Handle text and non-text files
def process_file(file):
    try:
        if file.name.endswith(".txt"):
            content = file.read().decode("utf-8")
        elif file.name.endswith(".pdf"):
            content = "Simulated PDF content"  # Requires pdf2md in practice
        else:
            content = "Unsupported file type"
        markdown_content = markdown.markdown(content)
        prompt = f"Analyze file content: {markdown_content[:500]}"
        llm_response = llm_call(prompt)
        return {"content": markdown_content, "llm_analysis": llm_response}
    except Exception as e:
        return f"File processing error: {str(e)}"

# 5. Task Planning: Generate plan with Gemini
def plan_task(task, step_count, history):
    prompt = f"""
    Task: {task}
    Current Step: {step_count}
    History (last 3 steps): {json.dumps(history[-3:] if history else [])}
    Summarize progress and plan next steps.
    """
    return llm_call(prompt)

# Main Agent Loop
def openhands_versa(task, file=None, max_steps=3, planning_interval=2):
    step_count = 0
    history = []
    
    while step_count < max_steps:
        # Periodic planning
        if step_count % planning_interval == 0:
            plan = plan_task(task, step_count, history)
            history.append(f"Plan: {plan}")
            yield f"**Step {step_count} - Plan**: {plan}"

        # Action selection
        action_result = None
        if "write code" in task.lower() or "code" in task.lower():
            prompt = f"Generate Python code for task: {task}"
            code = llm_call(prompt)
            action_result = execute_code(code, language="python")
            yield f"**Step {step_count} - Code Result**: {action_result}"
        elif "search" in task.lower():
            query = task.split("search")[-1].strip()
            action_result = search_web(query)
            yield f"**Step {step_count} - Search Result**: {action_result['summary']}"
        elif "browse" in task.lower():
            url = task.split("browse")[-1].strip() or "http://example.com"
            action_result = browse_web(url)
            yield f"**Step {step_count} - Browse Result**: {action_result['llm_analysis']}"
        elif "read file" in task.lower() and file:
            action_result = process_file(file)
            yield f"**Step {step_count} - File Result**: {action_result['llm_analysis']}"
        else:
            action_result = llm_call(f"Unknown task: {task}")
            yield f"**Step {step_count} - LLM Fallback**: {action_result}"

        history.append(action_result)
        step_count += 1

# Streamlit App
def main():
    st.title("OpenHands-Versa: Generalist AI Agent")
    st.write("Inspired by 'Coding Agents with Multimodal Browsing are Generalist Problem Solvers'")
    st.write(f"Current Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Task input
    task = st.text_input("Enter a task", placeholder="e.g., Write code to print Hello World, Search for Python documentation, Browse to http://example.com, Read file")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a file (optional, .txt or .pdf)", type=["txt", "pdf"])

    # Execute button
    if st.button("Execute Task"):
        if not task:
            st.error("Please enter a task.")
            return
        
        st.subheader("Task Execution Results")
        result_container = st.empty()
        results = []
        
        # Run agent and stream results
        for result in openhands_versa(task, file=uploaded_file, max_steps=3, planning_interval=2):
            results.append(result)
            result_container.markdown("\n\n".join(results))
        
        # Display final history
        st.subheader("Task History")
        st.write(results)

if __name__ == "__main__":
    main()
