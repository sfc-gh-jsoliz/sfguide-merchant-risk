"""Ask the agent: natural-language questions to the Cortex Agent over the semantic view."""
import pandas as pd
import streamlit as st

import ai
import brand
from views.common import stream


def show_answer(a, mode, animate):
    lbl = ('<span class="mr-cap sample">Sample AI response · captured from a Live run</span>' if mode != "Live"
           else '<span class="mr-cap">Live · Cortex Agent</span>')
    st.markdown(f'<div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap"><b>{brand.esc(a["question"])}</b>{lbl}</div>', unsafe_allow_html=True)
    if animate:
        st.write_stream(stream(brand.md_safe(a["text"])))
    else:
        st.markdown(brand.md_safe(a["text"]))
    if a.get("table") and a["table"].get("rows"):
        st.dataframe(pd.DataFrame(a["table"]["rows"], columns=a["table"]["columns"]), hide_index=True, width="stretch")
    if a.get("sql"):
        with st.expander("SQL written by Cortex Analyst"):
            st.code(a["sql"], language="sql")
    st.markdown(f'<div class="mr-src">Source: semantic view <code>MERCHANT_RISK_SV</code> via agent <code>MERCHANT_RISK_AGENT</code> · '
                f'{int(a.get("latency_ms") or 0) / 1000:.1f} s measured in Live</div>', unsafe_allow_html=True)


def render(mode):
    st.markdown(brand.header(
        "Ask the agent", "Plain-English questions about the book. The agent writes SQL over the semantic view and answers only from the result.",
        "Powered by Cortex Agents + Cortex Analyst" if mode == "Live" else "Sample AI responses · Cortex Agents in Live", mode),
        unsafe_allow_html=True)
    with st.container(key="card_ask"):
        st.markdown('<p class="mr-card-s">Try a question</p>', unsafe_allow_html=True)
        picked = st.pills("Suggested questions", ai.QUESTIONS, label_visibility="collapsed", key="ask_pick")
        typed = None
        if mode == "Live":
            typed = st.chat_input("Ask about approvals, declines, risk scores, reserves or the CFPB backdrop")
        else:
            st.caption("Sample mode replays the four suggested questions. Switch to Live to ask your own.")
    q = typed or picked
    if not q:
        if st.session_state.get("last_answer"):
            with st.container(key="card_answer"):
                show_answer(st.session_state["last_answer"], mode, False)
        else:
            st.markdown('<div class="mr-card mr-empty"><b>No question yet</b>Pick a suggested question to see the agent at work.</div>', unsafe_allow_html=True)
        return
    if st.session_state.get("last_answer", {}).get("question") == q and not typed:
        with st.container(key="card_answer"):
            show_answer(st.session_state["last_answer"], mode, False)
        return
    ph = st.empty()

    def on_step(i, _s):
        ph.markdown(f'<div class="mr-card">{brand.steps_html(ai.ASK_STEPS, i)}</div>', unsafe_allow_html=True)
    try:
        if mode == "Live":
            a = ai.ask_live(q, on_step)
        else:
            a = ai.sample_ai()["ask"].get(q)
            ai.sample_wait(on_step, ai.ASK_STEPS)
            if a is None:
                raise RuntimeError("No captured sample for this question.")
    except Exception as e:
        ph.empty()
        st.error(f"Agent call failed: {e}")
        return
    ph.markdown(f'<div class="mr-card">{brand.steps_html(ai.ASK_STEPS, 4, True)}</div>', unsafe_allow_html=True)
    st.session_state["last_answer"] = a
    with st.container(key="card_answer"):
        show_answer(a, mode, True)
