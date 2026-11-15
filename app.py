# external imports
from pathlib import Path
from pyvis.network import Network
import base64
import networkx as nx
import streamlit as st
import tempfile
# internal imports
from slugroute.agent.advisor import SlugAdvisor
from slugroute.agent.tools import get_engine, get_retriever

SLUG_ICON_PATH = Path(__file__).resolve().parent / "assets" / "banana_slug.png"
SLUG_SVG_PATH = Path(__file__).resolve().parent / "assets" / "banana_slug.svg"

# Base64 SVG for crisp inline rendering in banners and sidebar
if SLUG_SVG_PATH.exists():
  with open(SLUG_SVG_PATH, "r", encoding="utf-8") as f:
    _svg_code = f.read()
  SLUG_SVG_B64 = f"data:image/svg+xml;base64,{base64.b64encode(_svg_code.encode()).decode()}"  # noqa
else:
  SLUG_SVG_B64 = ""

st.set_page_config(
  page_title="SlugRoute | UCSC AI Academic Advisor",
  page_icon=str(SLUG_ICON_PATH) if SLUG_ICON_PATH.exists() else "🍌",
  layout="wide",
)

# Custom UCSC Banana Slug Gold & Navy Styling
st.markdown(
  """
  <style>
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
      color: #ffd100 !important;
      border-bottom-color: #ffd100 !important;
    }
    .stButton>button:hover {
      border-color: #ffd100 !important;
      color: #ffd100 !important;
    }
  </style>
  """,
  unsafe_allow_html=True,
)


@st.cache_resource
def load_core_systems():
  return get_engine(), get_retriever(), SlugAdvisor()


engine, retriever, advisor = load_core_systems()

# ---------------------------------------------------------
# Sidebar: Student Profile & Google Tech Credits
# ---------------------------------------------------------
with st.sidebar:
  st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
      <img src="{SLUG_SVG_B64}" width="38" alt="Banana Slug" />
      <div>
        <h2 style="margin: 0; color: #ffd100; font-size: 1.35rem; line-height: 1.1;">
          SlugRoute
        </h2>
        <span style="font-size: 0.74rem; color: #9ca3af;">UCSC Degree Navigator</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
  )
  st.markdown(
    "<div style='font-weight:600; font-size:0.92rem; margin:6px 0 2px 0; color:#E2E8F0;'>📚 Student Profile</div>",  # noqa
    unsafe_allow_html=True,
  )
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

  if st.button("🔄 Reset Advisor Session", use_container_width=True):
    advisor.reset()
    st.session_state.messages = []
    st.rerun()

  # Powered by Google AI Technology Card (Compact & High-Contrast)
  st.markdown(
    """
    <div style="background: #002244; border: 2px solid #FFD100; border-radius: 10px; padding: 10px 12px; margin-top: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
      <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 7px; border-bottom: 1px solid rgba(255, 209, 0, 0.35); padding-bottom: 4px;">
        <span style="font-size: 1.05rem;">⚡</span>
        <strong style="color: #FFD100; font-size: 0.90rem; letter-spacing: 0.3px;">Powered by Google AI</strong>
      </div>
      <div style="font-size: 0.79rem; color: #FFFFFF; line-height: 1.55;">
        <div style="margin-bottom: 2px;">
          <span style="color: #FFD100;">🔹</span> <strong style="color: #FFFFFF;">Gemini 3.5 Flash</strong> <span style="color: #CBD5E1; font-size: 0.73rem;">(Reasoning)</span>
        </div>
        <div style="margin-bottom: 2px;">
          <span style="color: #FFD100;">🔹</span> <strong style="color: #FFFFFF;">Gemini 3.5 Flash Lite</strong> <span style="color: #CBD5E1; font-size: 0.73rem;">(Failover)</span>
        </div>
        <div style="margin-bottom: 2px;">
          <span style="color: #FFD100;">🔹</span> <strong style="color: #FFFFFF;">Google GenAI SDK</strong> <span style="color: #CBD5E1; font-size: 0.73rem;">(Tool Calling)</span>
        </div>
        <div style="margin-bottom: 2px;">
          <span style="color: #FFD100;">🔹</span> <strong style="color: #FFFFFF;">Google AI Studio</strong> <span style="color: #CBD5E1; font-size: 0.73rem;">(API Platform)</span>
        </div>
      </div>
      <div style="margin-top: 7px; font-size: 0.78rem; font-weight: 600; color: #FFD100; text-align: center; border-top: 1px solid rgba(255,209,0,0.35); padding-top: 5px; letter-spacing: 0.2px;">
        Built for UCSC DevFest '26 🍌
      </div>
    </div>
    """,  # noqa
    unsafe_allow_html=True,
  )

