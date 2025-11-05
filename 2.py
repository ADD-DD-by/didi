import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 评论分析看板")

uploaded_file = st.file_uploader("请上传分析好的 Excel 文件（含 1~3 个工作表：近半年、近一年、近两年）", type="xlsx")

if uploaded_file:

    def clean_df(df, name):
        before = len(df)
        df['重要度'] = pd.to_numeric(df['重要度'], errors='coerce')
        df['满意度'] = pd.to_numeric(df['满意度'], errors='coerce')
        df['分歧度'] = pd.to_numeric(df['分歧度'], errors='coerce')
        df_cleaned = df.dropna(subset=['重要度', '满意度', '分歧度'])
        st.write(f"🧹 {name} 清洗后删除了 {before - len(df_cleaned)} 行空值")
        return df_cleaned

    # 检查可用工作表
    xls = pd.ExcelFile(uploaded_file)
    available_sheets = xls.sheet_names
    st.info(f"📘 检测到以下工作表: {', '.join(available_sheets)}")

    dfs = {}
    for sheet in ['近半年数据分析', '近一年数据分析', '近两年数据分析']:
        if sheet in available_sheets:
            dfs[sheet] = clean_df(pd.read_excel(xls, sheet_name=sheet), sheet)
        else:
            st.warning(f"⚠️ 文件中未找到工作表：{sheet}，已跳过。")

    if not dfs:
        st.error("❌ 文件中未包含任何有效的数据工作表，请检查文件内容。")
        st.stop()

    def normalize_satisfaction(s):
        return (s + 5) / 10

    def create_traces(df, period_name):
        avg_importance = df['重要度'].mean()
        traces = []
        unique_points = df['体验点'].unique()
        sizeref = 2. * max(df['分歧度']) / (20. ** 2) if len(df) > 0 else 1

        for point in unique_points:
            df_sub = df[df['体验点'] == point]
            norm_satis_sub = normalize_satisfaction(df_sub['满意度'])
            trace = go.Scatter(
                x=df_sub['重要度'],
                y=df_sub['满意度'],
                mode='markers+text',
                text=df_sub['体验点'],
                textposition='top center',
                marker=dict(
                    size=df_sub['分歧度'],
                    sizemode='area',
                    sizeref=sizeref,
                    sizemin=4,
                    color=norm_satis_sub,
                    coloraxis='coloraxis',
                    line=dict(width=1, color='DarkSlateGrey')
                ),
                name=point,
                legendgroup=point,
                visible=False,
                hovertemplate=(
                    "体验点: %{text}<br>" +
                    "重要度: %{x}<br>" +
                    "满意度: %{y}<br>" +
                    "分歧度: %{marker.size}<extra></extra>"
                )
            )
            traces.append(trace)
        return traces, avg_importance

    def create_reference_shapes(avg_importance, df):
        return [
            dict(type='line', x0=df['重要度'].min(), x1=df['重要度'].max(), y0=0, y1=0,
                 line=dict(color='lightgray', width=2, dash='dash')),
            dict(type='line', x0=avg_importance, x1=avg_importance, y0=df['满意度'].min(), y1=df['满意度'].max(),
                 line=dict(color='lightgray', width=2, dash='dash'))
        ]

    def create_annotations(avg_importance, df):
        return [
            dict(x=avg_importance, y=df['满意度'].max(), text=f"重要度均值: {avg_importance:.2f}",
                 showarrow=True, arrowhead=1, ax=40, ay=0),
            dict(x=df['重要度'].max(), y=0, text="满意度 = 0",
                 showarrow=True, arrowhead=1, ax=0, ay=40)
        ]

    def create_top_annotations(df):
        if '好评频率' not in df.columns or '差评频率' not in df.columns:
            return []
        top_good = df.loc[df['好评频率'].idxmax()]
        top_bad = df.loc[df['差评频率'].idxmax()]
        return [
            dict(x=top_good['重要度'], y=top_good['满意度'],
                 text=f"👍 Top好评点: {top_good['体验点']}", showarrow=True, arrowhead=2, ax=-50, ay=-50,
                 font=dict(color="green", size=12), arrowcolor="green"),
            dict(x=top_bad['重要度'], y=top_bad['满意度'],
                 text=f"👎 Top差评点: {top_bad['体验点']}", showarrow=True, arrowhead=2, ax=50, ay=50,
                 font=dict(color="red", size=12), arrowcolor="red")
        ]

    # ✅ 构建数据列表
    period_labels = {
        '近半年数据分析': '近半年',
        '近一年数据分析': '近一年',
        '近两年数据分析': '近两年'
    }

    traces_all = []
    lens = []
    dfs_ordered = []
    avgs_ordered = []

    for sheet, label in period_labels.items():
        if sheet in dfs:
            df = dfs[sheet]
            traces, avg = create_traces(df, label)
            traces_all.extend(traces)
            lens.append(len(traces))
            dfs_ordered.append((df, label))  # ✅ 存储成 (df, label)
            avgs_ordered.append(avg)

    if not traces_all:
        st.error("❌ 没有任何可绘制的数据。")
        st.stop()

    # ✅ 绘制气泡图
    fig = go.Figure(data=traces_all)
    for i in range(lens[0]):
        fig.data[i].visible = True

    buttons = []
    start_idx = 0
    for i, (df, label) in enumerate(dfs_ordered):
        vis = [False] * len(traces_all)
        for j in range(lens[i]):
            vis[start_idx + j] = True
        buttons.append(dict(
            label=label,
            method='update',
            args=[
                {'visible': vis},
                {
                    'shapes': create_reference_shapes(avgs_ordered[i], df),
                    'annotations': create_annotations(avgs_ordered[i], df) + create_top_annotations(df)
                }
            ]
        ))
        start_idx += lens[i]

    fig.add_annotation(
        text="📘 图例说明：\n颜色表示满意度（-5 至 5）\n气泡大小表示分歧度（越大越分歧）",
        xref="paper", yref="paper",
        x=1.02, y=0.4,
        showarrow=False,
        align="left",
        font=dict(size=11),
        bordercolor="gray",
        borderwidth=1,
        bgcolor="white",
        opacity=0.9
    )

    fig.update_layout(
        updatemenus=[dict(
            buttons=buttons,
            active=0,
            x=0.98, y=1.12,
            xanchor='right',
            yanchor='top',
            direction='down',
            showactive=True
        )],
        title='🔥 体验点气泡图（时间范围切换）',
        xaxis_title='重要度',
        yaxis_title='满意度',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        plot_bgcolor='white',
        height=800,
        width=1200,
        margin=dict(l=100, r=250, t=100, b=60),
        coloraxis=dict(
            colorscale='balance_r',
            colorbar=dict(
                title="满意度",
                tickvals=[0, 0.5, 1],
                ticktext=['-5', '0', '5'],
                len=0.7,
                thickness=15,
                outlinewidth=0,
                y=0.5,
                yanchor='middle',
                x=1.35,
                xanchor='left'
            ),
            cmin=0, cmax=1,
        ),
        legend=dict(
            title='体验点',
            traceorder='normal',
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='lightgray',
            borderwidth=1,
            x=1.02, y=0.99,
            xanchor='left',
            yanchor='top',
            font=dict(size=11),
            itemsizing='constant',
            valign='top',
            orientation='v'
        ),
        shapes=create_reference_shapes(avgs_ordered[0], dfs_ordered[0][0]),
        annotations=create_annotations(avgs_ordered[0], dfs_ordered[0][0]) + create_top_annotations(dfs_ordered[0][0])
    )

    st.plotly_chart(fig, use_container_width=True)

    # ✅ Top痛点条形图展示
    st.subheader("🔥 Top10 痛点条形图展示")

    def show_top_pain_bar(df, period_name):
        col_name = 'Top痛点'
        if col_name in df.columns:
            df_sorted = df.sort_values(by=col_name, ascending=False).head(10)
            fig = px.bar(
                df_sorted,
                x=col_name,
                y='体验点',
                orientation='h',
                color=col_name,
                color_continuous_scale='Reds',
                title=f"{period_name} Top10 痛点",
                height=400
            )
            fig.update_layout(
                xaxis_title='痛点评分',
                yaxis_title='体验点',
                coloraxis_showscale=False,
                margin=dict(l=80, r=20, t=40, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"{period_name} 数据中未找到字段 '{col_name}'，请检查列名")

    cols = st.columns(len(dfs_ordered))
    for col, (df, label) in zip(cols, dfs_ordered):
        with col:
            show_top_pain_bar(df, label)
