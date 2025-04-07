
import asyncio
import streamlit as st
from dotenv import load_dotenv
from utils.llm_groq import llm_assistant
from utils.web_search import get_web_urls, crawl_webpages
from utils.vectorized_db import add_text_to_index, retrieve_context


load_dotenv("./.env")

async def run():
    st.set_page_config(page_title="Web Search Agent")
    st.title("Web Search Agent")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    prompt = st.text_area(
        label="Put your query here",
        placeholder="Add your query...",
        label_visibility="hidden",
    )

    is_web_search = st.toggle("Enable web search", value=False, key="enable_web_search")
    go = st.button(
        "⚡️ Go",
    )

    if prompt and go:
        if is_web_search:
            web_urls = get_web_urls(prompt)
            if not web_urls:
                st.write("No results found.")
                st.stop()

            results = await crawl_webpages(web_urls, prompt)
            add_text_to_index(results)

            context_results = retrieve_context(prompt)
            formatted_context = "\n".join([f"{result['url']}\n{result['text']}" for result in context_results])

            st.session_state.chat_history.append({"role": "user", "content": prompt})
            llm_response = llm_assistant(prompt, formatted_context, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": llm_response})

            st.write(llm_response)

        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            llm_response = llm_assistant(prompt, "")
            st.session_state.chat_history.append({"role": "assistant", "content": llm_response})

            st.write(llm_response)


if __name__ == "__main__":
    asyncio.run(run())