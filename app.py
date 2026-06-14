"""Gradio web UI for The Unofficial Guide RAG pipeline.

Stage 6 of the architecture: a thin front end over query.ask(). Assumes the
ChromaDB index already exists at ./chroma_db (run embed.py first); this app
never builds the index itself.
"""

import gradio as gr

from query import ask


def answer_question(question):
    """Run a question through the RAG pipeline and return (answer, sources) text."""
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about CS professors at FSU, answered from student reviews."
    )

    question_box = gr.Textbox(
        label="Question",
        placeholder="e.g. What do students say about Professor Mills' teaching style?",
    )
    ask_button = gr.Button("Ask", variant="primary")

    answer_box = gr.Textbox(label="Answer", lines=8)
    sources_box = gr.Textbox(label="Sources", lines=4)

    # Both clicking Ask and pressing Enter in the input trigger the query.
    ask_button.click(
        fn=answer_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        fn=answer_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )


if __name__ == "__main__":
    demo.launch()