# ---------------------------------------------------------
# Main Header Banner (UCSC Banana Slug Theme)
# ---------------------------------------------------------
st.markdown(
  f"""
  <div style="background: linear-gradient(135deg, #003c6c 0%, #001f3f 100%); padding: 18px 24px; border-radius: 12px; border-left: 6px solid #ffd100; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
      <div style="display: flex; align-items: center; gap: 14px;">
        <img src="{SLUG_SVG_B64}" width="60" alt="UCSC Banana Slug" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));" />
        <div>
          <h1 style="color: #ffd100; margin: 0; font-size: 2rem; line-height: 1.1;">
            SlugRoute
          </h1>
          <p style="color: #e5e7eb; margin: 4px 0 0 0; font-size: 0.95rem;">
            UCSC Academic Advisor & Degree Pathfinder &bull; <em>Fiat Slug!</em>
          </p>
        </div>
      </div>
      <div style="background: rgba(255, 209, 0, 0.15); border: 1px solid #ffd100; border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; color: #ffd100; font-weight: 600;">
        UC Santa Cruz 🌲
      </div>
    </div>
  </div>
  """,  # noqa
  unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Main Interface Tabs
# ---------------------------------------------------------
tab_advisor, tab_roadmap, tab_graph = st.tabs(
  ["💬 AI Advisor", "🗺️ Degree Roadmap & Simulator", "🕸️ Prerequisite Graph"]
)

# --- Tab 1: AI Advisor Chat ---
with tab_advisor:
  st.subheader("🍌 UCSC AI Academic Advisor")
  st.caption("Grounded in authoritative catalog prerequisites and course data.")

  if "messages" not in st.session_state:
    st.session_state.messages = [
      {
        "role": "assistant",
        "content": (
          f"Fiat Slug! 🍌 I am **SlugRoute**, your UCSC AI Academic Advisor. "
          f"I see you're in the **{major}** track "
          f"with **{len(completed)}** courses completed. How can I help you plan?"
        ),
      }
    ]

  chat_container = st.container()

  with chat_container:
    for msg in st.session_state.messages:
      avatar = (
        str(SLUG_ICON_PATH)
        if (msg["role"] == "assistant" and SLUG_ICON_PATH.exists())
        else ("🍌" if msg["role"] == "assistant" else "🌲")
      )
      with st.chat_message(msg["role"], avatar=avatar):
        content = (
          engine.linkify_courses(msg["content"])
          if msg["role"] == "assistant"
          else msg["content"]
        )
        st.markdown(content)

  user_prompt = st.chat_input("Ask about prerequisites, roadmaps, or AI electives...")
  if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with chat_container:
      with st.chat_message("user", avatar="🌲"):
        st.markdown(user_prompt)

      asst_avatar = (
        str(SLUG_ICON_PATH) if SLUG_ICON_PATH.exists() else "🍌"
      )
      with st.chat_message("assistant", avatar=asst_avatar):
        with st.spinner("Analyzing degree graph and catalog..."):
          # Contextualize prompt with current profile
          context = (
            f"[Student Profile: Major={major}, "
            f"Completed={completed}, MaxCredits={max_credits}]\n"
            f"Student Query: {user_prompt}"
          )
          reply = advisor.chat(context)
          if not reply:
            reply = (
              "I apologize, but I could not formulate a response. "
              "Please try rephrasing your question."
            )
          reply_linked = engine.linkify_courses(reply)
          st.markdown(reply_linked)
          st.session_state.messages.append(
            {"role": "assistant", "content": reply_linked}
          )

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
              url = data.get("url") or engine.get_course_url(c)
              if url:
                st.markdown(
                  f"- **[{c}]({url})** ({credits_num} cr)\n  *{title}*"
                )
              else:
                st.markdown(f"- **{c}** ({credits_num} cr)\n  *{title}*")
  else:
    st.info("Select one or more target courses above to generate your roadmap.")

# --- Tab 3: Prerequisite Knowledge Graph ---
with tab_graph:
  st.subheader("Interactive Prerequisite Network")
  st.caption(
    "Visualizing prerequisite ancestor chains &bull; "
    "🟡 **Target (Slug Gold)** | 🟢 **Completed (Green)** | "
    "🔵 **Pending (UCSC Blue)**"
  )

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
        color = "#FFD100"  # Target course: Banana Slug Gold
      elif n in completed:
        color = "#00CC96"  # Completed: Forest Green
      else:
        color = "#005596"  # Pending prerequisite: UCSC Navy Blue

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
          "hierarchicalRepulsion": {"nodeDistance": 140},
          "solver": "hierarchicalRepulsion",
          "stabilization": {
            "enabled": true,
            "iterations": 500,
            "fit": true
          }
        },
        "layout": {
          "hierarchical": {
            "direction": "LR",
            "sortMethod": "directed",
            "levelSeparation": 150,
            "parentCentralization": true
          }
        },
        "interaction": {
          "dragNodes": true,
          "dragView": true,
          "zoomView": true,
          "hover": true
        }
      }
      """
    )

    raw_html = net.generate_html()
    fit_script = """
    <script type="text/javascript">
      function fitAndCenter() {
        if (typeof network !== 'undefined' && network !== null) {
          network.fit({
            animation: {
              duration: 350,
              easingFunction: 'easeInOutQuad'
            }
          });
        }
      }

      window.addEventListener('load', function() {
        setTimeout(fitAndCenter, 50);
        setTimeout(fitAndCenter, 200);
      });

      if (typeof ResizeObserver !== 'undefined') {
        var containerEl = document.getElementById('mynetwork') || document.body;
        var ro = new ResizeObserver(function(entries) {
          for (var i = 0; i < entries.length; i++) {
            if (entries[i].contentRect.width > 50) {
              setTimeout(fitAndCenter, 50);
              setTimeout(fitAndCenter, 200);
            }
          }
        });
        ro.observe(containerEl);
      }

      window.addEventListener('resize', fitAndCenter);
    </script>
    </body>
    """
    custom_html = raw_html.replace("</body>", fit_script)
    with tempfile.NamedTemporaryFile(
      delete=False, suffix=".html", mode="w", encoding="utf-8"
    ) as tmp:
      tmp.write(custom_html)
      tmp.flush()
      st.iframe(Path(tmp.name), height=540)
  else:
    st.info(f"{graph_course} has no prerequisite dependencies.")
