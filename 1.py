# 1.py
# streamlit run 1.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="多 Sheet 气泡图", layout="wide")
st.title("📊 多 Sheet 气泡图可视化")

# ✅ 上传控件放到主区域
uploaded_file = st.file_uploader("📁 请上传 Excel 文件（含多个 Sheet，每个 Sheet 一张图）", type=["xlsx"])

# 控制面板移到主区域下面
col1, col2 = st.columns(2)
with col1:
    font_size = st.slider("📝 字体大小", 8, 24, 12)
with col2:
    bubble_scale = st.slider("🎯 气泡大小倍数", 10, 200, 80)

# 如果上传了文件
if uploaded_file is not None:
    # 读取所有 Sheet
    sheets = pd.read_excel(uploaded_file, sheet_name=None)

    st.success(f"🎉 成功读取 {len(sheets)} 个 Sheet：{', '.join(sheets.keys())}")

    for sheet_name, df in sheets.items():
        st.subheader(f"📍 {sheet_name}")

        # 必要列检查
        required_cols = {"体验点", "重要度", "满意度", "分歧度"}
        if not required_cols.issubset(df.columns):
            st.warning(f"❌ Sheet “{sheet_name}” 缺少必要列，已跳过")
            continue

        x_avg = df["重要度"].mean()
        y_avg = 0

        fig = px.scatter(
            df,
            x="重要度",
            y="满意度",
            size=df["分歧度"] * bubble_scale,
            text="体验点",
            color="满意度",
            size_max=60,
            color_continuous_scale="Viridis"
        )

        fig.add_vline(x=x_avg, line_dash="dash", line_color="gray")
        fig.add_hline(y=y_avg, line_dash="dash", line_color="gray")
        fig.update_traces(textposition="top center", textfont_size=font_size)
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            width=1000,
            height=600,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👆 请上传包含多个 Sheet 的 Excel 文件，每个 Sheet 都包含“体验点 / 重要度 / 满意度 / 分歧度”四列。")
