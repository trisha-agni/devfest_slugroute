# external imports
from pathlib import Path
from pyvis.network import Network
import networkx as nx
import streamlit as st
import tempfile
# internal imports
from slugroute.agent.advisor import SlugAdvisor
from slugroute.agent.tools import get_engine, get_retriever

st.set_page_config(
  page_title="SlugRoute | UCSC AI Academic Advisor",
  page_icon="🎓",
  layout="wide",
)


@st.cache_resource
def load_core_systems():
  return get_engine(), get_retriever(), SlugAdvisor()


engine, retriever, advisor = load_core_systems()

# ---------------------------------------------------------
# Sidebar: Student Profile
# ---------------------------------------------------------
with st.sidebar:
  st.title("📚 Student Profile")
  major = st.selectbox(
    "Declared Major",
    options=["CS_BS", "BME_BS"],
    format_func=lambda x: (
      "Computer Science (B.S.)" if x == "CS_BS" else "Bioinformatics (B.S.)"
    ),
  )

  all_courses = sorted(list(engine.G.nodes()))
  default_completed = ["CSE 20", "MATH 19A"]

  completed = st.multiselect(
    "Completed Courses",
    options=all_courses,
    default=[c for c in default_completed if c in engine.G],
  )

  max_credits = st.slider(
    "Max Credits / Quarter",
    min_value=12,
    max_value=22,
    value=19,
    step=1,
  )

  st.divider()
  if st.button("🔄 Reset Advisor Session", use_container_width=True):
    advisor.reset()
    st.session_state.messages = []
    st.rerun()

# ---------------------------------------------------------
# Main Interface Tabs
# ---------------------------------------------------------
tab_advisor, tab_roadmap, tab_graph = st.tabs(
  ["💬 AI Advisor", "🗺️ Degree Roadmap & Simulator", "🕸️ Prerequisite Graph"]
)

# --- Tab 1: AI Advisor Chat ---
with tab_advisor:
  st.subheader("UCSC AI Academic Advisor")
  st.caption("Grounded in authoritative catalog prerequisites and course data.")

  if "messages" not in st.session_state:
    st.session_state.messages = [
      {
        "role": "assistant",
        "content": (
          f"Hello! I am **SlugRoute**. I see you're in the **{major}** track "
          f"with **{len(completed)}** courses completed. How can I help you plan?"
        ),
      }
    ]

  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.markdown(msg["content"])

  user_prompt = st.chat_input("Ask about prerequisites, roadmaps, or AI electives...")
  if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
      st.markdown(user_prompt)

    with st.chat_message("assistant"):
      with st.spinner("Analyzing degree graph and catalog..."):
        # Contextualize prompt with current profile
        context = (
          f"[Student Profile: Major={major}, "
          f"Completed={completed}, MaxCredits={max_credits}]\n"
          f"Student Query: {user_prompt}"
        )
        reply = advisor.chat(context)
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Tab 2: Interactive Roadmap & What-If Simulator ---
with tab_roadmap:
  st.subheader("Deterministic Roadmap Simulator")
  st.caption("Computed using topological DAG scheduling and credit-load balancing.")

  default_targets = ["CSE 102", "CSE 130"]
  targets = st.multiselect(
    "Target Graduation Courses",
    options=all_courses,
    default=[c for c in default_targets if c in engine.G],
  )

  if targets:
    plan = engine.generate_quarter_plan(
      target_courses=targets,
      completed_courses=set(completed),
      major=major,
      max_credits_per_qtr=max_credits,
    )

    if not plan:
      st.success("All target courses are already completed or satisfied!")
    else:
      cols = st.columns(min(len(plan), 4))
      for idx, q in enumerate(plan):
        col = cols[idx % 4]
        with col:
          with st.container(border=True):
            st.markdown(f"#### Quarter {q['quarter']}")
            st.caption(f"**Total Credits:** {q['total_credits']} cr")
            for c in q["courses"]:
              data = retriever.get_course(c) or {}
              title = data.get("title", "")
              credits_num = data.get("credits", 5)
              st.markdown(f"- **{c}** ({credits_num} cr)\n  *{title}*")
  else:
    st.info("Select one or more target courses above to generate your roadmap.")

# --- Tab 3: Prerequisite Knowledge Graph ---
with tab_graph:
  st.subheader("Interactive Prerequisite Network")
  st.caption("Visualizing prerequisite ancestor chains using NetworkX.")

  graph_course = st.selectbox(
    "Select Course to Inspect Dependency Chain",
    options=all_courses,
    index=all_courses.index("CSE 101") if "CSE 101" in all_courses else 0,
  )

  # Add depth slider
  depth_option = st.select_slider(
    "Prerequisite Depth",
    options=[1, 2, 3, "Full Tree"],
    value=1,
    help="1: Direct prereqs only | Full Tree: Entire ancestral chain",
  )

  if depth_option == "Full Tree":
    nodes_to_render = nx.ancestors(engine.G, graph_course) | {graph_course}
  else:
    nodes_to_render = {graph_course}
    current_frontier = {graph_course}
    for _ in range(depth_option):
      next_frontier = set()
      for n in current_frontier:
        next_frontier.update(engine.G.predecessors(n))
      nodes_to_render.update(next_frontier)
      current_frontier = next_frontier

  sub_g = engine.G.subgraph(nodes_to_render).copy()
  if sub_g.number_of_nodes() > 0:
    net = Network(
      height="520px",
      width="100%",
      directed=True,
      bgcolor="#0e1117",
      font_color="#ffffff",
      cdn_resources="remote",  # <-- Uses CDN; stops creating lib/ folder
    )

    for n in sub_g.nodes():
        if n == graph_course:
            color = "#fdc700"  # 🍌 Target Course: UCSC Banana Slug Gold
        elif n in completed:
            color = "#10B981"  # Completed: Emerald Green
        else:
            color = "#003c6c"  # Pending prerequisite: UCSC Deep Blue

        net.add_node(
            n,
            label=n,
            title=f"{n}: {sub_g.nodes[n].get('title', '')}",
            color=color,
            size=25 if n == graph_course else 18,
        )

    for u, v in sub_g.edges():
      net.add_edge(u, v, color="#555555")

    net.set_options(
      """
      var options = {
        "physics": {
          "hierarchicalRepulsion": {"nodeDistance": 130},
          "solver": "hierarchicalRepulsion"
        },
        "layout": {
          "hierarchical": {
            "direction": "LR",
            "sortMethod": "directed"
          }
        }
      }
      """
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
      net.save_graph(tmp.name)
      st.iframe(Path(tmp.name), height=540)
  else:
    st.info(f"{graph_course} has no prerequisite dependencies.")
