"""
FinEasy AI — Hugging Face Spaces entry point (Gradio SDK)
Mounts the full FastAPI backend + frontend onto Gradio's server.
"""
import gradio as gr
from backend.main import app as fastapi_app

# Minimal Gradio UI that auto-redirects to the real app
with gr.Blocks(title="FinEasy AI") as demo:
    gr.HTML("""
    <div style="text-align:center; padding:40px; font-family:sans-serif;">
        <h1>🧾 FinEasy AI</h1>
        <p>AI-Powered Indian Tax Filing Platform</p>
        <p>Redirecting to the application...</p>
        <script>window.location.href = '/app/index.html';</script>
        <p><a href="/app/index.html">Click here if not redirected</a></p>
    </div>
    """)

# Mount Gradio onto our existing FastAPI app — this makes everything work together
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
